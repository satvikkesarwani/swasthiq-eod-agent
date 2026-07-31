import json
import logging
from datetime import date, datetime
from typing import Any

from pydantic import SecretStr

from app.core.request_context import get_request_id

SENSITIVE_KEYS = ("authorization", "api_key", "token", "secret", "password", "cookie", "raw_row", "prompt", "model_output")


def redact(value: Any) -> Any:
    if isinstance(value, SecretStr):
        return "********"
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, BaseException):
        return {"type": type(value).__name__}
    if isinstance(value, dict):
        return {
            key: "********" if any(pattern in key.lower() for pattern in SENSITIVE_KEYS) else redact(entry)
            for key, entry in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(entry) for entry in value[:20]]
    return value


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        request_id = getattr(record, "request_id", None)
        if request_id:
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exception"] = {"type": record.exc_info[0].__name__ if record.exc_info[0] else "Exception"}
        return json.dumps(redact(payload), ensure_ascii=False, sort_keys=True, default=str)


def configure_logging(*, level: str = "INFO", log_format: str = "text") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    logging.getLogger("app").setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
