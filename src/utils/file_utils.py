"""
PDF-to-Markdown Extractor - File Utilities.

Utilities for file and directory management.
"""

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from loguru import logger

from src.core.config import settings


def create_output_dir(
    base_dir: Optional[Path] = None,
    job_id: Optional[str] = None,
) -> Path:
    """
    Create an output directory for extraction results.

    Creates a unique directory for storing extraction outputs.
    Directory name format: YYYYMMDD_HHMMSS_{job_id}

    Args:
        base_dir: Base directory for outputs (default: settings.output_dir).
        job_id: Optional job ID to include in directory name.

    Returns:
        Path: Created output directory path.

    Example:
        >>> output_dir = create_output_dir(job_id="abc123")
        >>> print(output_dir)
        /app/data/outputs/20251230_153045_abc123
    """
    base_dir = base_dir or settings.output_dir

    # Generate timestamp-based directory name
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if job_id:
        dir_name = f"{timestamp}_{job_id}"
    else:
        dir_name = timestamp

    output_path = base_dir / dir_name

    # Create directory
    output_path.mkdir(parents=True, exist_ok=True)

    logger.debug(f"Created output directory: {output_path}")

    return output_path


def cleanup_old_outputs(
    base_dir: Optional[Path] = None,
    max_age_days: int = 7,
    dry_run: bool = False,
) -> int:
    """
    Clean up old output directories.

    Removes output directories older than specified age.

    Args:
        base_dir: Base directory containing outputs (default: settings.output_dir).
        max_age_days: Maximum age in days before deletion (default: 7).
        dry_run: If True, only report what would be deleted without deleting.

    Returns:
        int: Number of directories deleted (or that would be deleted if dry_run).

    Example:
        >>> # Delete outputs older than 7 days
        >>> deleted = cleanup_old_outputs(max_age_days=7)
        >>> print(f"Deleted {deleted} old directories")
    """
    base_dir = base_dir or settings.output_dir

    if not base_dir.exists():
        logger.warning(f"Output directory does not exist: {base_dir}")
        return 0

    # Calculate cutoff time
    cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
    cutoff_timestamp = cutoff_time.timestamp()

    deleted_count = 0

    # Iterate through directories
    for item in base_dir.iterdir():
        if item.is_dir():
            # Check modification time
            mtime = item.stat().st_mtime

            if mtime < cutoff_timestamp:
                if dry_run:
                    logger.info(f"Would delete (dry-run): {item.name}")
                    deleted_count += 1
                else:
                    try:
                        shutil.rmtree(item)
                        logger.info(f"Deleted old output directory: {item.name}")
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Failed to delete {item.name}: {e}")

    logger.info(
        f"Cleanup completed: {deleted_count} directories "
        f"{'would be ' if dry_run else ''}deleted (max_age={max_age_days} days)"
    )

    return deleted_count


def get_file_info(file_path: Path) -> dict:
    """
    Get file information.

    Args:
        file_path: Path to file.

    Returns:
        dict: File information (name, size, modified time, etc.).

    Example:
        >>> info = get_file_info(Path("document.pdf"))
        >>> print(info["size_mb"])
        2.5
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    stat = file_path.stat()

    return {
        "name": file_path.name,
        "path": str(file_path),
        "size_bytes": stat.st_size,
        "size_kb": stat.st_size / 1024,
        "size_mb": stat.st_size / (1024 * 1024),
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "extension": file_path.suffix,
    }


def ensure_directory(directory: Path) -> Path:
    """
    Ensure a directory exists, create if it doesn't.

    Args:
        directory: Path to directory.

    Returns:
        Path: The directory path (created if needed).

    Example:
        >>> dir_path = ensure_directory(Path("/app/data/temp"))
        >>> assert dir_path.exists()
    """
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename to be safe for filesystem.

    Removes or replaces unsafe characters and limits length.

    Args:
        filename: Original filename.
        max_length: Maximum filename length (default: 255).

    Returns:
        str: Sanitized filename.

    Example:
        >>> safe = safe_filename("my file: test?.pdf")
        >>> print(safe)
        my_file_test.pdf
    """
    # Replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    safe = filename

    for char in unsafe_chars:
        safe = safe.replace(char, "_")

    # Remove leading/trailing spaces and dots
    safe = safe.strip(". ")

    # Limit length
    if len(safe) > max_length:
        name, ext = safe.rsplit(".", 1) if "." in safe else (safe, "")
        name = name[: max_length - len(ext) - 1]
        safe = f"{name}.{ext}" if ext else name

    return safe


def copy_file_to_upload(
    source_path: Path,
    upload_dir: Optional[Path] = None,
    new_name: Optional[str] = None,
) -> Path:
    """
    Copy a file to the upload directory.

    Args:
        source_path: Source file path.
        upload_dir: Upload directory (default: settings.upload_dir).
        new_name: Optional new filename (default: keep original).

    Returns:
        Path: Path to copied file.

    Example:
        >>> uploaded = copy_file_to_upload(Path("/tmp/doc.pdf"))
        >>> print(uploaded)
        /app/data/uploads/doc.pdf
    """
    upload_dir = upload_dir or settings.upload_dir
    ensure_directory(upload_dir)

    # Determine destination filename
    if new_name:
        dest_name = safe_filename(new_name)
    else:
        dest_name = safe_filename(source_path.name)

    dest_path = upload_dir / dest_name

    # Copy file
    shutil.copy2(source_path, dest_path)
    logger.debug(f"Copied file: {source_path.name} -> {dest_path}")

    return dest_path
