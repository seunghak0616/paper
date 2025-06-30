"""
Application configuration settings using Pydantic.
Provides type-safe environment variable handling and validation.
"""

import os

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Database
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/papers",
        description="PostgreSQL database connection URL"
    )

    # API Keys
    openai_api_key: str = Field(
        ...,  # Required
        description="OpenAI API key for embeddings"
    )
    dbpia_api_key: str | None = Field(
        default=None,
        description="DBpia API key for crawling"
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # CORS Settings
    cors_allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True)

    # Security
    rate_limit_default: str = Field(
        default="100/minute",
        description="Default rate limit"
    )

    # OpenAI Settings
    embedding_model: str = Field(
        default="text-embedding-ada-002",
        description="OpenAI embedding model"
    )
    max_chunk_size: int = Field(
        default=500,
        description="Maximum text chunk size for embeddings"
    )

    # File paths
    data_dir: str = Field(default="data", description="Data directory")
    pdf_dir: str = Field(default="data/pdfs", description="PDF storage directory")
    logs_dir: str = Field(default="logs", description="Logs directory")

    @validator('cors_allowed_origins', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Support comma-separated string
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator('openai_api_key')
    def validate_openai_key(cls, v):
        """Validate OpenAI API key format."""
        if not v or not v.startswith('sk-'):
            raise ValueError('OpenAI API key must start with "sk-"')
        return v

    @validator('database_url')
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError('Database URL must be PostgreSQL format')
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        # Environment variable prefixes
        env_prefix = ""


# Global settings instance
settings = Settings()

# Environment-specific configurations
def get_cors_origins() -> list[str]:
    """Get CORS origins based on environment."""
    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        # Production should have explicit domains
        prod_origins = os.getenv("CORS_ORIGINS", "").split(",")
        if not prod_origins or prod_origins == [""]:
            raise ValueError("CORS_ORIGINS must be set in production")
        return [origin.strip() for origin in prod_origins if origin.strip()]

    elif env == "staging":
        return [
            "https://staging.yourdomain.com",
            "http://localhost:3000"
        ]

    else:  # development
        return [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080"
        ]


def validate_environment():
    """Validate critical environment variables."""
    errors = []

    # Check required API keys
    if not settings.openai_api_key:
        errors.append("OPENAI_API_KEY is required")

    # Check database connection
    try:
        # Basic URL validation already done by pydantic
        pass
    except Exception as e:
        errors.append(f"Database configuration error: {e}")

    # Production-specific checks
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env == "production":
        if "*" in settings.cors_allowed_origins:
            errors.append("Wildcard CORS origins not allowed in production")

        if not os.getenv("CORS_ORIGINS"):
            errors.append("CORS_ORIGINS must be explicitly set in production")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"- {error}" for error in errors))


# Validate on import
try:
    validate_environment()
except ValueError as e:
    print(f"⚠️  Configuration Warning: {e}")
    # Don't fail on import in development, but log the warning
