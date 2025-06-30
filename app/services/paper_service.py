"""
Paper management service.
"""

from pathlib import Path

from sqlalchemy.orm import Session

from app.exceptions import DatabaseError, FileNotFoundError
from app.repositories import ChunkRepository, PaperRepository
from app.schemas import PaperResponse


class PaperService:
    """Service for paper management operations."""

    def __init__(self, db: Session):
        self.db = db
        self.paper_repo = PaperRepository(db)
        self.chunk_repo = ChunkRepository(db)

    def get_papers(
        self,
        skip: int = 0,
        limit: int = 10,
        search_query: str | None = None
    ) -> list[PaperResponse]:
        """
        Get papers with optional search.
        
        Args:
            skip: Number of papers to skip
            limit: Maximum number of papers to return
            search_query: Optional search query
            
        Returns:
            List of PaperResponse objects
        """
        try:
            if search_query:
                papers = self.paper_repo.search_by_text(
                    query=search_query,
                    skip=skip,
                    limit=limit
                )
            else:
                papers = self.paper_repo.get_all(skip=skip, limit=limit)

            return [PaperResponse.model_validate(paper) for paper in papers]

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(detail=str(e))

    def get_paper_by_id(self, paper_id: int) -> PaperResponse | None:
        """
        Get paper by ID.
        
        Args:
            paper_id: Paper ID
            
        Returns:
            PaperResponse object or None
        """
        try:
            paper = self.paper_repo.get_by_id(paper_id)
            return PaperResponse.model_validate(paper) if paper else None

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(detail=str(e))

    def get_paper_by_title(self, title: str) -> PaperResponse | None:
        """
        Get paper by exact title match.
        
        Args:
            title: Paper title
            
        Returns:
            PaperResponse object or None
        """
        try:
            paper = self.paper_repo.get_by_title(title)
            return PaperResponse.model_validate(paper) if paper else None

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(detail=str(e))

    def get_papers_by_author(
        self,
        author: str,
        skip: int = 0,
        limit: int = 10
    ) -> list[PaperResponse]:
        """
        Get papers by author.
        
        Args:
            author: Author name
            skip: Number of papers to skip
            limit: Maximum number of papers to return
            
        Returns:
            List of PaperResponse objects
        """
        try:
            papers = self.paper_repo.get_by_author(
                author=author,
                skip=skip,
                limit=limit
            )
            return [PaperResponse.model_validate(paper) for paper in papers]

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(detail=str(e))

    def get_papers_by_publisher(
        self,
        publisher: str,
        skip: int = 0,
        limit: int = 10
    ) -> list[PaperResponse]:
        """
        Get papers by publisher.
        
        Args:
            publisher: Publisher name
            skip: Number of papers to skip
            limit: Maximum number of papers to return
            
        Returns:
            List of PaperResponse objects
        """
        try:
            papers = self.paper_repo.get_by_publisher(
                publisher=publisher,
                skip=skip,
                limit=limit
            )
            return [PaperResponse.model_validate(paper) for paper in papers]

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(detail=str(e))

    def get_recent_papers(self, limit: int = 10) -> list[PaperResponse]:
        """
        Get recently added papers.
        
        Args:
            limit: Maximum number of papers to return
            
        Returns:
            List of PaperResponse objects
        """
        try:
            papers = self.paper_repo.get_recent(limit=limit)
            return [PaperResponse.model_validate(paper) for paper in papers]

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(detail=str(e))

    def get_papers_with_pdf(
        self,
        skip: int = 0,
        limit: int = 10
    ) -> list[PaperResponse]:
        """
        Get papers that have PDF files.
        
        Args:
            skip: Number of papers to skip
            limit: Maximum number of papers to return
            
        Returns:
            List of PaperResponse objects
        """
        try:
            papers = self.paper_repo.get_with_pdf(skip=skip, limit=limit)
            return [PaperResponse.model_validate(paper) for paper in papers]

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(detail=str(e))

    def create_paper(self, paper_data: dict) -> PaperResponse:
        """
        Create a new paper.
        
        Args:
            paper_data: Paper data dictionary
            
        Returns:
            PaperResponse object
        """
        try:
            paper = self.paper_repo.create(**paper_data)
            return PaperResponse.model_validate(paper)

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(detail=str(e))

    def update_paper(self, paper_id: int, paper_data: dict) -> PaperResponse | None:
        """
        Update a paper.
        
        Args:
            paper_id: Paper ID
            paper_data: Updated paper data
            
        Returns:
            Updated PaperResponse object or None
        """
        try:
            paper = self.paper_repo.update(paper_id, **paper_data)
            return PaperResponse.model_validate(paper) if paper else None

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(detail=str(e))

    def delete_paper(self, paper_id: int) -> bool:
        """
        Delete a paper and its associated chunks.
        
        Args:
            paper_id: Paper ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Delete associated chunks first
            self.chunk_repo.delete_by_paper_id(paper_id)

            # Delete the paper
            return self.paper_repo.delete(paper_id)

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(detail=str(e))

    def get_paper_pdf_path(self, title: str) -> Path:
        """
        Get PDF file path for a paper by title.
        
        Args:
            title: Paper title
            
        Returns:
            Path to PDF file
            
        Raises:
            FileNotFoundError: If paper or PDF file not found
        """
        try:
            paper = self.paper_repo.get_by_title(title)
            if not paper:
                raise FileNotFoundError(f"Paper with title '{title}' not found")

            if not paper.pdf_path:
                raise FileNotFoundError(f"No PDF file associated with paper '{title}'")

            pdf_path = Path(paper.pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            return pdf_path

        except FileNotFoundError:
            raise
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(detail=str(e))

    def get_paper_statistics(self) -> dict:
        """
        Get statistics about papers in the database.
        
        Returns:
            Dictionary with statistics
        """
        try:
            total_papers = self.paper_repo.count()
            papers_with_pdf = len(self.paper_repo.get_with_pdf(limit=10000))  # TODO: Optimize
            papers_without_pdf = total_papers - papers_with_pdf

            return {
                "total_papers": total_papers,
                "papers_with_pdf": papers_with_pdf,
                "papers_without_pdf": papers_without_pdf,
                "pdf_coverage_percentage": (papers_with_pdf / total_papers * 100) if total_papers > 0 else 0
            }

        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(detail=str(e))
