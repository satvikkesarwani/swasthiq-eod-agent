from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.report import ErrorResponse, HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, responses={500: {"model": ErrorResponse}})
def health(request: Request, session: Session = Depends(get_db)) -> HealthResponse:
    session.execute(text("SELECT 1"))
    settings = request.app.state.settings
    return HealthResponse(status="healthy", database="connected", version=settings.app_version)
