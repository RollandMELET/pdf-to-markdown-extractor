"""
PDF-to-Markdown Extractor - Celery Tasks.

Asynchronous tasks for PDF extraction, comparison, and processing.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from src.core.celery_app import celery_app
from src.core.job_tracker import JobTracker, JobStatus
from src.core.orchestrator import Orchestrator


def _serialize_result(extraction_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize extraction result for Celery.

    Args:
        extraction_result: Result from orchestrator.extract().

    Returns:
        dict: Serialized result (JSON-compatible).
    """
    serialized = {
        "complexity": extraction_result["complexity"],
        "strategy_used": extraction_result["strategy_used"],
    }

    # Serialize main result
    result = extraction_result["result"]
    if result:
        serialized["result"] = {
            "markdown": result.markdown,
            "metadata": result.metadata,
            "confidence_score": result.confidence_score,
            "extraction_time": result.extraction_time,
            "extractor_name": result.extractor_name,
            "extractor_version": result.extractor_version,
            "success": result.success,
            "page_count": result.page_count,
            "table_count": len(result.tables),
            "image_count": len(result.images),
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
        }

    # Serialize aggregation if present (parallel strategies)
    if "aggregation" in extraction_result:
        serialized["aggregation"] = {
            "extractor_count": extraction_result["aggregation"]["extractor_count"],
            "successful_count": extraction_result["aggregation"]["successful_count"],
            "average_confidence": extraction_result["aggregation"]["average_confidence"],
        }

    return serialized


@celery_app.task(
    name="pdf_extractor.extract_pdf",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def extract_pdf_task(
    self,
    file_path: str,
    strategy: Optional[str] = None,
    force_complexity: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Celery task for PDF extraction (Feature #64).

    Wraps orchestrator.extract() for async processing via Celery.

    Args:
        self: Celery task instance (bound).
        file_path: Path to PDF file as string.
        strategy: Extraction strategy (fallback, parallel_local, etc.).
        force_complexity: Force complexity level.
        options: Extraction options.

    Returns:
        dict: Extraction result serialized as dict.

    Example:
        >>> result = extract_pdf_task.delay("/path/to/doc.pdf")
        >>> result.get(timeout=600)
        {'result': {...}, 'complexity': {...}}
    """
    job_id = self.request.id
    tracker = JobTracker()

    logger.info(f"Celery task started: extract_pdf (job_id={job_id}, file={file_path})")

    # Feature #65-66: Set initial status with progress
    tracker.set_status(
        job_id,
        JobStatus.PENDING,
        metadata={"file_path": file_path, "strategy": strategy},
        progress_percentage=0.0
    )

    try:
        # Convert string path to Path object
        pdf_path = Path(file_path)

        # Feature #65-66: Update status to extracting
        tracker.set_status(job_id, JobStatus.EXTRACTING, progress_percentage=25.0)

        # Create orchestrator
        orchestrator = Orchestrator()

        # Extract
        extraction_result = orchestrator.extract(
            file_path=pdf_path,
            strategy=strategy,
            force_complexity=force_complexity,
            options=options,
        )

        # Feature #65-66: Update status if comparing (parallel extraction)
        if "aggregation" in extraction_result:
            tracker.set_status(job_id, JobStatus.COMPARING, progress_percentage=75.0)

        # Serialize ExtractionResult for Celery
        serialized = _serialize_result(extraction_result)

        # Feature #65-66: Update status to completed
        tracker.set_status(
            job_id,
            JobStatus.COMPLETED,
            metadata={"success": True, "confidence": serialized.get("result", {}).get("confidence_score")},
            progress_percentage=100.0
        )

        logger.info(f"Celery task completed: extract_pdf (job_id={job_id}, file={file_path})")

        return serialized

    except Exception as e:
        logger.error(f"Celery task failed: extract_pdf (job_id={job_id}, file={file_path}): {e}")

        # Feature #65: Update status to failed
        tracker.set_status(
            job_id,
            JobStatus.FAILED,
            metadata={"error": str(e)}
        )

        # Retry on failure
        raise self.retry(exc=e)


logger.info("Celery tasks module loaded")
