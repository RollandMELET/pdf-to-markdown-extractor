"""
PDF-to-Markdown Extractor - Base Extractor Classes.

Defines the abstract base class for all PDF extractors and the
ExtractionResult dataclass for standardized results.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ExtractionError(Exception):
    """
    Exception raised when PDF extraction fails.

    This is used by extractors to provide detailed error information
    when extraction cannot be completed.

    Attributes:
        extractor: Name of the extractor that failed.
        message: Error message describing what went wrong.
        file_path: Path to the PDF file that failed to extract.
        original_error: The original exception that caused the failure (if any).
    """

    def __init__(
        self,
        extractor: str,
        message: str,
        file_path: str,
        original_error: Optional[Exception] = None,
    ):
        """Initialize ExtractionError."""
        self.extractor = extractor
        self.message = message
        self.file_path = file_path
        self.original_error = original_error

        error_msg = f"[{extractor}] {message} (file: {file_path})"
        if original_error:
            error_msg += f" | Original error: {original_error}"

        super().__init__(error_msg)


@dataclass
class ExtractionResult:
    """
    Result of a PDF extraction operation.

    This dataclass standardizes the output format for all extractors,
    making it easy to compare results and build consensus.

    Attributes:
        markdown: Extracted content in markdown format.
        metadata: PDF metadata (title, author, page_count, etc.).
        images: List of extracted image paths or references.
        tables: List of extracted tables (as markdown or structured data).
        confidence_score: Confidence in extraction quality (0.0-1.0).
        extractor_name: Name of the extractor that produced this result.
        extractor_version: Version of the extractor.
        extraction_time: Time taken for extraction in seconds.
        page_count: Number of pages in the PDF.
        errors: List of errors encountered during extraction.
        warnings: List of warnings generated during extraction.
        extraction_timestamp: When the extraction was performed.
        options: Extraction options used (for reproducibility).

    Example:
        >>> result = ExtractionResult(
        ...     markdown="# Title\\n\\nContent",
        ...     metadata={"title": "My Document"},
        ...     confidence_score=0.95,
        ...     extractor_name="DoclingExtractor"
        ... )
        >>> print(result.markdown)
        # Title

        Content
    """

    markdown: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    images: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    confidence_score: float = 1.0
    extractor_name: str = "UnknownExtractor"
    extractor_version: str = "0.0.0"
    extraction_time: float = 0.0
    page_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    extraction_timestamp: datetime = field(default_factory=datetime.utcnow)
    options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate extraction result after initialization."""
        # Ensure confidence_score is in valid range
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(f"confidence_score must be between 0.0 and 1.0, got {self.confidence_score}")

        # Ensure markdown is not None
        if self.markdown is None:
            self.markdown = ""

    @property
    def success(self) -> bool:
        """
        Check if extraction was successful.

        Returns:
            bool: True if extraction succeeded (no errors and has content).
        """
        return len(self.errors) == 0 and len(self.markdown) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if extraction generated warnings."""
        return len(self.warnings) > 0

    @property
    def has_errors(self) -> bool:
        """Check if extraction encountered errors."""
        return len(self.errors) > 0

    @property
    def image_count(self) -> int:
        """Get number of extracted images."""
        return len(self.images)

    @property
    def table_count(self) -> int:
        """Get number of extracted tables."""
        return len(self.tables)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary.

        Returns:
            dict: Result as dictionary (JSON-serializable).
        """
        return {
            "markdown": self.markdown,
            "metadata": self.metadata,
            "images": self.images,
            "tables": self.tables,
            "confidence_score": self.confidence_score,
            "extractor_name": self.extractor_name,
            "extractor_version": self.extractor_version,
            "extraction_time": self.extraction_time,
            "page_count": self.page_count,
            "errors": self.errors,
            "warnings": self.warnings,
            "extraction_timestamp": self.extraction_timestamp.isoformat(),
            "options": self.options,
            "success": self.success,
            "image_count": self.image_count,
            "table_count": self.table_count,
        }


class BaseExtractor(ABC):
    """
    Abstract base class for PDF extractors.

    All extractor implementations must inherit from this class and
    implement the required abstract methods.

    Attributes:
        name: Unique name of the extractor (e.g., "DoclingExtractor").
        version: Version of the extractor implementation.
        description: Human-readable description of the extractor.

    Example:
        >>> class MyExtractor(BaseExtractor):
        ...     name = "MyExtractor"
        ...     version = "1.0.0"
        ...
        ...     def extract(self, file_path, options):
        ...         # Implementation here
        ...         return ExtractionResult(...)
        ...
        ...     def is_available(self):
        ...         return True
        ...
        ...     def get_capabilities(self):
        ...         return {"tables": True, "images": True}
    """

    name: str = "BaseExtractor"
    version: str = "0.0.0"
    description: str = "Base PDF extractor"

    @abstractmethod
    def extract(self, file_path: Path, options: Optional[Dict[str, Any]] = None) -> ExtractionResult:
        """
        Extract markdown content from a PDF file.

        Args:
            file_path: Path to the PDF file to extract.
            options: Optional extraction options (e.g., {"ocr": True, "images": False}).

        Returns:
            ExtractionResult: Extraction result with markdown and metadata.

        Raises:
            FileNotFoundError: If file_path does not exist.
            PDFExtractionError: If extraction fails.

        Example:
            >>> extractor = MyExtractor()
            >>> result = extractor.extract(Path("document.pdf"))
            >>> print(result.markdown)
        """
        raise NotImplementedError("Subclass must implement extract()")

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the extractor is available and dependencies are installed.

        Returns:
            bool: True if extractor can be used, False otherwise.

        Example:
            >>> extractor = DoclingExtractor()
            >>> if extractor.is_available():
            ...     result = extractor.extract(pdf_path)
        """
        raise NotImplementedError("Subclass must implement is_available()")

    @abstractmethod
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get extractor capabilities.

        Returns:
            dict: Capabilities dictionary with boolean values.
                  Keys: tables, images, ocr, formulas, multi_column, metadata

        Example:
            >>> extractor = DoclingExtractor()
            >>> caps = extractor.get_capabilities()
            >>> if caps["tables"]:
            ...     print("Extractor supports table extraction")
        """
        raise NotImplementedError("Subclass must implement get_capabilities()")

    def validate_file(self, file_path: Path) -> None:
        """
        Validate that the file exists and is a PDF.

        Args:
            file_path: Path to validate.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file is not a PDF.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        if file_path.suffix.lower() != ".pdf":
            raise ValueError(f"File is not a PDF: {file_path}")

    def get_info(self) -> Dict[str, Any]:
        """
        Get extractor information.

        Returns:
            dict: Extractor name, version, description, and capabilities.
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "available": self.is_available(),
            "capabilities": self.get_capabilities(),
        }

    def __str__(self) -> str:
        """String representation of extractor."""
        return f"{self.name} v{self.version}"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"<{self.__class__.__name__}(name='{self.name}', version='{self.version}')>"
