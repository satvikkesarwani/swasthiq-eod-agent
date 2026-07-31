from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request, session: Session = Depends(get_db)) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    settings = request.app.state.settings
    return {"status": "healthy", "database": "connected", "version": settings.app_version}
