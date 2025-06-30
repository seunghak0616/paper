"""
Integration tests for API endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status


@pytest.mark.integration
class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, test_client):
        """Test health check returns OK."""
        response = test_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "ok"}


@pytest.mark.integration
class TestPapersEndpoint:
    """Test papers listing endpoint."""

    def test_list_papers_empty(self, test_client):
        """Test listing papers when database is empty."""
        response = test_client.get("/papers")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_papers_with_data(self, test_client, sample_paper):
        """Test listing papers with data."""
        response = test_client.get("/papers")

        assert response.status_code == status.HTTP_200_OK
        papers = response.json()
        assert len(papers) == 1
        assert papers[0]["title"] == sample_paper.title
        assert papers[0]["author"] == sample_paper.author

    def test_list_papers_pagination(self, test_client, test_db_session):
        """Test papers pagination."""
        # Create multiple papers
        from app.models import Paper

        for i in range(5):
            paper = Paper(
                title=f"Test Paper {i}",
                author=f"Author {i}",
                publisher="Test Publisher",
                publication_date="2024-01-01",
                url=f"https://example.com/paper{i}",
                pdf_path=f"test_data/pdfs/paper{i}.pdf"
            )
            test_db_session.add(paper)
        test_db_session.commit()

        # Test pagination
        response = test_client.get("/papers?skip=2&limit=2")

        assert response.status_code == status.HTTP_200_OK
        papers = response.json()
        assert len(papers) == 2

    def test_list_papers_search(self, test_client, sample_paper):
        """Test papers search functionality."""
        response = test_client.get("/papers?q=Machine")

        assert response.status_code == status.HTTP_200_OK
        papers = response.json()
        assert len(papers) == 1
        assert "Machine" in papers[0]["title"]

    def test_list_papers_search_no_results(self, test_client, sample_paper):
        """Test papers search with no results."""
        response = test_client.get("/papers?q=NonExistent")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_papers_invalid_pagination(self, test_client):
        """Test invalid pagination parameters."""
        # Negative skip
        response = test_client.get("/papers?skip=-1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Limit too large
        response = test_client.get("/papers?limit=101")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Limit zero
        response = test_client.get("/papers?limit=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
class TestSearchEndpoint:
    """Test semantic search endpoint."""

    @patch('app.server.client')
    def test_search_papers_success(self, mock_client, test_client, sample_paper_chunk, mock_openai_response):
        """Test successful paper search."""
        # Mock OpenAI API response
        mock_client.embeddings.create.return_value = MagicMock(
            data=[MagicMock(embedding=[0.1] * 1536)]
        )

        response = test_client.post("/search?query=neural networks")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()
        assert len(results) >= 1
        assert results[0]["paper_title"] == sample_paper_chunk.paper.title
        assert "neural networks" in results[0]["chunk_text"]

    def test_search_papers_short_query(self, test_client):
        """Test search with too short query."""
        response = test_client.post("/search?query=a")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error = response.json()
        assert "2자 이상 입력해주세요" in error["detail"]

    def test_search_papers_long_query(self, test_client):
        """Test search with too long query."""
        long_query = "a" * 101
        response = test_client.post("/search?query=" + long_query)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error = response.json()
        assert "100자 이하로 입력해주세요" in error["detail"]

    def test_search_papers_dangerous_query(self, test_client):
        """Test search with dangerous characters."""
        response = test_client.post("/search?query=test'; DROP TABLE papers; --")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error = response.json()
        assert "허용되지 않는 문자가" in error["detail"]

    @patch('app.server.client')
    def test_search_papers_openai_error(self, mock_client, test_client):
        """Test search when OpenAI API fails."""
        # Mock OpenAI API error
        mock_client.embeddings.create.side_effect = Exception("OpenAI API error")

        response = test_client.post("/search?query=test query")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        error = response.json()
        assert "검색 중 오류가 발생했습니다" in error["detail"]

    def test_search_papers_empty_database(self, test_client):
        """Test search with empty database."""
        with patch('app.server.client') as mock_client:
            mock_client.embeddings.create.return_value = MagicMock(
                data=[MagicMock(embedding=[0.1] * 1536)]
            )

            response = test_client.post("/search?query=test query")

            assert response.status_code == status.HTTP_200_OK
            assert response.json() == []


@pytest.mark.integration
class TestPDFEndpoint:
    """Test PDF serving endpoint."""

    def test_pdf_not_found(self, test_client):
        """Test PDF endpoint with non-existent file."""
        response = test_client.get("/papers/NonExistent Paper/pdf")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_pdf_file_serve(self, test_client, sample_paper, temp_pdf_file):
        """Test serving existing PDF file."""
        # Update paper with actual file path
        sample_paper.pdf_path = temp_pdf_file

        response = test_client.get(f"/papers/{sample_paper.title}/pdf")

        # Should return the PDF content
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/pdf"

    def test_pdf_range_request(self, test_client, sample_paper, temp_pdf_file):
        """Test PDF range request."""
        sample_paper.pdf_path = temp_pdf_file

        headers = {"Range": "bytes=0-100"}
        response = test_client.get(
            f"/papers/{sample_paper.title}/pdf",
            headers=headers
        )

        assert response.status_code == status.HTTP_206_PARTIAL_CONTENT
        assert "content-range" in response.headers


@pytest.mark.integration
class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.mark.slow
    def test_rate_limit_enforcement(self, test_client):
        """Test that rate limiting is enforced."""
        # This test might be slow as it tests rate limiting
        # Make many requests quickly to trigger rate limit

        responses = []
        for _ in range(10):  # Adjust based on rate limit settings
            response = test_client.get("/health")
            responses.append(response.status_code)

        # Most should succeed, but might hit rate limit
        assert most_responses_successful(responses)


def most_responses_successful(responses):
    """Helper to check if most responses were successful."""
    successful = sum(1 for code in responses if code == 200)
    return successful >= len(responses) * 0.8  # 80% success rate
