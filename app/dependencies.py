"""
Dependency injection for FastAPI.
"""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.models import SessionLocal
from app.repositories import ChunkRepository, PaperRepository
from app.services import PaperService, SearchService


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_paper_repository(db: Session = Depends(get_db)) -> PaperRepository:
    """Get paper repository."""
    return PaperRepository(db)


def get_chunk_repository(db: Session = Depends(get_db)) -> ChunkRepository:
    """Get chunk repository."""
    return ChunkRepository(db)


def get_paper_service(db: Session = Depends(get_db)) -> PaperService:
    """Get paper service."""
    return PaperService(db)


def get_search_service(db: Session = Depends(get_db)) -> SearchService:
    """Get search service."""
    return SearchService(db)


# Cache frequently used objects
@lru_cache
def get_settings():
    """Get application settings (cached)."""
    from app.config import settings
    return settings
