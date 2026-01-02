"""
Mistral OCR PDF Extractor (Features #121-123).

API-based extractor using Mistral's vision models for OCR.
"""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from src.extractors.base import BaseExtractor, ExtractionResult, ExtractionError


class MistralExtractor(BaseExtractor):
    """
    Mistral OCR API extractor (Features #121-123).

    Uses Mistral's vision models (Pixtral) for PDF OCR.
    Serves as fallback when local extractors fail (Feature #123).

    Example:
        >>> extractor = MistralExtractor()
        >>> if extractor.is_available():
        ...     result = extractor.extract(Path("document.pdf"))
    """

    name: str = "MistralExtractor"
    version: str = "1.0.0"
    description: str = "API-based extractor using Mistral vision models"

    def __init__(self):
        """Initialize Mistral extractor (Feature #121)."""
        self._api_key = None
        self._client = None
        self._check_availability()

    def _check_availability(self) -> None:
        """
        Check if Mistral API is available (Feature #122).

        Loads API key from environment and validates.
        """
        # Feature #122: Load API key from environment
        self._api_key = os.getenv("MISTRAL_API_KEY")

        if not self._api_key:
            logger.warning(
                f"{self.name} not available: MISTRAL_API_KEY not set. "
                "Set environment variable to enable Mistral extraction."
            )
            return

        try:
            # Try to import Mistral client (new API 1.0+)
            from mistralai import Mistral

            self._client = Mistral(api_key=self._api_key)
            logger.info(f"{self.name} initialized with API key")

        except ImportError as e:
            logger.warning(
                f"{self.name} not available: mistralai package not installed. "
                f"Install with: pip install mistralai. Error: {e}"
            )
            self._client = None
        except Exception as e:
            logger.warning(f"{self.name} initialization failed: {e}")
            self._client = None

    def is_available(self) -> bool:
        """
        Check if Mistral extractor is available (Feature #121).

        Returns:
            bool: True if API key is set and client initialized.
        """
        return self._client is not None

    def extract(
        self,
        file_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> ExtractionResult:
        """
        Extract PDF using Mistral OCR API (Features #121-123).

        Args:
            file_path: Path to PDF file.
            options: Extraction options (model, etc.).

        Returns:
            ExtractionResult: Extraction result.

        Raises:
            ExtractionError: If extraction fails.

        Example:
            >>> extractor = MistralExtractor()
            >>> result = extractor.extract(Path("scan.pdf"))
        """
        if not self.is_available():
            raise ExtractionError(
                extractor=self.name,
                message="Mistral API not available. Set MISTRAL_API_KEY environment variable.",
                file_path=str(file_path),
            )

        # Validate file
        self.validate_file(file_path)

        # Parse options
        options = options or {}
        model = options.get("model", "pixtral-large-latest")  # Updated model name for Mistral API 1.0+

        logger.info(f"Starting Mistral extraction: {file_path.name} (model={model})")

        start_time = time.time()

        try:
            # Read PDF file
            pdf_bytes = file_path.read_bytes()

            # Prepare API request
            # Note: This is a simplified implementation
            # Actual Mistral OCR API usage would require specific formatting

            # Placeholder for actual Mistral API call
            # In production, would use Mistral's document API
            markdown_content = self._call_mistral_ocr(pdf_bytes, model)

            # Extract metadata
            metadata = {
                "filename": file_path.name,
                "file_size": file_path.stat().st_size,
                "model": model,
            }

            extraction_time = time.time() - start_time

            logger.info(
                f"Mistral extraction completed: {file_path.name} "
                f"({extraction_time:.2f}s, {len(markdown_content)} chars)"
            )

            return ExtractionResult(
                markdown=markdown_content,
                metadata=metadata,
                images=[],
                tables=[],
                formulas=[],
                confidence_score=0.85,  # Mistral typically medium confidence
                extraction_time=extraction_time,
                extractor_name=self.name,
                extractor_version=self.version,
                success=True,
            )

        except Exception as e:
            extraction_time = time.time() - start_time
            error_msg = f"Mistral extraction failed: {str(e)}"
            logger.error(f"{error_msg} (file: {file_path.name})")

            raise ExtractionError(
                extractor=self.name,
                message=error_msg,
                file_path=str(file_path),
                original_error=e,
            )

    def _call_mistral_ocr(self, pdf_bytes: bytes, model: str) -> str:
        """
        Call Mistral OCR API using vision model.

        Args:
            pdf_bytes: PDF file bytes.
            model: Model to use (default: pixtral-12b-2024-09-04).

        Returns:
            str: Extracted markdown.
        """
        import base64

        # Convert PDF to base64 for API
        pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')

        try:
            # Use Mistral chat API with vision model for OCR
            # Note: This uses the vision capability to "read" the PDF
            response = self._client.chat.complete(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this PDF document and format it as clean Markdown. Preserve structure, headings, tables, and lists. Be precise and complete."
                            },
                            {
                                "type": "image_url",
                                "image_url": f"data:application/pdf;base64,{pdf_b64}"
                            }
                        ]
                    }
                ]
            )

            # Extract markdown from response
            markdown = response.choices[0].message.content
            logger.info(f"Mistral API extraction successful ({len(markdown)} chars)")

            return markdown

        except Exception as e:
            logger.error(f"Mistral API call failed: {e}")
            raise ExtractionError(
                extractor=self.name,
                message=f"Mistral API call failed: {e}",
                file_path="<pdf_bytes>",  # file_path not available in this scope
                original_error=e
            )

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get Mistral extractor capabilities (Feature #121).

        Returns:
            dict: Capabilities dictionary.
        """
        return {
            "name": self.name,
            "version": self.version,
            "supports_tables": True,
            "supports_formulas": False,  # Mistral focuses on OCR
            "supports_images": True,
            "supports_ocr": True,
            "supports_complex_layouts": True,
            "precision": "medium",
            "speed": "fast",
            "requires_api_key": True,
            "cost_per_page": 0.002,  # Approximate
        }
