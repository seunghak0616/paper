"""
Paper chunk repository implementation.
"""


from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.exceptions import DatabaseError
from app.models import Paper, PaperChunk
from app.repositories.base import BaseRepository


class ChunkRepository(BaseRepository[PaperChunk]):
    """Repository for PaperChunk entities."""

    def __init__(self, db: Session):
        super().__init__(db, PaperChunk)

    def get_by_paper_id(self, paper_id: int) -> list[PaperChunk]:
        """Get all chunks for a specific paper."""
        try:
            return (
                self.db.query(PaperChunk)
                .filter(PaperChunk.paper_id == paper_id)
                .order_by(PaperChunk.page_number, PaperChunk.id)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching chunks by paper ID: {str(e)}")

    def get_by_page(self, paper_id: int, page_number: int) -> list[PaperChunk]:
        """Get chunks for a specific page of a paper."""
        try:
            return (
                self.db.query(PaperChunk)
                .filter(
                    PaperChunk.paper_id == paper_id,
                    PaperChunk.page_number == page_number
                )
                .order_by(PaperChunk.id)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching chunks by page: {str(e)}")

    def search_similar_by_embedding(
        self,
        query_embedding: list[float],
        limit: int = 5,
        similarity_threshold: float | None = None
    ) -> list[PaperChunk]:
        """
        Search for similar chunks using cosine similarity.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            similarity_threshold: Optional minimum similarity score
        """
        try:
            query = (
                self.db.query(PaperChunk)
                .options(joinedload(PaperChunk.paper))  # Eager load paper data
                .order_by(PaperChunk.embedding.cosine_distance(query_embedding))
                .limit(limit)
            )

            # Note: PostgreSQL pgvector doesn't support direct similarity filtering
            # in the query, so we'll apply threshold filtering in the service layer
            # if needed

            return query.all()

        except SQLAlchemyError as e:
            raise DatabaseError(f"Error searching similar chunks: {str(e)}")

    def get_chunks_with_papers(
        self,
        chunk_ids: list[int]
    ) -> list[PaperChunk]:
        """
        Get chunks with their associated papers in a single query.
        Optimized to avoid N+1 query problem.
        """
        try:
            return (
                self.db.query(PaperChunk)
                .options(joinedload(PaperChunk.paper))
                .filter(PaperChunk.id.in_(chunk_ids))
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching chunks with papers: {str(e)}")

    def count_by_paper(self, paper_id: int) -> int:
        """Count chunks for a specific paper."""
        try:
            return (
                self.db.query(PaperChunk)
                .filter(PaperChunk.paper_id == paper_id)
                .count()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error counting chunks by paper: {str(e)}")

    def get_max_page_number(self, paper_id: int) -> int | None:
        """Get the maximum page number for a paper."""
        try:
            result = (
                self.db.query(PaperChunk.page_number)
                .filter(PaperChunk.paper_id == paper_id)
                .order_by(PaperChunk.page_number.desc())
                .first()
            )
            return result[0] if result else None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error getting max page number: {str(e)}")

    def delete_by_paper_id(self, paper_id: int) -> int:
        """Delete all chunks for a specific paper. Returns count of deleted chunks."""
        try:
            count = (
                self.db.query(PaperChunk)
                .filter(PaperChunk.paper_id == paper_id)
                .count()
            )

            self.db.query(PaperChunk).filter(
                PaperChunk.paper_id == paper_id
            ).delete()

            self.db.commit()
            return count

        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error deleting chunks by paper ID: {str(e)}")

    def search_by_text(
        self,
        query: str,
        limit: int = 10
    ) -> list[PaperChunk]:
        """Search chunks by text content (full-text search)."""
        try:
            return (
                self.db.query(PaperChunk)
                .options(joinedload(PaperChunk.paper))
                .filter(PaperChunk.chunk_text.ilike(f"%{query}%"))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error searching chunks by text: {str(e)}")

    def get_papers_for_chunks(self, chunk_ids: list[int]) -> list[Paper]:
        """
        Get unique papers for given chunk IDs.
        Optimized for bulk operations.
        """
        try:
            paper_ids = (
                self.db.query(PaperChunk.paper_id)
                .filter(PaperChunk.id.in_(chunk_ids))
                .distinct()
                .all()
            )

            paper_id_list = [pid[0] for pid in paper_ids]

            return (
                self.db.query(Paper)
                .filter(Paper.id.in_(paper_id_list))
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Error fetching papers for chunks: {str(e)}")

    def bulk_create(self, chunks_data: list[dict]) -> list[PaperChunk]:
        """Bulk create chunks for better performance."""
        try:
            chunks = [PaperChunk(**chunk_data) for chunk_data in chunks_data]
            self.db.add_all(chunks)
            self.db.commit()

            # Refresh all instances
            for chunk in chunks:
                self.db.refresh(chunk)

            return chunks
        except SQLAlchemyError as e:
            self.db.rollback()
            raise DatabaseError(f"Error bulk creating chunks: {str(e)}")
