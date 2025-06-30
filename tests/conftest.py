"""
Pytest configuration and shared fixtures.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.models import Base, Paper, PaperChunk
from app.server import app, get_db


@pytest.fixture(scope="session")
def test_settings():
    """Test settings with overrides."""
    return Settings(
        database_url="sqlite:///./test.db",
        openai_api_key="sk-test-key-for-testing-only",
        dbpia_api_key="test-dbpia-key",
        cors_allowed_origins=["http://localhost:3000"],
        rate_limit_default="1000/minute",  # Higher limit for tests
        data_dir="test_data",
        pdf_dir="test_data/pdfs",
        logs_dir="test_logs"
    )


@pytest.fixture(scope="session")
def test_engine(test_settings):
    """Create test database engine."""
    engine = create_engine(
        test_settings.database_url,
        connect_args={"check_same_thread": False}
    )

    # Create tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    session = TestingSessionLocal()

    yield session

    # Rollback any transactions
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session, test_settings):
    """Create test client with database override."""

    def override_get_db():
        yield test_db_session

    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db

    # Patch settings
    with patch('app.server.settings', test_settings):
        with TestClient(app) as client:
            yield client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sample_paper(test_db_session):
    """Create sample paper for testing."""
    paper = Paper(
        title="Test Paper on Machine Learning",
        author="Test Author",
        publisher="Test Publisher",
        publication_date="2024-01-01",
        url="https://example.com/paper1",
        pdf_path="test_data/pdfs/paper1.pdf",
        abstract="This is a test paper about machine learning algorithms."
    )

    test_db_session.add(paper)
    test_db_session.commit()
    test_db_session.refresh(paper)

    return paper


@pytest.fixture
def sample_paper_chunk(test_db_session, sample_paper):
    """Create sample paper chunk for testing."""
    # Mock embedding vector (1536 dimensions for OpenAI ada-002)
    mock_embedding = [0.1] * 1536

    chunk = PaperChunk(
        paper_id=sample_paper.id,
        chunk_text="This is a test chunk about neural networks and deep learning.",
        page_number=1,
        embedding=mock_embedding
    )

    test_db_session.add(chunk)
    test_db_session.commit()
    test_db_session.refresh(chunk)

    return chunk


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    return {
        "data": [
            {
                "embedding": [0.1] * 1536,
                "index": 0,
                "object": "embedding"
            }
        ],
        "model": "text-embedding-ada-002",
        "object": "list",
        "usage": {
            "prompt_tokens": 5,
            "total_tokens": 5
        }
    }


@pytest.fixture
def temp_pdf_file():
    """Create temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        # Write minimal PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
181
%%EOF"""
        tmp.write(pdf_content)
        tmp.flush()

        yield tmp.name

        # Cleanup
        os.unlink(tmp.name)


@pytest.fixture(autouse=True)
def clean_test_data():
    """Clean up test data before and after each test."""
    test_dirs = ["test_data", "test_logs"]

    # Cleanup before test
    for test_dir in test_dirs:
        if Path(test_dir).exists():
            import shutil
            shutil.rmtree(test_dir)

    yield

    # Cleanup after test
    for test_dir in test_dirs:
        if Path(test_dir).exists():
            import shutil
            shutil.rmtree(test_dir)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


# Test database initialization
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment."""
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["OPENAI_API_KEY"] = "sk-test-key-for-testing-only"

    yield

    # Cleanup environment
    os.environ.pop("ENVIRONMENT", None)
    os.environ.pop("OPENAI_API_KEY", None)
