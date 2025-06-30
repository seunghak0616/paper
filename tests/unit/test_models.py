"""
Unit tests for database models.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Paper, PaperChunk


class TestPaper:
    """Test Paper model."""

    def test_paper_creation(self, test_db_session):
        """Test creating a paper."""
        paper = Paper(
            title="Test Paper",
            author="Test Author",
            publisher="Test Publisher",
            publication_date="2024-01-01",
            url="https://example.com/paper",
            pdf_path="/path/to/paper.pdf",
            abstract="Test abstract"
        )

        test_db_session.add(paper)
        test_db_session.commit()

        assert paper.id is not None
        assert paper.title == "Test Paper"
        assert paper.author == "Test Author"

    def test_paper_required_fields(self, test_db_session):
        """Test paper creation with missing required fields."""
        # Missing title should raise error
        paper = Paper(
            author="Test Author",
            publisher="Test Publisher"
        )

        test_db_session.add(paper)

        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_paper_string_representation(self, test_db_session):
        """Test paper string representation."""
        paper = Paper(
            title="Test Paper",
            author="Test Author",
            publisher="Test Publisher"
        )

        test_db_session.add(paper)
        test_db_session.commit()

        assert str(paper) == "Test Paper"

    def test_paper_url_uniqueness(self, test_db_session):
        """Test that paper URLs must be unique."""
        # Create first paper
        paper1 = Paper(
            title="Paper 1",
            author="Author 1",
            publisher="Publisher",
            url="https://example.com/paper"
        )
        test_db_session.add(paper1)
        test_db_session.commit()

        # Try to create second paper with same URL
        paper2 = Paper(
            title="Paper 2",
            author="Author 2",
            publisher="Publisher",
            url="https://example.com/paper"  # Same URL
        )
        test_db_session.add(paper2)

        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_paper_optional_fields(self, test_db_session):
        """Test paper with optional fields."""
        paper = Paper(
            title="Test Paper",
            author="Test Author",
            publisher="Test Publisher"
            # Optional fields: publication_date, url, pdf_path, abstract
        )

        test_db_session.add(paper)
        test_db_session.commit()

        assert paper.id is not None
        assert paper.publication_date is None
        assert paper.url is None
        assert paper.pdf_path is None
        assert paper.abstract is None


class TestPaperChunk:
    """Test PaperChunk model."""

    def test_chunk_creation(self, test_db_session, sample_paper):
        """Test creating a paper chunk."""
        embedding = [0.1] * 1536  # Mock embedding

        chunk = PaperChunk(
            paper_id=sample_paper.id,
            chunk_text="This is a test chunk.",
            page_number=1,
            embedding=embedding
        )

        test_db_session.add(chunk)
        test_db_session.commit()

        assert chunk.id is not None
        assert chunk.paper_id == sample_paper.id
        assert chunk.chunk_text == "This is a test chunk."
        assert chunk.page_number == 1
        assert len(chunk.embedding) == 1536

    def test_chunk_paper_relationship(self, test_db_session, sample_paper):
        """Test chunk-paper relationship."""
        embedding = [0.2] * 1536

        chunk = PaperChunk(
            paper_id=sample_paper.id,
            chunk_text="Test chunk with relationship.",
            page_number=2,
            embedding=embedding
        )

        test_db_session.add(chunk)
        test_db_session.commit()

        # Test relationship
        assert chunk.paper == sample_paper
        assert chunk in sample_paper.chunks

    def test_chunk_required_fields(self, test_db_session, sample_paper):
        """Test chunk creation with missing required fields."""
        # Missing chunk_text
        chunk = PaperChunk(
            paper_id=sample_paper.id,
            page_number=1,
            embedding=[0.1] * 1536
        )

        test_db_session.add(chunk)

        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_chunk_embedding_dimension(self, test_db_session, sample_paper):
        """Test chunk with different embedding dimensions."""
        # Wrong dimension (should be 1536 for OpenAI ada-002)
        wrong_embedding = [0.1] * 512

        chunk = PaperChunk(
            paper_id=sample_paper.id,
            chunk_text="Test chunk.",
            page_number=1,
            embedding=wrong_embedding
        )

        test_db_session.add(chunk)
        test_db_session.commit()  # Should work, dimension not enforced at DB level

        assert len(chunk.embedding) == 512

    def test_chunk_foreign_key_constraint(self, test_db_session):
        """Test chunk with invalid paper_id."""
        chunk = PaperChunk(
            paper_id=99999,  # Non-existent paper
            chunk_text="Test chunk.",
            page_number=1,
            embedding=[0.1] * 1536
        )

        test_db_session.add(chunk)

        with pytest.raises(IntegrityError):
            test_db_session.commit()

    def test_chunk_string_representation(self, test_db_session, sample_paper):
        """Test chunk string representation."""
        chunk = PaperChunk(
            paper_id=sample_paper.id,
            chunk_text="This is a test chunk for string representation.",
            page_number=1,
            embedding=[0.1] * 1536
        )

        test_db_session.add(chunk)
        test_db_session.commit()

        str_repr = str(chunk)
        assert "This is a test chunk" in str_repr
        assert "page 1" in str_repr

    def test_multiple_chunks_per_paper(self, test_db_session, sample_paper):
        """Test multiple chunks for one paper."""
        chunks_data = [
            ("First chunk text", 1),
            ("Second chunk text", 1),
            ("Third chunk text", 2),
        ]

        chunks = []
        for text, page in chunks_data:
            chunk = PaperChunk(
                paper_id=sample_paper.id,
                chunk_text=text,
                page_number=page,
                embedding=[0.1] * 1536
            )
            chunks.append(chunk)
            test_db_session.add(chunk)

        test_db_session.commit()

        # Check all chunks are associated with the paper
        assert len(sample_paper.chunks) == 3

        # Check page numbers
        page_numbers = [chunk.page_number for chunk in sample_paper.chunks]
        assert 1 in page_numbers
        assert 2 in page_numbers

    def test_chunk_cascade_delete(self, test_db_session, sample_paper):
        """Test that chunks are deleted when paper is deleted."""
        # Create chunks
        chunk1 = PaperChunk(
            paper_id=sample_paper.id,
            chunk_text="Chunk 1",
            page_number=1,
            embedding=[0.1] * 1536
        )
        chunk2 = PaperChunk(
            paper_id=sample_paper.id,
            chunk_text="Chunk 2",
            page_number=2,
            embedding=[0.2] * 1536
        )

        test_db_session.add_all([chunk1, chunk2])
        test_db_session.commit()

        chunk_ids = [chunk1.id, chunk2.id]

        # Delete paper
        test_db_session.delete(sample_paper)
        test_db_session.commit()

        # Check chunks are also deleted (cascade)
        remaining_chunks = test_db_session.query(PaperChunk).filter(
            PaperChunk.id.in_(chunk_ids)
        ).all()

        assert len(remaining_chunks) == 0
