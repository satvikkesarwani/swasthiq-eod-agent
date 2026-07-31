import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.api.routes_clinic_days import router as clinic_days_router
from app.api.routes_health import router as health_router
from app.api.routes_narratives import router as narratives_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import FixedWindowRateLimiter
from app.core.request_context import reset_request_id, set_request_id
from app.core.safe_strings import safe_error_code, safe_error_message, safe_field_path
from app.db.session import Base, build_engine, build_session_factory
from app.integrations.llm_provider import ChatNVIDIANarrativeProvider, DisabledNarrativeProvider
from app.schemas.ingestion import BillingLogRequest

logger = get_logger(__name__)


def _error_response(*, request: Request, code: str, message: str, status_code: int) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID") or f"req_{uuid4().hex}"
    return JSONResponse(
        status_code=status_code,
        headers={"X-Request-ID": request_id},
        content={
            "error": {
                "code": code,
                "message": message,
                "details": [],
                "request_id": request_id,
            }
        },
    )


def _build_provider(settings: Settings):
    if settings.llm_enabled and settings.llm_provider == "nvidia":
        return ChatNVIDIANarrativeProvider(
            api_keys=settings.nvidia_api_key_pool,
            model=settings.nvidia_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout_seconds=settings.llm_timeout_seconds,
            transport_retries=settings.llm_transport_retries,
            base_url=settings.nvidia_base_url,
        )
    return DisabledNarrativeProvider()


def create_app(*, settings: Settings | None = None, narrative_provider=None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(level=settings.log_level, log_format=settings.log_format)
    engine = build_engine(settings.database_url)
    if settings.app_env == "test":
        Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        engine.dispose()

    app = FastAPI(
        lifespan=lifespan,
        title=settings.app_name,
        version=settings.app_version,
        description="Deterministic clinic-day billing reconciliation, analytics, and grounded narrative API.",
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.narrative_provider = narrative_provider or _build_provider(settings)
    app.state.narrative_rate_limiter = FixedWindowRateLimiter(
        limit=settings.narrative_rate_limit_per_minute,
        window_seconds=60,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )

    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        if settings.app_env == "production":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    @app.middleware("http")
    async def request_body_limit_middleware(request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            limit = settings.max_request_body_bytes
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    if int(content_length) > limit:
                        logger.warning(
                            "request.body_too_large content_length=%s limit=%s path=%s",
                            content_length,
                            limit,
                            request.url.path,
                        )
                        return _error_response(
                            request=request,
                            code="REQUEST_TOO_LARGE",
                            message=f"Request body must be no larger than {limit} bytes.",
                            status_code=413,
                        )
                except ValueError:
                    pass

            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > limit:
                    logger.warning(
                        "request.body_stream_too_large bytes=%s limit=%s path=%s",
                        len(body),
                        limit,
                        request.url.path,
                    )
                    return _error_response(
                        request=request,
                        code="REQUEST_TOO_LARGE",
                        message=f"Request body must be no larger than {limit} bytes.",
                        status_code=413,
                    )

            payload = bytes(body)
            request._body = payload
            sent = False

            async def receive():
                nonlocal sent
                if sent:
                    return {"type": "http.request", "body": b"", "more_body": False}
                sent = True
                return {"type": "http.request", "body": payload, "more_body": False}

            request._receive = receive
        return await call_next(request)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid4().hex}"
        request.state.request_id = request_id
        request_token = set_request_id(request_id)
        started_at = time.perf_counter()
        logger.info(
            "request.start request_id=%s method=%s path=%s content_length=%s origin_present=%s",
            request_id,
            request.method,
            request.url.path,
            request.headers.get("content-length"),
            request.headers.get("origin") is not None,
        )
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request.exception request_id=%s method=%s path=%s elapsed_ms=%s",
                request_id,
                request.method,
                request.url.path,
                round((time.perf_counter() - started_at) * 1000),
            )
            reset_request_id(request_token)
            raise
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request.end request_id=%s method=%s path=%s status=%s elapsed_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            round((time.perf_counter() - started_at) * 1000),
        )
        reset_request_id(request_token)
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.warning(
            "app_error request_id=%s code=%s status=%s message=%s details_count=%s",
            getattr(request.state, "request_id", None),
            exc.code,
            exc.status_code,
            exc.message,
            len(exc.details),
        )
        headers = {"X-Request-ID": getattr(request.state, "request_id", None) or ""}
        retry_after = next(
            (
                item.get("retry_after_seconds")
                for item in exc.details
                if isinstance(item, dict) and isinstance(item.get("retry_after_seconds"), int)
            ),
            None,
        )
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)
        return JSONResponse(
            status_code=exc.status_code,
            headers=headers,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError):
        details = [
            {
                "field": safe_field_path(".".join(str(part) for part in error["loc"])),
                "code": safe_error_code(error["type"]),
                "message": safe_error_message(error["msg"]),
            }
            for error in exc.errors()
        ]
        logger.warning(
            "request.validation_error request_id=%s path=%s details_count=%s",
            getattr(request.state, "request_id", None),
            request.url.path,
            len(details),
        )
        return JSONResponse(
            status_code=422,
            headers={"X-Request-ID": getattr(request.state, "request_id", None) or ""},
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request does not match the API contract.",
                    "details": details,
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled API error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            headers={"X-Request-ID": getattr(request.state, "request_id", None) or ""},
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                    "details": [],
                    "request_id": getattr(request.state, "request_id", None),
                }
            },
        )

    api_prefix = "/api/v1"

    @app.get("/", include_in_schema=False)
    def root_status(request: Request) -> dict[str, str]:
        settings = request.app.state.settings
        return {
            "name": settings.app_name,
            "status": "online",
            "health": f"{api_prefix}/health",
            "api": api_prefix,
            "version": settings.app_version,
        }

    app.include_router(health_router, prefix=api_prefix)
    app.include_router(clinic_days_router, prefix=api_prefix)
    app.include_router(narratives_router, prefix=api_prefix)

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        openapi_schema.setdefault("components", {}).setdefault("schemas", {})["BillingLogRequest"] = BillingLogRequest.model_json_schema(ref_template="#/components/schemas/{model}")
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    return app


app = create_app()
