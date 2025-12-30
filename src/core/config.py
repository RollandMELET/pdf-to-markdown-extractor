"""
PDF-to-Markdown Extractor - Configuration Management.

Centralized configuration using Pydantic Settings with type validation
and environment variable loading.
"""

from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings are typed and validated using Pydantic. Values are loaded
    from environment variables with sensible defaults.

    Example:
        >>> from src.core.config import settings
        >>> print(settings.api_port)
        8000
        >>> print(settings.redis_url)
        redis://redis:6379/0
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================
    # Application Metadata
    # ==========================================
    app_name: str = Field(
        default="PDF-to-Markdown Extractor",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="production",
        description="Runtime environment"
    )

    # ==========================================
    # API Configuration
    # ==========================================
    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="API server port"
    )
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    api_workers: int = Field(
        default=2,
        ge=1,
        description="Number of Uvicorn workers"
    )
    api_reload: bool = Field(
        default=False,
        description="Enable auto-reload (development only)"
    )

    # ==========================================
    # Redis Configuration
    # ==========================================
    redis_url: str = Field(
        default="redis://redis:6379/0",
        description="Redis connection URL"
    )
    redis_max_connections: int = Field(
        default=20,
        ge=1,
        description="Maximum Redis connections in pool"
    )
    redis_socket_timeout: int = Field(
        default=5,
        ge=1,
        description="Redis socket timeout in seconds"
    )

    # ==========================================
    # Celery Configuration
    # ==========================================
    celery_broker_url: Optional[str] = Field(
        default=None,
        description="Celery broker URL (defaults to redis_url)"
    )
    celery_result_backend: Optional[str] = Field(
        default=None,
        description="Celery result backend URL (defaults to redis_url)"
    )
    celery_task_time_limit: int = Field(
        default=600,
        ge=60,
        description="Celery task hard time limit in seconds"
    )
    celery_task_soft_time_limit: int = Field(
        default=540,
        ge=60,
        description="Celery task soft time limit in seconds"
    )
    celery_worker_prefetch_multiplier: int = Field(
        default=1,
        ge=1,
        description="Number of tasks to prefetch per worker"
    )
    celery_worker_max_tasks_per_child: int = Field(
        default=50,
        ge=1,
        description="Max tasks per worker before restart"
    )

    # ==========================================
    # Logging Configuration
    # ==========================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(
        default="json",
        description="Log output format"
    )
    log_dir: Path = Field(
        default=Path("/app/logs"),
        description="Directory for log files"
    )
    log_rotation: str = Field(
        default="100 MB",
        description="Log rotation trigger (size)"
    )
    log_retention: str = Field(
        default="30 days",
        description="Log retention duration"
    )
    log_compression: str = Field(
        default="zip",
        description="Log compression format"
    )

    # ==========================================
    # External API Keys
    # ==========================================
    mistral_api_key: Optional[str] = Field(
        default=None,
        description="Mistral AI API key for OCR"
    )

    # ==========================================
    # Processing Limits
    # ==========================================
    max_file_size_mb: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum upload file size in MB"
    )
    max_pages: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of pages to process"
    )
    extraction_timeout_seconds: int = Field(
        default=600,
        ge=60,
        le=3600,
        description="Extraction timeout in seconds"
    )

    # ==========================================
    # Storage Paths
    # ==========================================
    upload_dir: Path = Field(
        default=Path("/app/data/uploads"),
        description="Directory for uploaded files"
    )
    output_dir: Path = Field(
        default=Path("/app/data/outputs"),
        description="Directory for extraction outputs"
    )
    cache_dir: Path = Field(
        default=Path("/app/data/cache"),
        description="Directory for cached data"
    )

    # ==========================================
    # Extraction Strategy
    # ==========================================
    default_extraction_strategy: Literal[
        "fallback", "parallel_local", "parallel_all", "hybrid"
    ] = Field(
        default="fallback",
        description="Default extraction strategy"
    )
    similarity_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for divergence detection"
    )

    # ==========================================
    # CORS Configuration
    # ==========================================
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )

    # ==========================================
    # Validators
    # ==========================================

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is uppercase."""
        if isinstance(v, str):
            return v.upper()
        return v

    @field_validator("celery_broker_url", mode="before")
    @classmethod
    def validate_celery_broker_url(cls, v: Optional[str], info) -> str:
        """Default celery_broker_url to redis_url if not set."""
        if v is None:
            # Access redis_url from the values being validated
            return info.data.get("redis_url", "redis://redis:6379/0")
        return v

    @field_validator("celery_result_backend", mode="before")
    @classmethod
    def validate_celery_result_backend(cls, v: Optional[str], info) -> str:
        """Default celery_result_backend to redis_url if not set."""
        if v is None:
            return info.data.get("redis_url", "redis://redis:6379/0")
        return v

    # ==========================================
    # Computed Properties
    # ==========================================

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    def ensure_directories(self) -> None:
        """
        Ensure all required directories exist.

        Creates upload_dir, output_dir, cache_dir, and log_dir if they
        don't exist.
        """
        for directory in [
            self.upload_dir,
            self.output_dir,
            self.cache_dir,
            self.log_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_summary(self) -> dict:
        """
        Get a summary of current configuration.

        Returns:
            dict: Configuration summary (safe for logging, no secrets).

        Example:
            >>> from src.core.config import settings
            >>> summary = settings.get_summary()
            >>> print(summary['app_name'])
            PDF-to-Markdown Extractor
        """
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "environment": self.environment,
            "api_port": self.api_port,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "redis_url": self._mask_url(self.redis_url),
            "max_file_size_mb": self.max_file_size_mb,
            "max_pages": self.max_pages,
            "extraction_strategy": self.default_extraction_strategy,
            "mistral_api_key_set": self.mistral_api_key is not None,
        }

    @staticmethod
    def _mask_url(url: str) -> str:
        """
        Mask credentials in URL for safe logging.

        Args:
            url: URL potentially containing credentials.

        Returns:
            str: URL with credentials masked.

        Example:
            >>> Settings._mask_url("redis://user:pass@host:6379/0")
            redis://***:***@host:6379/0
        """
        if "@" in url:
            protocol, rest = url.split("://", 1)
            if "@" in rest:
                creds, host = rest.split("@", 1)
                return f"{protocol}://***:***@{host}"
        return url


# ==========================================
# Global Settings Instance
# ==========================================

settings = Settings()


# ==========================================
# Convenience Functions
# ==========================================

def get_settings() -> Settings:
    """
    Get the global settings instance.

    Returns:
        Settings: Application settings.

    Example:
        >>> from src.core.config import get_settings
        >>> config = get_settings()
        >>> print(config.api_port)
        8000
    """
    return settings


def reload_settings() -> Settings:
    """
    Reload settings from environment variables.

    This creates a new Settings instance, useful for testing or
    when environment variables change at runtime.

    Returns:
        Settings: New settings instance.

    Example:
        >>> import os
        >>> os.environ['API_PORT'] = '9000'
        >>> config = reload_settings()
        >>> print(config.api_port)
        9000
    """
    global settings
    settings = Settings()
    return settings
