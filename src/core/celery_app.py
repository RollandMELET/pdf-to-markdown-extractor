"""
PDF-to-Markdown Extractor - Celery Application.

Celery configuration for asynchronous PDF extraction tasks.
"""

import os
from celery import Celery
from kombu import Exchange, Queue
from loguru import logger

# ==========================================
# Environment Configuration
# ==========================================
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# ==========================================
# Celery Application
# ==========================================
app = Celery(
    "pdf-extractor",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["src.core.tasks"]  # Auto-discover tasks (created in later features)
)

# ==========================================
# Celery Configuration
# ==========================================
app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit
    task_acks_late=True,  # Acknowledge after task completion
    worker_prefetch_multiplier=1,  # One task at a time per worker

    # Result backend
    result_expires=86400,  # Results expire after 24 hours
    result_persistent=True,

    # Retry policy
    task_default_max_retries=3,
    task_default_retry_delay=60,  # 1 minute between retries

    # Broker connection
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,

    # Task routing (default queue)
    task_default_queue="pdf-extraction",
    task_default_exchange="pdf-extraction",
    task_default_routing_key="pdf.extraction",

    # Queues definition
    task_queues=(
        Queue(
            "pdf-extraction",
            Exchange("pdf-extraction"),
            routing_key="pdf.extraction",
        ),
    ),

    # Worker settings
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    worker_disable_rate_limits=False,

    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


# ==========================================
# Event Handlers
# ==========================================
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Configure periodic tasks (if needed in future)."""
    # Placeholder for future periodic tasks (cleanup, monitoring, etc.)
    pass


# ==========================================
# Tasks
# ==========================================
@app.task(bind=True, name="pdf_extractor.health_check")
def health_check(self):
    """
    Health check task for monitoring worker availability.

    Returns:
        dict: Worker health status
    """
    logger.info(f"Health check task executed by worker: {self.request.hostname}")
    return {
        "status": "ok",
        "worker": self.request.hostname,
        "task_id": self.request.id,
        "message": "Celery worker is running and healthy"
    }
