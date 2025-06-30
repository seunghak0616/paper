"""
Unit tests for configuration module.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config import Settings, get_cors_origins, validate_environment


class TestSettings:
    """Test Settings class."""

    def test_default_settings(self):
        """Test default settings values."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
            settings = Settings()

            assert settings.host == "0.0.0.0"
            assert settings.port == 8000
            assert settings.embedding_model == "text-embedding-ada-002"
            assert settings.max_chunk_size == 500
            assert "http://localhost:3000" in settings.cors_allowed_origins

    def test_openai_key_validation(self):
        """Test OpenAI API key validation."""
        # Valid key
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-valid-key"}):
            settings = Settings()
            assert settings.openai_api_key == "sk-valid-key"

        # Invalid key format
        with patch.dict(os.environ, {"OPENAI_API_KEY": "invalid-key"}):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "must start with" in str(exc_info.value)

    def test_database_url_validation(self):
        """Test database URL validation."""
        # Valid PostgreSQL URL
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test-key",
            "DATABASE_URL": "postgresql://user:pass@localhost/db"
        }):
            settings = Settings()
            assert settings.database_url.startswith("postgresql://")

        # Invalid URL
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test-key",
            "DATABASE_URL": "mysql://invalid"
        }):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "PostgreSQL format" in str(exc_info.value)

    def test_cors_origins_parsing(self):
        """Test CORS origins parsing from string."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test-key",
            "CORS_ALLOWED_ORIGINS": "http://localhost:3000,https://example.com"
        }):
            settings = Settings()
            assert len(settings.cors_allowed_origins) == 2
            assert "http://localhost:3000" in settings.cors_allowed_origins
            assert "https://example.com" in settings.cors_allowed_origins


class TestCorsOrigins:
    """Test CORS origins configuration."""

    def test_development_cors_origins(self):
        """Test CORS origins in development environment."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            origins = get_cors_origins()
            assert "http://localhost:3000" in origins
            assert "http://127.0.0.1:3000" in origins

    def test_staging_cors_origins(self):
        """Test CORS origins in staging environment."""
        with patch.dict(os.environ, {"ENVIRONMENT": "staging"}):
            origins = get_cors_origins()
            assert "https://staging.yourdomain.com" in origins
            assert "http://localhost:3000" in origins

    def test_production_cors_origins(self):
        """Test CORS origins in production environment."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": "https://prod.example.com,https://app.example.com"
        }):
            origins = get_cors_origins()
            assert "https://prod.example.com" in origins
            assert "https://app.example.com" in origins

    def test_production_missing_cors_origins(self):
        """Test error when CORS_ORIGINS missing in production."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            with pytest.raises(ValueError) as exc_info:
                get_cors_origins()
            assert "CORS_ORIGINS must be set" in str(exc_info.value)


class TestEnvironmentValidation:
    """Test environment validation."""

    def test_valid_environment(self):
        """Test validation with valid environment."""
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "sk-test-key",
            "ENVIRONMENT": "development"
        }):
            # Should not raise any exception
            validate_environment()

    def test_missing_openai_key(self):
        """Test validation with missing OpenAI key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                validate_environment()
            assert "OPENAI_API_KEY is required" in str(exc_info.value)

    def test_production_wildcard_cors(self):
        """Test validation rejects wildcard CORS in production."""
        with patch('app.config.settings') as mock_settings:
            mock_settings.openai_api_key = "sk-test-key"
            mock_settings.cors_allowed_origins = ["*"]

            with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
                with pytest.raises(ValueError) as exc_info:
                    validate_environment()
                assert "Wildcard CORS origins not allowed" in str(exc_info.value)

    def test_production_missing_explicit_cors(self):
        """Test validation requires explicit CORS in production."""
        with patch('app.config.settings') as mock_settings:
            mock_settings.openai_api_key = "sk-test-key"
            mock_settings.cors_allowed_origins = ["http://localhost:3000"]

            with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
                with pytest.raises(ValueError) as exc_info:
                    validate_environment()
                assert "CORS_ORIGINS must be explicitly set" in str(exc_info.value)
