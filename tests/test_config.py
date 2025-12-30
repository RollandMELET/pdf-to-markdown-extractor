"""
Tests for configuration management.

This test file verifies that the Settings class and configuration
management work correctly.
"""

import pytest
from pathlib import Path

from src.core.config import settings, get_settings, reload_settings, Settings


@pytest.mark.unit
@pytest.mark.config
class TestSettings:
    """Test suite for Settings class."""

    def test_settings_instance(self):
        """Test that settings is a valid Settings instance."""
        assert isinstance(settings, Settings)

    def test_get_settings_returns_singleton(self):
        """Test that get_settings() returns the singleton instance."""
        config = get_settings()
        assert config is settings

    def test_redis_url_is_set(self):
        """Test that redis_url is set."""
        assert settings.redis_url is not None
        assert "redis://" in settings.redis_url

    def test_default_values(self):
        """Test that default configuration values are set correctly."""
        assert settings.api_port == 8000
        assert settings.api_host == "0.0.0.0"
        assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert settings.log_format in ["json", "text"]
        assert settings.max_file_size_mb > 0
        assert settings.max_pages > 0

    def test_computed_property_max_file_size_bytes(self):
        """Test max_file_size_bytes computed property."""
        expected_bytes = settings.max_file_size_mb * 1024 * 1024
        assert settings.max_file_size_bytes == expected_bytes

    def test_computed_property_is_production(self):
        """Test is_production computed property."""
        # In test environment, should be False or based on environment
        if settings.environment == "production":
            assert settings.is_production is True
        else:
            assert settings.is_production is False

    def test_computed_property_is_development(self):
        """Test is_development computed property."""
        if settings.environment == "development":
            assert settings.is_development is True
        else:
            assert settings.is_development is False

    def test_get_summary(self):
        """Test get_summary() method."""
        summary = settings.get_summary()

        # Check required keys
        assert "app_name" in summary
        assert "app_version" in summary
        assert "environment" in summary
        assert "api_port" in summary
        assert "log_level" in summary
        assert "redis_url" in summary

        # Check that summary values match settings
        assert summary["app_name"] == settings.app_name
        assert summary["app_version"] == settings.app_version
        assert summary["environment"] == settings.environment
        assert summary["api_port"] == settings.api_port

    def test_mask_url_with_credentials(self):
        """Test _mask_url() method with credentials."""
        url_with_creds = "redis://user:password@localhost:6379/0"
        masked = Settings._mask_url(url_with_creds)
        assert "***:***@" in masked
        assert "password" not in masked
        assert "user" not in masked
        assert "localhost:6379/0" in masked

    def test_mask_url_without_credentials(self):
        """Test _mask_url() method without credentials."""
        url_no_creds = "redis://localhost:6379/0"
        masked = Settings._mask_url(url_no_creds)
        assert masked == url_no_creds  # Should remain unchanged

    def test_celery_broker_url_defaults_to_redis_url(self):
        """Test that celery_broker_url defaults to redis_url."""
        # When creating a new Settings instance without celery_broker_url,
        # it should default to redis_url (unless env vars override)
        # This test verifies the validator logic exists
        import os
        # Save original env vars
        orig_broker = os.environ.get("CELERY_BROKER_URL")
        orig_redis = os.environ.get("REDIS_URL")

        try:
            # Clear celery env vars to test default behavior
            os.environ.pop("CELERY_BROKER_URL", None)
            os.environ["REDIS_URL"] = "redis://testhost:6379/5"

            test_config = Settings()
            assert test_config.celery_broker_url == "redis://testhost:6379/5"
        finally:
            # Restore env vars
            if orig_broker:
                os.environ["CELERY_BROKER_URL"] = orig_broker
            if orig_redis:
                os.environ["REDIS_URL"] = orig_redis

    def test_celery_result_backend_defaults_to_redis_url(self):
        """Test that celery_result_backend defaults to redis_url."""
        import os
        # Save original env vars
        orig_backend = os.environ.get("CELERY_RESULT_BACKEND")
        orig_redis = os.environ.get("REDIS_URL")

        try:
            # Clear celery env vars to test default behavior
            os.environ.pop("CELERY_RESULT_BACKEND", None)
            os.environ["REDIS_URL"] = "redis://testhost:6379/5"

            test_config = Settings()
            assert test_config.celery_result_backend == "redis://testhost:6379/5"
        finally:
            # Restore env vars
            if orig_backend:
                os.environ["CELERY_RESULT_BACKEND"] = orig_backend
            if orig_redis:
                os.environ["REDIS_URL"] = orig_redis

    def test_log_level_uppercase_validator(self):
        """Test that log_level is converted to uppercase."""
        test_config = Settings(log_level="info")
        assert test_config.log_level == "INFO"

    def test_extraction_strategy_values(self):
        """Test that extraction strategy has valid value."""
        valid_strategies = ["fallback", "parallel_local", "parallel_all", "hybrid"]
        assert settings.default_extraction_strategy in valid_strategies

    def test_similarity_threshold_range(self):
        """Test that similarity_threshold is in valid range."""
        assert 0.0 <= settings.similarity_threshold <= 1.0

    def test_cors_origins_is_list(self):
        """Test that cors_origins is a list."""
        assert isinstance(settings.cors_origins, list)

    def test_storage_paths_are_path_objects(self):
        """Test that storage paths are Path objects."""
        assert isinstance(settings.upload_dir, Path)
        assert isinstance(settings.output_dir, Path)
        assert isinstance(settings.cache_dir, Path)
        assert isinstance(settings.log_dir, Path)


@pytest.mark.unit
@pytest.mark.config
def test_reload_settings():
    """Test reload_settings() function."""
    import os

    # Save original value
    original_port = settings.api_port

    # Change environment variable
    os.environ["API_PORT"] = "9000"

    # Reload settings
    new_settings = reload_settings()

    # Check that new settings reflect the change
    assert new_settings.api_port == 9000

    # Restore original
    os.environ["API_PORT"] = str(original_port)
    reload_settings()


@pytest.mark.unit
@pytest.mark.config
def test_ensure_directories(temp_dir):
    """Test ensure_directories() method."""
    # Create test settings with temp directories
    test_config = Settings(
        upload_dir=temp_dir / "uploads",
        output_dir=temp_dir / "outputs",
        cache_dir=temp_dir / "cache",
        log_dir=temp_dir / "logs",
    )

    # Ensure directories are created
    test_config.ensure_directories()

    # Verify all directories exist
    assert test_config.upload_dir.exists()
    assert test_config.output_dir.exists()
    assert test_config.cache_dir.exists()
    assert test_config.log_dir.exists()
