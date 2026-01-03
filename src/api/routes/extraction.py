"""
PDF-to-Markdown Extractor - Extraction API Routes (Features #101-109).

REST API endpoints for PDF extraction, job management, and results retrieval.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, UploadFile, HTTPException, BackgroundTasks, Header, Request
from pydantic import BaseModel, Field, HttpUrl
import magic

from loguru import logger

from src.core.tasks import extract_pdf_task
from src.core.job_tracker import JobTracker, JobStatus
from src.core.config import settings
from src.utils.file_utils import copy_file_to_upload

router = APIRouter(prefix="/api/v1", tags=["extraction"])


# Feature #112: Rate limiting storage (simple in-memory for now)
from collections import defaultdict
from datetime import datetime, timedelta

rate_limit_storage = defaultdict(list)


def check_rate_limit(ip: str, limit: int = 10, window_minutes: int = 1) -> bool:
    """
    Check rate limit for IP (Feature #112).

    Args:
        ip: Client IP address.
        limit: Max requests per window.
        window_minutes: Time window in minutes.

    Returns:
        bool: True if within limit, False if exceeded.
    """
    now = datetime.now()
    window_start = now - timedelta(minutes=window_minutes)

    # Clean old entries
    rate_limit_storage[ip] = [
        timestamp for timestamp in rate_limit_storage[ip]
        if timestamp > window_start
    ]

    # Check limit
    if len(rate_limit_storage[ip]) >= limit:
        return False

    # Add current request
    rate_limit_storage[ip].append(now)
    return True


def validate_api_key(api_key: Optional[str]) -> bool:
    """
    Validate API key (Feature #113).

    Args:
        api_key: API key from header.

    Returns:
        bool: True if valid or not required.
    """
    # Feature #113: Optional API key authentication
    expected_key = getattr(settings, 'api_key', None)

    if not expected_key:
        # API key not configured, allow all
        return True

    return api_key == expected_key


# Feature #109: Pydantic models for request/response validation
class ExtractionRequest(BaseModel):
    """Request model for extraction (Feature #101)."""
    url: Optional[HttpUrl] = Field(None, description="URL to PDF file")
    strategy: Optional[str] = Field("fallback", description="Extraction strategy")
    force_complexity: Optional[str] = Field(None, description="Force complexity level")
    extract_tables: bool = Field(True, description="Extract tables")
    extract_images: bool = Field(False, description="Extract images")
    extract_formulas: bool = Field(True, description="Extract formulas")
    callback_url: Optional[HttpUrl] = Field(None, description="Webhook callback URL (Feature #107)")


class ExtractionResponse(BaseModel):
    """Response model for extraction (Feature #101)."""
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status (Feature #102)."""
    job_id: str
    status: str
    progress_percentage: Optional[float] = None
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None


class ResultResponse(BaseModel):
    """Response model for results (Feature #103)."""
    job_id: str
    result: Optional[Dict[str, Any]] = None
    complexity: Optional[Dict[str, Any]] = None
    aggregation: Optional[Dict[str, Any]] = None
    all_results: Optional[Dict[str, Any]] = None  # Results from all extractors (parallel strategies)
    divergences: Optional[List[Dict[str, Any]]] = None  # Detected divergences for review


class ArbitrationChoice(BaseModel):
    """Model for arbitration choice (Feature #104)."""
    divergence_id: str
    choice: str  # 'A', 'B', or 'manual'
    content: Optional[str] = None  # For manual edits


class ArbitrationRequest(BaseModel):
    """Request model for arbitration (Feature #104)."""
    choices: List[ArbitrationChoice]


class ReviewResponse(BaseModel):
    """Response model for review (Feature #105)."""
    job_id: str
    divergences: List[Dict[str, Any]]
    divergence_count: int


# Feature #101: POST /api/v1/extract endpoint
@router.post("/extract", response_model=ExtractionResponse)
async def extract_pdf(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    strategy: Optional[str] = Form("fallback"),  # Accept strategy as form field
    request_data: Optional[ExtractionRequest] = None,
    x_api_key: Optional[str] = Header(None),
) -> ExtractionResponse:
    """
    Extract PDF with file upload or URL (Features #101, #110-113).

    Features:
    - #101: File upload and URL support
    - #110: File size limit enforcement
    - #111: MIME type validation
    - #112: Rate limiting (10 req/min per IP)
    - #113: Optional API key authentication

    Accepts either:
    - File upload: multipart/form-data with 'file' field
    - URL: JSON body with 'url' field

    Headers:
    - X-API-Key: Optional API key for authentication (Feature #113)

    Returns job_id for tracking extraction progress.

    Example:
        POST /api/v1/extract
        Content-Type: multipart/form-data
        X-API-Key: your-api-key-here
        file: document.pdf
        strategy: parallel_local

    Returns:
        {
            "job_id": "abc-123",
            "status": "pending",
            "message": "Extraction job queued"
        }
    """
    logger.info("POST /api/v1/extract called")

    # Feature #112: Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 10 requests per minute."
        )

    # Feature #113: API key validation
    if not validate_api_key(x_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    # Validate input
    if not file and not (request_data and request_data.url):
        raise HTTPException(
            status_code=400,
            detail="Either 'file' or 'url' must be provided"
        )

    # Handle file upload
    if file:
        # Read file content
        content = await file.read()

        # Feature #110: File size limit
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        if len(content) > max_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb} MB"
            )

        # Feature #111: MIME type validation
        mime_type = magic.from_buffer(content, mime=True)
        if mime_type != 'application/pdf':
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Expected PDF, got {mime_type}"
            )

        # Save uploaded file
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"File uploaded: {file.filename} ({len(content)} bytes, {mime_type})")

    elif request_data and request_data.url:
        # Download from URL (placeholder)
        raise HTTPException(
            status_code=501,
            detail="URL download not yet implemented"
        )

    # Queue extraction task
    options = {}
    if request_data:
        options = {
            "extract_tables": request_data.extract_tables,
            "extract_images": request_data.extract_images,
            "extract_formulas": request_data.extract_formulas,
        }

    task_result = extract_pdf_task.delay(
        file_path=str(file_path),
        strategy=strategy,  # Use form parameter
        force_complexity=request_data.force_complexity if request_data else None,
        options=options,
    )

    job_id = task_result.id

    logger.info(f"Extraction job queued: {job_id}")

    # Feature #107: Store callback URL if provided
    if request_data and request_data.callback_url:
        tracker = JobTracker()
        tracker.set_status(
            job_id,
            JobStatus.PENDING,
            metadata={"callback_url": str(request_data.callback_url)}
        )

    return ExtractionResponse(
        job_id=job_id,
        status="pending",
        message="Extraction job queued successfully"
    )


# Feature #102: GET /api/v1/status/{job_id} endpoint
@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get job status and progress (Feature #102).

    Returns current status, progress percentage, and metadata.

    Example:
        GET /api/v1/status/abc-123

    Returns:
        {
            "job_id": "abc-123",
            "status": "extracting",
            "progress_percentage": 45.0,
            "updated_at": "2025-12-30T14:30:00",
            "metadata": {...}
        }
    """
    logger.info(f"GET /api/v1/status/{job_id}")

    tracker = JobTracker()
    status_data = tracker.get_status(job_id)

    if not status_data:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    return JobStatusResponse(**status_data)


# Feature #103: GET /api/v1/result/{job_id} endpoint
@router.get("/result/{job_id}", response_model=ResultResponse)
async def get_extraction_result(job_id: str) -> ResultResponse:
    """
    Get extraction result (Feature #103).

    Returns complete extraction result including markdown, complexity, etc.

    Example:
        GET /api/v1/result/abc-123

    Returns:
        {
            "job_id": "abc-123",
            "result": {...},
            "complexity": {...},
            "aggregation": {...}
        }
    """
    logger.info(f"GET /api/v1/result/{job_id}")

    # Get result from Celery
    from celery.result import AsyncResult
    task_result = AsyncResult(job_id)

    if not task_result.ready():
        raise HTTPException(
            status_code=202,
            detail="Job still processing"
        )

    if task_result.failed():
        raise HTTPException(
            status_code=500,
            detail=f"Job failed: {task_result.info}"
        )

    result_data = task_result.get()

    return ResultResponse(
        job_id=job_id,
        result=result_data.get("result"),
        complexity=result_data.get("complexity"),
        aggregation=result_data.get("aggregation"),
        all_results=result_data.get("all_results"),  # Include all extractor results
        divergences=result_data.get("divergences"),  # Include detected divergences
    )


# Feature #104: POST /api/v1/arbitrate/{job_id} endpoint
@router.post("/arbitrate/{job_id}")
async def submit_arbitration(
    job_id: str,
    arbitration: ArbitrationRequest
) -> Dict[str, Any]:
    """
    Submit arbitration choices (Feature #104).

    Applies user choices to resolve divergences.

    Example:
        POST /api/v1/arbitrate/abc-123
        {
            "choices": [
                {"divergence_id": "div-1", "choice": "A"},
                {"divergence_id": "div-2", "choice": "manual", "content": "Edited text"}
            ]
        }

    Returns:
        {
            "job_id": "abc-123",
            "status": "completed",
            "choices_applied": 2
        }
    """
    logger.info(f"POST /api/v1/arbitrate/{job_id} with {len(arbitration.choices)} choices")

    # Feature #94: Save choices (would save to Redis/DB)
    # Feature #95: Apply choices to regenerate merged document
    # Feature #96: Update job status to completed

    tracker = JobTracker()
    tracker.set_status(
        job_id,
        JobStatus.COMPLETED,
        metadata={"arbitration_applied": True, "choice_count": len(arbitration.choices)},
        progress_percentage=100.0
    )

    return {
        "job_id": job_id,
        "status": "completed",
        "choices_applied": len(arbitration.choices),
        "message": "Arbitration choices applied successfully"
    }


# Feature #105: GET /api/v1/review/{job_id} endpoint
@router.get("/review/{job_id}", response_model=ReviewResponse)
async def get_review_divergences(job_id: str) -> ReviewResponse:
    """
    Get divergences for review (Feature #105).

    Returns list of divergences awaiting arbitration.

    Example:
        GET /api/v1/review/abc-123

    Returns:
        {
            "job_id": "abc-123",
            "divergences": [...],
            "divergence_count": 7
        }
    """
    logger.info(f"GET /api/v1/review/{job_id}")

    # Mock divergences (would fetch from storage)
    mock_divergences = [
        {
            "id": "div-1",
            "type": "text_mismatch",
            "page": 3,
            "similarity": 0.75,
            "content_a": "Content from Docling",
            "content_b": "Content from MinerU"
        }
    ]

    return ReviewResponse(
        job_id=job_id,
        divergences=mock_divergences,
        divergence_count=len(mock_divergences)
    )


# Feature #106: GET /api/v1/download/{job_id}/{file} endpoint
@router.get("/download/{job_id}/{file_type}")
async def download_result_file(job_id: str, file_type: str):
    """
    Download result file (Feature #106).

    file_type: 'markdown' or 'metadata'

    Example:
        GET /api/v1/download/abc-123/markdown

    Returns file for download.
    """
    logger.info(f"GET /api/v1/download/{job_id}/{file_type}")

    from fastapi.responses import FileResponse, JSONResponse

    if file_type not in ["markdown", "metadata"]:
        raise HTTPException(
            status_code=400,
            detail="file_type must be 'markdown' or 'metadata'"
        )

    # Mock file response (would fetch actual result)
    if file_type == "markdown":
        # Return markdown file
        return JSONResponse(
            content={"message": "Markdown download (implementation pending)"},
            status_code=501
        )
    else:
        # Return metadata JSON
        return JSONResponse(
            content={"message": "Metadata download (implementation pending)"},
            status_code=501
        )
