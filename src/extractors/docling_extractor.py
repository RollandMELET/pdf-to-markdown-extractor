"""
PDF-to-Markdown Extractor - Docling Extractor.

PDF extractor using Docling library for high-quality extraction.
"""

import time
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from src.extractors.base import BaseExtractor, ExtractionResult


class DoclingExtractor(BaseExtractor):
    """
    PDF extractor using Docling library.

    Docling provides high-quality PDF extraction with support for:
    - Text extraction
    - Table detection and extraction
    - Image extraction
    - Multi-column layout handling
    - Metadata extraction

    Example:
        >>> from pathlib import Path
        >>> extractor = DoclingExtractor()
        >>> if extractor.is_available():
        ...     result = extractor.extract(Path("document.pdf"))
        ...     print(result.markdown)
    """

    name = "DoclingExtractor"
    version = "1.0.0"
    description = "High-quality PDF extraction using Docling library"

    def __init__(self):
        """Initialize Docling extractor."""
        self._converter = None

    def _get_converter(self):
        """
        Get or create DocumentConverter instance.

        Returns:
            DocumentConverter: Docling document converter.
        """
        if self._converter is None:
            from docling.document_converter import DocumentConverter

            self._converter = DocumentConverter()
            logger.debug("DocumentConverter initialized")

        return self._converter

    def extract(
        self, file_path: Path, options: Optional[Dict[str, Any]] = None
    ) -> ExtractionResult:
        """
        Extract markdown content from PDF using Docling.

        Args:
            file_path: Path to PDF file.
            options: Extraction options (currently unused, reserved for future).

        Returns:
            ExtractionResult: Extraction result with markdown and metadata.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file is not a PDF.
            Exception: If extraction fails.

        Example:
            >>> extractor = DoclingExtractor()
            >>> result = extractor.extract(Path("doc.pdf"))
            >>> print(result.markdown)
        """
        # Validate file
        self.validate_file(file_path)

        # Initialize options
        options = options or {}

        # Start timing
        start_time = time.time()

        logger.info(f"Starting Docling extraction: {file_path.name}")

        try:
            # Get converter
            converter = self._get_converter()

            # Convert PDF to Docling document
            result = converter.convert(str(file_path))

            # Extract markdown
            markdown_content = result.document.export_to_markdown()

            # Calculate extraction time
            extraction_time = time.time() - start_time

            # Build extraction result
            extraction_result = ExtractionResult(
                markdown=markdown_content,
                metadata={
                    "filename": file_path.name,
                    "file_size": file_path.stat().st_size,
                },
                confidence_score=0.95,  # Docling is generally high confidence
                extractor_name=self.name,
                extractor_version=self.version,
                extraction_time=extraction_time,
                page_count=0,  # Will be added in Feature #22
                options=options,
            )

            logger.info(
                f"Docling extraction completed: {file_path.name} "
                f"({extraction_time:.2f}s, {len(markdown_content)} chars)"
            )

            return extraction_result

        except Exception as e:
            extraction_time = time.time() - start_time
            logger.error(f"Docling extraction failed for {file_path.name}: {e}")

            # Return result with error
            return ExtractionResult(
                markdown="",
                metadata={"filename": file_path.name},
                confidence_score=0.0,
                extractor_name=self.name,
                extractor_version=self.version,
                extraction_time=extraction_time,
                errors=[str(e)],
                options=options,
            )

    def is_available(self) -> bool:
        """
        Check if Docling is available.

        Returns:
            bool: True if Docling can be imported, False otherwise.

        Example:
            >>> extractor = DoclingExtractor()
            >>> if extractor.is_available():
            ...     print("Docling is ready")
        """
        try:
            from docling.document_converter import DocumentConverter

            return True
        except ImportError:
            return False

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get Docling extractor capabilities.

        Returns:
            dict: Capabilities supported by Docling.

        Example:
            >>> extractor = DoclingExtractor()
            >>> caps = extractor.get_capabilities()
            >>> print(caps["tables"])
            True
        """
        return {
            "tables": True,  # Will be implemented in Feature #20
            "images": True,  # Will be implemented in Feature #21
            "ocr": False,  # Docling doesn't do OCR directly
            "formulas": True,  # Docling handles formulas well
            "multi_column": True,  # Docling handles multi-column layouts
            "metadata": True,  # Will be implemented in Feature #22
        }
