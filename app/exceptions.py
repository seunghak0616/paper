"""
Custom exception classes for the application.
Provides user-friendly error messages and proper HTTP status codes.
"""

from typing import Any

from fastapi import HTTPException, status


class PapersAPIException(HTTPException):
    """Base exception class for Papers API."""

    def __init__(
        self,
        status_code: int,
        user_message: str,
        detail: str | None = None,
        headers: dict[str, Any] | None = None
    ):
        """
        Args:
            status_code: HTTP status code
            user_message: User-friendly message
            detail: Technical details (for logging)
            headers: Optional HTTP headers
        """
        self.user_message = user_message
        self.technical_detail = detail

        # Use user message as the main detail
        super().__init__(
            status_code=status_code,
            detail=user_message,
            headers=headers
        )


class DatabaseError(PapersAPIException):
    """Database-related errors."""

    def __init__(self, detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            user_message="데이터베이스 연결에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
            detail=detail
        )


class SearchError(PapersAPIException):
    """Search-related errors."""

    def __init__(self, detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            user_message="검색 중 오류가 발생했습니다. 다른 검색어로 시도해보세요.",
            detail=detail
        )


class EmbeddingError(PapersAPIException):
    """Embedding generation errors."""

    def __init__(self, detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            user_message="텍스트 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            detail=detail
        )


class FileNotFoundError(PapersAPIException):
    """File not found errors."""

    def __init__(self, filename: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            user_message=f"요청하신 파일을 찾을 수 없습니다: {filename}",
            detail=f"File not found: {filename}"
        )


class ValidationError(PapersAPIException):
    """Input validation errors."""

    def __init__(self, field: str, message: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            user_message=f"입력값 오류: {field} - {message}",
            detail=f"Validation error for {field}: {message}"
        )


class RateLimitError(PapersAPIException):
    """Rate limiting errors."""

    def __init__(self, detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            user_message="요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
            detail=detail
        )


class AuthenticationError(PapersAPIException):
    """Authentication errors."""

    def __init__(self, detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            user_message="인증이 필요합니다.",
            detail=detail
        )


class ConfigurationError(PapersAPIException):
    """Configuration errors."""

    def __init__(self, detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            user_message="서버 설정에 문제가 있습니다. 관리자에게 문의하세요.",
            detail=detail
        )


# Exception handlers
def create_exception_handler(logger):
    """Create exception handler with proper logging."""

    async def exception_handler(request, exc: PapersAPIException):
        """Handle custom exceptions with logging."""

        # Log technical details
        if hasattr(exc, 'technical_detail') and exc.technical_detail:
            logger.error(f"API Error: {exc.technical_detail}")

        # Log request info
        logger.error(f"Request: {request.method} {request.url}")

        # Return user-friendly message
        return {
            "error": exc.user_message,
            "status_code": exc.status_code
        }

    return exception_handler


# Utility functions for common error patterns
def handle_database_error(func):
    """Decorator to handle database errors."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "connection" in str(e).lower():
                raise DatabaseError(detail=str(e))
            raise
    return wrapper


def validate_search_query(query: str) -> str:
    """Validate and sanitize search query."""
    if not query or not query.strip():
        raise ValidationError("query", "검색어를 입력해주세요.")

    query = query.strip()

    if len(query) < 2:
        raise ValidationError("query", "검색어는 2자 이상 입력해주세요.")

    if len(query) > 100:
        raise ValidationError("query", "검색어는 100자 이하로 입력해주세요.")

    # Basic SQL injection prevention (additional to ORM protection)
    dangerous_patterns = ["'", '"', ';', '--', '/*', '*/']
    if any(pattern in query for pattern in dangerous_patterns):
        raise ValidationError("query", "허용되지 않는 문자가 포함되어 있습니다.")

    return query
