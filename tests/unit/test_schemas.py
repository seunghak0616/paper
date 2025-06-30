"""
Unit tests for Pydantic schemas.
"""


import pytest
from pydantic import ValidationError

from app.schemas import PaperResponse, SearchResult


class TestPaperResponse:
    """Test PaperResponse schema."""

    def test_paper_response_valid_data(self):
        """Test PaperResponse with valid data."""
        data = {
            "id": 1,
            "title": "Test Paper",
            "author": "Test Author",
            "publisher": "Test Publisher",
            "publication_date": "2024-01-01",
            "url": "https://example.com/paper",
            "pdf_path": "/path/to/paper.pdf",
            "abstract": "Test abstract"
        }

        response = PaperResponse(**data)

        assert response.id == 1
        assert response.title == "Test Paper"
        assert response.author == "Test Author"
        assert response.publication_date == "2024-01-01"

    def test_paper_response_minimal_data(self):
        """Test PaperResponse with minimal required data."""
        data = {
            "id": 1,
            "title": "Test Paper",
            "author": "Test Author",
            "publisher": "Test Publisher"
        }

        response = PaperResponse(**data)

        assert response.id == 1
        assert response.title == "Test Paper"
        assert response.publication_date is None
        assert response.url is None
        assert response.pdf_path is None
        assert response.abstract is None

    def test_paper_response_missing_required_fields(self):
        """Test PaperResponse with missing required fields."""
        # Missing title
        data = {
            "id": 1,
            "author": "Test Author",
            "publisher": "Test Publisher"
        }

        with pytest.raises(ValidationError) as exc_info:
            PaperResponse(**data)

        assert "title" in str(exc_info.value)

    def test_paper_response_invalid_types(self):
        """Test PaperResponse with invalid field types."""
        # Invalid ID type
        data = {
            "id": "not_an_integer",
            "title": "Test Paper",
            "author": "Test Author",
            "publisher": "Test Publisher"
        }

        with pytest.raises(ValidationError) as exc_info:
            PaperResponse(**data)

        assert "id" in str(exc_info.value)

    def test_paper_response_serialization(self):
        """Test PaperResponse serialization."""
        data = {
            "id": 1,
            "title": "Test Paper",
            "author": "Test Author",
            "publisher": "Test Publisher",
            "publication_date": "2024-01-01",
            "url": "https://example.com/paper"
        }

        response = PaperResponse(**data)
        serialized = response.model_dump()

        assert serialized["id"] == 1
        assert serialized["title"] == "Test Paper"
        assert serialized["publication_date"] == "2024-01-01"

    def test_paper_response_json_serialization(self):
        """Test PaperResponse JSON serialization."""
        data = {
            "id": 1,
            "title": "Test Paper",
            "author": "Test Author",
            "publisher": "Test Publisher"
        }

        response = PaperResponse(**data)
        json_str = response.model_dump_json()

        assert '"id":1' in json_str
        assert '"title":"Test Paper"' in json_str

    def test_paper_response_from_orm(self):
        """Test PaperResponse creation from ORM model."""
        # Mock ORM object
        class MockPaper:
            id = 1
            title = "Test Paper"
            author = "Test Author"
            publisher = "Test Publisher"
            publication_date = "2024-01-01"
            url = "https://example.com/paper"
            pdf_path = "/path/to/paper.pdf"
            abstract = "Test abstract"

        mock_paper = MockPaper()
        response = PaperResponse.model_validate(mock_paper)

        assert response.id == 1
        assert response.title == "Test Paper"


class TestSearchResult:
    """Test SearchResult schema."""

    def test_search_result_valid_data(self):
        """Test SearchResult with valid data."""
        data = {
            "paper_title": "Test Paper",
            "chunk_text": "This is a test chunk of text.",
            "page_number": 1,
            "pdf_path": "/path/to/paper.pdf"
        }

        result = SearchResult(**data)

        assert result.paper_title == "Test Paper"
        assert result.chunk_text == "This is a test chunk of text."
        assert result.page_number == 1
        assert result.pdf_path == "/path/to/paper.pdf"

    def test_search_result_minimal_data(self):
        """Test SearchResult with minimal data."""
        data = {
            "paper_title": "Test Paper",
            "chunk_text": "Test chunk."
        }

        result = SearchResult(**data)

        assert result.paper_title == "Test Paper"
        assert result.chunk_text == "Test chunk."
        assert result.page_number is None
        assert result.pdf_path is None

    def test_search_result_missing_required_fields(self):
        """Test SearchResult with missing required fields."""
        # Missing paper_title
        data = {
            "chunk_text": "Test chunk.",
            "page_number": 1
        }

        with pytest.raises(ValidationError) as exc_info:
            SearchResult(**data)

        assert "paper_title" in str(exc_info.value)

        # Missing chunk_text
        data = {
            "paper_title": "Test Paper",
            "page_number": 1
        }

        with pytest.raises(ValidationError) as exc_info:
            SearchResult(**data)

        assert "chunk_text" in str(exc_info.value)

    def test_search_result_invalid_page_number(self):
        """Test SearchResult with invalid page number."""
        # Negative page number
        data = {
            "paper_title": "Test Paper",
            "chunk_text": "Test chunk.",
            "page_number": -1
        }

        with pytest.raises(ValidationError) as exc_info:
            SearchResult(**data)

        assert "page_number" in str(exc_info.value)

        # Zero page number
        data = {
            "paper_title": "Test Paper",
            "chunk_text": "Test chunk.",
            "page_number": 0
        }

        with pytest.raises(ValidationError) as exc_info:
            SearchResult(**data)

        assert "page_number" in str(exc_info.value)

    def test_search_result_empty_strings(self):
        """Test SearchResult with empty strings."""
        # Empty paper title
        data = {
            "paper_title": "",
            "chunk_text": "Test chunk."
        }

        with pytest.raises(ValidationError) as exc_info:
            SearchResult(**data)

        assert "paper_title" in str(exc_info.value)

        # Empty chunk text
        data = {
            "paper_title": "Test Paper",
            "chunk_text": ""
        }

        with pytest.raises(ValidationError) as exc_info:
            SearchResult(**data)

        assert "chunk_text" in str(exc_info.value)

    def test_search_result_serialization(self):
        """Test SearchResult serialization."""
        data = {
            "paper_title": "Test Paper",
            "chunk_text": "This is a test chunk.",
            "page_number": 1,
            "pdf_path": "/path/to/paper.pdf"
        }

        result = SearchResult(**data)
        serialized = result.model_dump()

        assert serialized["paper_title"] == "Test Paper"
        assert serialized["chunk_text"] == "This is a test chunk."
        assert serialized["page_number"] == 1
        assert serialized["pdf_path"] == "/path/to/paper.pdf"

    def test_search_result_json_serialization(self):
        """Test SearchResult JSON serialization."""
        data = {
            "paper_title": "Test Paper",
            "chunk_text": "Test chunk.",
            "page_number": 1
        }

        result = SearchResult(**data)
        json_str = result.model_dump_json()

        assert '"paper_title":"Test Paper"' in json_str
        assert '"chunk_text":"Test chunk."' in json_str
        assert '"page_number":1' in json_str

    def test_search_result_long_text(self):
        """Test SearchResult with very long text."""
        long_text = "A" * 10000  # Very long chunk text

        data = {
            "paper_title": "Test Paper",
            "chunk_text": long_text,
            "page_number": 1
        }

        result = SearchResult(**data)
        assert len(result.chunk_text) == 10000

    def test_search_result_unicode_text(self):
        """Test SearchResult with Unicode text."""
        data = {
            "paper_title": "한글 논문 제목",
            "chunk_text": "이것은 한글로 된 텍스트 청크입니다. 🤖",
            "page_number": 1
        }

        result = SearchResult(**data)
        assert result.paper_title == "한글 논문 제목"
        assert "한글로 된" in result.chunk_text
        assert "🤖" in result.chunk_text
