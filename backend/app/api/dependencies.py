from fastapi import Request
from sqlalchemy.orm import Session

from app.integrations.llm_provider import NarrativeProvider


def get_db(request: Request):
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        yield session


def get_narrative_provider(request: Request) -> NarrativeProvider:
    return request.app.state.narrative_provider
