"""
Paper repository implementation.
"""


from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.exceptions import DatabaseError
from app.models import Paper
from app.repositories.base import BaseRepository


class PaperRepository(BaseRepository[Paper]):
    """Repository for Paper entities."""

    def __init__(self, db: Session):
        super().__init__(db, Paper)

    def search_by_text(self, query: str, skip: int = 0, limit: int = 10) -> list[Paper]:
        """Search papers by title, author, or publisher."""
        try:
            q_lower = query.lower()
            return (
                self.db.query(Paper)
                .filter(
                    Paper.title.ilike(f"%{q_lower}%") |
                    Paper.author.ilike(f"%{q_lower}%") |
                    Paper.publisher.ilike(f"%{q_lower}%")
                )
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error searching papers: {str(e)}")

    def get_by_title(self, title: str) -> Paper | None:
        """Get paper by exact title match."""
        try:
            return self.db.query(Paper).filter(Paper.title == title).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching paper by title: {str(e)}")

    def get_by_url(self, url: str) -> Paper | None:
        """Get paper by URL."""
        try:
            return self.db.query(Paper).filter(Paper.url == url).first()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching paper by URL: {str(e)}")

    def get_by_author(self, author: str, skip: int = 0, limit: int = 10) -> list[Paper]:
        """Get papers by author."""
        try:
            return (
                self.db.query(Paper)
                .filter(Paper.author.ilike(f"%{author}%"))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching papers by author: {str(e)}")

    def get_by_publisher(self, publisher: str, skip: int = 0, limit: int = 10) -> list[Paper]:
        """Get papers by publisher."""
        try:
            return (
                self.db.query(Paper)
                .filter(Paper.publisher.ilike(f"%{publisher}%"))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching papers by publisher: {str(e)}")

    def get_with_pdf(self, skip: int = 0, limit: int = 10) -> list[Paper]:
        """Get papers that have PDF files."""
        try:
            return (
                self.db.query(Paper)
                .filter(Paper.pdf_path.isnot(None))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching papers with PDF: {str(e)}")

    def get_without_pdf(self, skip: int = 0, limit: int = 10) -> list[Paper]:
        """Get papers without PDF files."""
        try:
            return (
                self.db.query(Paper)
                .filter(Paper.pdf_path.is_(None))
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching papers without PDF: {str(e)}")

    def count_by_author(self, author: str) -> int:
        """Count papers by author."""
        try:
            return (
                self.db.query(Paper)
                .filter(Paper.author.ilike(f"%{author}%"))
                .count()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error counting papers by author: {str(e)}")

    def count_by_publisher(self, publisher: str) -> int:
        """Count papers by publisher."""
        try:
            return (
                self.db.query(Paper)
                .filter(Paper.publisher.ilike(f"%{publisher}%"))
                .count()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error counting papers by publisher: {str(e)}")

    def get_recent(self, limit: int = 10) -> list[Paper]:
        """Get recently added papers."""
        try:
            return (
                self.db.query(Paper)
                .order_by(Paper.id.desc())
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching recent papers: {str(e)}")
