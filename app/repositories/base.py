"""
Base repository pattern implementation.
"""

from abc import ABC
from typing import Generic, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.exceptions import DatabaseError

T = TypeVar('T')


class BaseRepository(Generic[T], ABC):
    """Base repository class with common CRUD operations."""

    def __init__(self, db: Session, model: type[T]):
        self.db = db
        self.model = model

    def get_by_id(self, id: int) -> T | None:
        """Get entity by ID."""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching {self.model.__name__} by ID: {str(e)}")

    def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """Get all entities with pagination."""
        try:
            return self.db.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching {self.model.__name__} list: {str(e)}")

    def create(self, **kwargs) -> T:
        """Create new entity."""
        try:
            instance = self.model(**kwargs)
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error creating {self.model.__name__}: {str(e)}")

    def update(self, id: int, **kwargs) -> T | None:
        """Update entity by ID."""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None

            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            self.db.commit()
            self.db.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error updating {self.model.__name__}: {str(e)}")

    def delete(self, id: int) -> bool:
        """Delete entity by ID."""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return False

            self.db.delete(instance)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error deleting {self.model.__name__}: {str(e)}")

    def count(self) -> int:
        """Count total entities."""
        try:
            return self.db.query(self.model).count()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error counting {self.model.__name__}: {str(e)}")

    def exists(self, id: int) -> bool:
        """Check if entity exists by ID."""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first() is not None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error checking {self.model.__name__} existence: {str(e)}")
