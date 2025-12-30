"""
PDF-to-Markdown Extractor - Job Status Tracker (Feature #65).

Tracks extraction job status in Redis.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger

from src.utils.redis_client import get_redis_client


class JobStatus(Enum):
    """
    Job status enumeration (Feature #65).

    States:
        PENDING: Job queued, not started yet
        EXTRACTING: Extraction in progress
        COMPARING: Comparing results (for parallel strategies)
        COMPLETED: Job finished successfully
        FAILED: Job failed with error
    """

    PENDING = "pending"
    EXTRACTING = "extracting"
    COMPARING = "comparing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobTracker:
    """
    Job status tracker using Redis (Feature #65).

    Stores and retrieves job status information in Redis for monitoring
    and progress tracking.

    Example:
        >>> tracker = JobTracker()
        >>> tracker.set_status("job-123", JobStatus.EXTRACTING)
        >>> status = tracker.get_status("job-123")
        >>> print(status['status'])
        extracting
    """

    def __init__(self, ttl: int = 86400):
        """
        Initialize job tracker.

        Args:
            ttl: TTL for job status in Redis (seconds). Default: 24 hours.
        """
        self.redis_client = get_redis_client()
        self.ttl = ttl

    def set_status(
        self,
        job_id: str,
        status: JobStatus,
        metadata: Optional[Dict[str, Any]] = None,
        progress_percentage: Optional[float] = None,
    ) -> None:
        """
        Store job status in Redis (Features #65-66).

        Args:
            job_id: Unique job identifier.
            status: Job status (pending, extracting, comparing, completed, failed).
            metadata: Additional job metadata (file_path, strategy, etc.).
            progress_percentage: Progress percentage 0-100 (Feature #66).

        Example:
            >>> tracker = JobTracker()
            >>> tracker.set_status(
            ...     "job-123",
            ...     JobStatus.EXTRACTING,
            ...     {"file": "document.pdf"},
            ...     progress_percentage=50.0
            ... )
        """
        key = f"job:{job_id}:status"

        status_data = {
            "job_id": job_id,
            "status": status.value,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Feature #66: Add progress percentage
        if progress_percentage is not None:
            status_data["progress_percentage"] = min(100.0, max(0.0, progress_percentage))

        if metadata:
            status_data["metadata"] = metadata

        try:
            # Store as JSON
            self.redis_client.set(key, json.dumps(status_data), ex=self.ttl)

            logger.debug(
                f"Job status updated: {job_id} -> {status.value} "
                f"({progress_percentage}%)" if progress_percentage else ""
            )

        except Exception as e:
            logger.warning(f"Failed to set job status: {e}")

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status from Redis (Feature #65).

        Args:
            job_id: Unique job identifier.

        Returns:
            dict: Job status data or None if not found.
                {
                    'job_id': str,
                    'status': str,
                    'updated_at': str,
                    'metadata': dict (optional),
                }

        Example:
            >>> tracker = JobTracker()
            >>> status = tracker.get_status("job-123")
            >>> if status:
            ...     print(f"Status: {status['status']}")
        """
        key = f"job:{job_id}:status"

        try:
            data = self.redis_client.get(key)

            if data:
                return json.loads(data)

            return None

        except Exception as e:
            logger.warning(f"Failed to get job status: {e}")
            return None

    def delete_status(self, job_id: str) -> bool:
        """
        Delete job status from Redis.

        Args:
            job_id: Unique job identifier.

        Returns:
            bool: True if deleted, False otherwise.
        """
        key = f"job:{job_id}:status"

        try:
            deleted_count = self.redis_client.delete(key)
            return deleted_count > 0

        except Exception as e:
            logger.warning(f"Failed to delete job status: {e}")
            return False

    def list_jobs(self, status_filter: Optional[JobStatus] = None) -> List[Dict[str, Any]]:
        """
        List all jobs, optionally filtered by status.

        Args:
            status_filter: Filter by job status (optional).

        Returns:
            list[dict]: List of job status data.

        Example:
            >>> tracker = JobTracker()
            >>> pending_jobs = tracker.list_jobs(JobStatus.PENDING)
            >>> print(len(pending_jobs))
        """
        # This requires scanning Redis keys (not implemented for now)
        # Will be implemented when needed
        logger.warning("list_jobs() not yet implemented")
        return []
