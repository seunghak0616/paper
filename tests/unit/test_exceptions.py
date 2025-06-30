"""
Unit tests for exception handling.
"""

import pytest
from fastapi import status

from app.exceptions import (
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    EmbeddingError,
    FileNotFoundError,
    PapersAPIException,
    RateLimitError,
    SearchError,
    ValidationError,
    validate_search_query,
)


class TestPapersAPIException:
    """Test base exception class."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = PapersAPIException(
            status_code=400,
            user_message="User friendly message",
            detail="Technical detail"
        )

        assert exc.status_code == 400
        assert exc.user_message == "User friendly message"
        assert exc.technical_detail == "Technical detail"
        assert exc.detail == "User friendly message"  # User message becomes detail

    def test_exception_without_detail(self):
        """Test exception without technical detail."""
        exc = PapersAPIException(
            status_code=500,
            user_message="Something went wrong"
        )

        assert exc.status_code == 500
        assert exc.user_message == "Something went wrong"
        assert exc.technical_detail is None


class TestSpecificExceptions:
    """Test specific exception classes."""

    def test_database_error(self):
        """Test DatabaseError."""
        exc = DatabaseError("Connection failed")

        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "데이터베이스 연결에 문제가" in exc.user_message
        assert exc.technical_detail == "Connection failed"

    def test_search_error(self):
        """Test SearchError."""
        exc = SearchError("Vector search failed")

        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "검색 중 오류가" in exc.user_message
        assert exc.technical_detail == "Vector search failed"

    def test_embedding_error(self):
        """Test EmbeddingError."""
        exc = EmbeddingError("OpenAI API error")

        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "텍스트 처리 중 오류가" in exc.user_message
        assert exc.technical_detail == "OpenAI API error"

    def test_file_not_found_error(self):
        """Test FileNotFoundError."""
        exc = FileNotFoundError("test.pdf")

        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert "test.pdf" in exc.user_message
        assert "File not found: test.pdf" in exc.technical_detail

    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError("query", "Too short")

        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "query" in exc.user_message
        assert "Too short" in exc.user_message
        assert "Validation error for query" in exc.technical_detail

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        exc = RateLimitError("Rate limit exceeded")

        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "요청이 너무 많습니다" in exc.user_message
        assert exc.technical_detail == "Rate limit exceeded"

    def test_authentication_error(self):
        """Test AuthenticationError."""
        exc = AuthenticationError("Invalid token")

        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert "인증이 필요합니다" in exc.user_message
        assert exc.technical_detail == "Invalid token"

    def test_configuration_error(self):
        """Test ConfigurationError."""
        exc = ConfigurationError("Missing API key")

        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "서버 설정에 문제가" in exc.user_message
        assert exc.technical_detail == "Missing API key"


class TestSearchQueryValidation:
    """Test search query validation."""

    def test_valid_query(self):
        """Test valid search query."""
        query = "머신러닝"
        result = validate_search_query(query)
        assert result == "머신러닝"

    def test_query_with_whitespace(self):
        """Test query with whitespace."""
        query = "  딥러닝  "
        result = validate_search_query(query)
        assert result == "딥러닝"

    def test_empty_query(self):
        """Test empty query."""
        with pytest.raises(ValidationError) as exc_info:
            validate_search_query("")
        assert "검색어를 입력해주세요" in str(exc_info.value)

    def test_whitespace_only_query(self):
        """Test whitespace-only query."""
        with pytest.raises(ValidationError) as exc_info:
            validate_search_query("   ")
        assert "검색어를 입력해주세요" in str(exc_info.value)

    def test_none_query(self):
        """Test None query."""
        with pytest.raises(ValidationError) as exc_info:
            validate_search_query(None)
        assert "검색어를 입력해주세요" in str(exc_info.value)

    def test_too_short_query(self):
        """Test query that's too short."""
        with pytest.raises(ValidationError) as exc_info:
            validate_search_query("a")
        assert "2자 이상 입력해주세요" in str(exc_info.value)

    def test_too_long_query(self):
        """Test query that's too long."""
        long_query = "a" * 101
        with pytest.raises(ValidationError) as exc_info:
            validate_search_query(long_query)
        assert "100자 이하로 입력해주세요" in str(exc_info.value)

    def test_query_with_sql_injection_attempt(self):
        """Test query with potential SQL injection."""
        dangerous_queries = [
            "test'; DROP TABLE papers; --",
            'test" OR 1=1 --',
            "test/* comment */",
            "test;",
            "test--comment"
        ]

        for dangerous_query in dangerous_queries:
            with pytest.raises(ValidationError) as exc_info:
                validate_search_query(dangerous_query)
            assert "허용되지 않는 문자가" in str(exc_info.value)

    def test_edge_case_valid_queries(self):
        """Test edge case valid queries."""
        valid_queries = [
            "AI",  # 2 characters
            "a" * 100,  # 100 characters (max)
            "한글 검색어",
            "English query",
            "Mixed 한글 English 123"
        ]

        for query in valid_queries:
            result = validate_search_query(query)
            assert result == query
