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
            doc = result.document

            # Extract markdown
            markdown_content = doc.export_to_markdown()

            # Calculate extraction time
            extraction_time = time.time() - start_time

            # Extract tables (Feature #20)
            tables = self._extract_tables(doc)

            # Extract images (Feature #21)
            images = self._extract_images(doc, file_path, options)

            # Extract metadata (Feature #22)
            metadata = self._extract_metadata(doc, file_path)

            # Build extraction result
            extraction_result = ExtractionResult(
                markdown=markdown_content,
                metadata=metadata,
                tables=tables,
                images=images,
                confidence_score=0.95,  # Docling is generally high confidence
                extractor_name=self.name,
                extractor_version=self.version,
                extraction_time=extraction_time,
                page_count=metadata.get("page_count", 0),
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
            "tables": True,  # Implemented in Feature #20
            "images": True,  # Implemented in Feature #21
            "ocr": False,  # Docling doesn't do OCR directly
            "formulas": True,  # Docling handles formulas well
            "multi_column": True,  # Docling handles multi-column layouts
            "metadata": True,  # Implemented in Feature #22
        }

    def _extract_tables(self, doc) -> list[str]:
        """
        Extract tables from Docling document (Feature #20).

        Args:
            doc: Docling document object.

        Returns:
            list[str]: List of tables as markdown strings.
        """
        tables = []

        try:
            # Iterate through document items to find tables
            for item, level in doc.iterate_items():
                # Check if item is a table
                if hasattr(item, "export_to_markdown") and "Table" in str(type(item)):
                    table_md = item.export_to_markdown()
                    tables.append(table_md)
                    logger.debug(f"Extracted table: {len(table_md)} chars")

        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")

        logger.info(f"Extracted {len(tables)} tables")
        return tables

    def _extract_images(
        self, doc, file_path: Path, options: Optional[Dict[str, Any]] = None
    ) -> list[str]:
        """
        Extract images from Docling document (Feature #21).

        Args:
            doc: Docling document object.
            file_path: Original PDF file path.
            options: Extraction options.

        Returns:
            list[str]: List of image references/paths.
        """
        images = []

        try:
            # Check if image extraction is enabled
            extract_images = options.get("extract_images", False) if options else False

            if extract_images:
                # Iterate through document to find images
                for item, level in doc.iterate_items():
                    # Check if item is a picture/image
                    if hasattr(item, "image") or "Picture" in str(type(item)):
                        # For now, just track that an image was found
                        # Full extraction to file will be in future enhancement
                        image_ref = f"image_{len(images)}"
                        images.append(image_ref)
                        logger.debug(f"Found image: {image_ref}")

        except Exception as e:
            logger.warning(f"Image extraction failed: {e}")

        logger.info(f"Found {len(images)} images")
        return images

    def _extract_metadata(self, doc, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from Docling document (Feature #22).

        Args:
            doc: Docling document object.
            file_path: Original PDF file path.

        Returns:
            dict: Metadata dictionary with title, author, page_count, etc.
        """
        metadata = {
            "filename": file_path.name,
            "file_size": file_path.stat().st_size,
        }

        try:
            # Extract page count
            if hasattr(doc, "pages") and doc.pages:
                metadata["page_count"] = len(doc.pages)
            else:
                metadata["page_count"] = 0

            # Extract title (from document or first heading)
            if hasattr(doc, "name") and doc.name:
                metadata["title"] = doc.name
            else:
                # Try to get first heading as title
                for item, level in doc.iterate_items():
                    if hasattr(item, "text") and level == 0:
                        metadata["title"] = item.text
                        break

            # Extract other metadata if available
            if hasattr(doc, "metadata"):
                doc_meta = doc.metadata
                if hasattr(doc_meta, "author"):
                    metadata["author"] = doc_meta.author
                if hasattr(doc_meta, "creation_date"):
                    metadata["creation_date"] = str(doc_meta.creation_date)

            logger.debug(f"Extracted metadata: {metadata}")

        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")

        return metadata
