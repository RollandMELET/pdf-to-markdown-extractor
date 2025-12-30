"""
PDF-to-Markdown Extractor - Pytest Configuration and Fixtures.

Global fixtures and configuration for pytest tests.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient


# ==========================================
# Environment Setup
# ==========================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Setup test environment variables.

    This fixture runs once per test session and sets up necessary
    environment variables for testing.
    """
    # Set test environment
    os.environ["ENVIRONMENT"] = "development"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["LOG_FORMAT"] = "text"

    # Use in-memory or test Redis
    os.environ["REDIS_URL"] = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")

    # Disable external APIs in tests (unless explicitly enabled)
    if "MISTRAL_API_KEY" not in os.environ:
        os.environ["MISTRAL_API_KEY"] = "test-key-do-not-use"

    yield

    # Cleanup (if needed)


# ==========================================
# Temporary Directory Fixtures
# ==========================================

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for tests.

    Yields:
        Path: Path to temporary directory.

    Example:
        >>> def test_file_creation(temp_dir):
        ...     test_file = temp_dir / "test.txt"
        ...     test_file.write_text("test")
        ...     assert test_file.exists()
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def upload_dir(temp_dir: Path) -> Path:
    """
    Create a temporary upload directory.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        Path: Path to upload directory.
    """
    upload_path = temp_dir / "uploads"
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


@pytest.fixture
def output_dir(temp_dir: Path) -> Path:
    """
    Create a temporary output directory.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        Path: Path to output directory.
    """
    output_path = temp_dir / "outputs"
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


@pytest.fixture
def cache_dir(temp_dir: Path) -> Path:
    """
    Create a temporary cache directory.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        Path: Path to cache directory.
    """
    cache_path = temp_dir / "cache"
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path


# ==========================================
# Configuration Fixtures
# ==========================================

@pytest.fixture
def test_settings():
    """
    Get test configuration settings.

    Returns:
        Settings: Test settings instance.

    Example:
        >>> def test_config(test_settings):
        ...     assert test_settings.environment == "development"
    """
    from src.core.config import Settings

    # Create test settings with overrides
    settings = Settings(
        environment="development",
        log_level="DEBUG",
        redis_url="redis://localhost:6379/15",
        upload_dir=Path("/tmp/test-uploads"),
        output_dir=Path("/tmp/test-outputs"),
        cache_dir=Path("/tmp/test-cache"),
    )

    return settings


# ==========================================
# FastAPI Test Client Fixtures
# ==========================================

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create FastAPI test client.

    Yields:
        TestClient: FastAPI test client for API testing.

    Example:
        >>> def test_health_endpoint(client):
        ...     response = client.get("/health")
        ...     assert response.status_code == 200
    """
    from src.api.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def async_client():
    """
    Create async FastAPI test client.

    Yields:
        AsyncClient: Async FastAPI test client.

    Example:
        >>> @pytest.mark.asyncio
        ... async def test_async_endpoint(async_client):
        ...     response = await async_client.get("/health")
        ...     assert response.status_code == 200
    """
    from httpx import AsyncClient
    from src.api.main import app

    async def _client():
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    return _client


# ==========================================
# Redis Fixtures
# ==========================================

@pytest.fixture
def redis_client():
    """
    Create Redis client for testing.

    Yields:
        RedisClient: Test Redis client instance.

    Example:
        >>> def test_redis_set_get(redis_client):
        ...     redis_client.set("test", "value")
        ...     assert redis_client.get("test") == "value"
    """
    from src.utils.redis_client import RedisClient

    # Use test Redis database (15)
    client = RedisClient(redis_url="redis://localhost:6379/15")

    yield client

    # Cleanup: flush test database
    try:
        client.get_client().flushdb()
    except Exception:
        pass  # Redis might not be available in all test environments


# ==========================================
# PDF Fixture Helpers
# ==========================================

@pytest.fixture
def simple_pdf_path() -> Path:
    """
    Get path to simple PDF fixture.

    Returns:
        Path: Path to simple PDF file.
    """
    return Path("tests/fixtures/simple")


@pytest.fixture
def medium_pdf_path() -> Path:
    """
    Get path to medium complexity PDF fixture.

    Returns:
        Path: Path to medium PDF file.
    """
    return Path("tests/fixtures/medium")


@pytest.fixture
def complex_pdf_path() -> Path:
    """
    Get path to complex PDF fixture.

    Returns:
        Path: Path to complex PDF file.
    """
    return Path("tests/fixtures/complex")


@pytest.fixture
def edge_case_pdf_path() -> Path:
    """
    Get path to edge case PDF fixture.

    Returns:
        Path: Path to edge case PDF file.
    """
    return Path("tests/fixtures/edge_cases")


# ==========================================
# Mock Fixtures
# ==========================================

@pytest.fixture
def mock_mistral_api(monkeypatch):
    """
    Mock Mistral API for testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Example:
        >>> def test_with_mock_mistral(mock_mistral_api):
        ...     # Mistral API calls are mocked
        ...     pass
    """
    class MockMistralResponse:
        def __init__(self, content):
            self.content = content

    def mock_extract(*args, **kwargs):
        return MockMistralResponse("# Mocked extraction result\n\nTest content")

    # Mock the Mistral API client (implementation depends on actual extractor)
    # This is a placeholder - adjust based on actual implementation
    monkeypatch.setattr(
        "src.extractors.mistral_extractor.MistralClient.extract",
        mock_extract
    )


# ==========================================
# Logging Fixtures
# ==========================================

@pytest.fixture
def caplog_debug(caplog):
    """
    Capture logs at DEBUG level.

    Args:
        caplog: Pytest caplog fixture.

    Returns:
        caplog: Configured caplog fixture.

    Example:
        >>> def test_logging(caplog_debug):
        ...     logger.debug("Test message")
        ...     assert "Test message" in caplog_debug.text
    """
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog


# ==========================================
# Database/State Cleanup
# ==========================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    Cleanup after each test.

    This fixture runs automatically after each test to ensure
    clean state between tests.
    """
    yield

    # Add cleanup logic here if needed
    # For example: clear Redis cache, remove temp files, etc.


# ==========================================
# Celery Fixtures
# ==========================================

@pytest.fixture
def celery_worker():
    """
    Create Celery worker for testing.

    Yields:
        Worker: Celery worker instance for task testing.

    Note:
        This is a placeholder. Actual implementation depends on
        celery testing setup.
    """
    # Placeholder for Celery worker fixture
    # Will be implemented when Celery tasks are created
    yield None


# ==========================================
# Pytest Markers
# ==========================================

def pytest_configure(config):
    """
    Configure pytest with custom markers.

    This function is called during pytest initialization.
    """
    # Markers are already defined in pytest.ini
    pass


def pytest_collection_modifyitems(config, items):
    """
    Modify collected test items.

    This can be used to automatically add markers based on test location
    or naming conventions.

    Args:
        config: Pytest config object.
        items: List of collected test items.
    """
    for item in items:
        # Auto-mark tests based on file location
        if "test_api" in str(item.fspath):
            item.add_marker(pytest.mark.api)

        if "test_extractor" in str(item.fspath):
            item.add_marker(pytest.mark.extractor)

        if "test_celery" in str(item.fspath) or "test_task" in str(item.fspath):
            item.add_marker(pytest.mark.celery)

        # Mark integration tests based on naming
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark e2e tests
        if "e2e" in str(item.fspath) or "end_to_end" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
