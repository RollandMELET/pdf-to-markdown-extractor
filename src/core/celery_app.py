"""
PDF-to-Markdown Extractor - Celery Application.

This is a minimal stub to enable docker-compose worker testing.
Full implementation in later features.
"""

from celery import Celery

# Create Celery application
app = Celery(
    "pdf-extractor",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

# Basic configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@app.task
def health_check():
    """Simple health check task for testing."""
    return {"status": "ok", "message": "Celery worker is running"}
