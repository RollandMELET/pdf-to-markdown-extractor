"""
Tests for DoclingExtractor.

Verifies PDF extraction functionality using Docling library.
"""

import pytest
from pathlib import Path

from src.extractors.docling_extractor import DoclingExtractor
from src.extractors.base import ExtractionResult


@pytest.mark.unit
@pytest.mark.extractor
@pytest.mark.requires_pdf
class TestDoclingExtractor:
    """Test suite for DoclingExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create DoclingExtractor instance."""
        return DoclingExtractor()

    def test_extractor_initialization(self, extractor):
        """Test that extractor initializes correctly."""
        assert extractor.name == "DoclingExtractor"
        assert extractor.version == "1.0.0"
        assert extractor.description is not None

    def test_is_available(self, extractor):
        """Test that Docling is available."""
        assert extractor.is_available() is True

    def test_get_capabilities(self, extractor):
        """Test get_capabilities returns expected capabilities."""
        caps = extractor.get_capabilities()

        assert isinstance(caps, dict)
        assert caps["tables"] is True
        assert caps["images"] is True
        assert caps["multi_column"] is True
        assert caps["metadata"] is True
        assert caps["ocr"] is False  # Docling doesn't do OCR directly

    def test_get_info(self, extractor):
        """Test get_info returns extractor information."""
        info = extractor.get_info()

        assert info["name"] == "DoclingExtractor"
        assert info["version"] == "1.0.0"
        assert info["available"] is True
        assert "capabilities" in info


@pytest.mark.integration
@pytest.mark.extractor
@pytest.mark.requires_pdf
@pytest.mark.slow
class TestDoclingExtractionTextOnly:
    """Test DoclingExtractor with text_only.pdf (Feature #29)."""

    @pytest.fixture
    def extractor(self):
        """Create DoclingExtractor instance."""
        return DoclingExtractor()

    @pytest.fixture
    def text_only_pdf(self, simple_pdf_path):
        """Get path to text_only.pdf."""
        return simple_pdf_path / "text_only.pdf"

    def test_extract_text_only_pdf(self, extractor, text_only_pdf):
        """Test extraction of text-only PDF."""
        # Skip if file doesn't exist
        if not text_only_pdf.exists():
            pytest.skip(f"PDF fixture not found: {text_only_pdf}")

        result = extractor.extract(text_only_pdf)

        # Verify result
        assert isinstance(result, ExtractionResult)
        assert result.success is True
        assert len(result.markdown) > 0
        assert result.extractor_name == "DoclingExtractor"
        assert result.confidence_score >= 0.9

    def test_text_only_markdown_content(self, extractor, text_only_pdf):
        """Test that extracted markdown contains expected content."""
        if not text_only_pdf.exists():
            pytest.skip(f"PDF fixture not found: {text_only_pdf}")

        result = extractor.extract(text_only_pdf)

        # Check for expected content
        markdown_lower = result.markdown.lower()
        assert "simple text document" in markdown_lower
        assert "pdf extraction" in markdown_lower

    def test_text_only_metadata(self, extractor, text_only_pdf):
        """Test metadata extraction from text_only.pdf."""
        if not text_only_pdf.exists():
            pytest.skip(f"PDF fixture not found: {text_only_pdf}")

        result = extractor.extract(text_only_pdf)

        assert "filename" in result.metadata
        assert result.metadata["filename"] == "text_only.pdf"
        assert result.page_count >= 1


@pytest.mark.integration
@pytest.mark.extractor
@pytest.mark.requires_pdf
@pytest.mark.slow
class TestDoclingExtractionSimpleTable:
    """Test DoclingExtractor with simple_table.pdf (Feature #30)."""

    @pytest.fixture
    def extractor(self):
        """Create DoclingExtractor instance."""
        return DoclingExtractor()

    @pytest.fixture
    def simple_table_pdf(self, simple_pdf_path):
        """Get path to simple_table.pdf."""
        return simple_pdf_path / "simple_table.pdf"

    def test_extract_simple_table_pdf(self, extractor, simple_table_pdf):
        """Test extraction of PDF with table."""
        if not simple_table_pdf.exists():
            pytest.skip(f"PDF fixture not found: {simple_table_pdf}")

        result = extractor.extract(simple_table_pdf)

        assert result.success is True
        assert len(result.markdown) > 0

    def test_table_detection(self, extractor, simple_table_pdf):
        """Test that table is detected and extracted."""
        if not simple_table_pdf.exists():
            pytest.skip(f"PDF fixture not found: {simple_table_pdf}")

        result = extractor.extract(simple_table_pdf)

        # Should detect at least one table
        assert result.table_count >= 1

        # Tables should contain markdown content
        if result.tables:
            assert len(result.tables[0]) > 0

    def test_table_in_markdown(self, extractor, simple_table_pdf):
        """Test that table appears in markdown output."""
        if not simple_table_pdf.exists():
            pytest.skip(f"PDF fixture not found: {simple_table_pdf}")

        result = extractor.extract(simple_table_pdf)

        # Markdown should contain table indicators
        # (either | for markdown tables or table structure)
        markdown_has_table = (
            "|" in result.markdown or "table" in result.markdown.lower()
        )
        assert markdown_has_table


@pytest.mark.integration
@pytest.mark.extractor
@pytest.mark.requires_pdf
class TestDoclingErrorCases:
    """Test DoclingExtractor error handling (Feature #31)."""

    @pytest.fixture
    def extractor(self):
        """Create DoclingExtractor instance."""
        return DoclingExtractor()

    def test_nonexistent_file(self, extractor):
        """Test extraction fails gracefully for non-existent file."""
        fake_path = Path("/app/nonexistent_file.pdf")

        with pytest.raises(FileNotFoundError):
            extractor.extract(fake_path)

    def test_non_pdf_file(self, extractor, temp_dir):
        """Test extraction fails for non-PDF file."""
        text_file = temp_dir / "test.txt"
        text_file.write_text("Not a PDF")

        with pytest.raises(ValueError, match="not a PDF"):
            extractor.extract(text_file)

    def test_empty_pdf(self, extractor, edge_case_pdf_path):
        """Test extraction of empty PDF."""
        # This test requires an actual empty.pdf fixture
        # For now, we skip if not available
        empty_pdf = edge_case_pdf_path / "empty.pdf"

        if not empty_pdf.exists():
            pytest.skip("empty.pdf fixture not available")

        result = extractor.extract(empty_pdf)

        # Empty PDF should still return a result, but may have low confidence
        assert isinstance(result, ExtractionResult)
        # May or may not be successful depending on how Docling handles empty PDFs

    def test_directory_instead_of_file(self, extractor, temp_dir):
        """Test that passing directory raises error."""
        with pytest.raises(ValueError, match="not a file"):
            extractor.extract(temp_dir)

    def test_extraction_with_none_options(self, extractor, simple_pdf_path):
        """Test that extraction works with None options."""
        pdf = simple_pdf_path / "text_only.pdf"

        if not pdf.exists():
            pytest.skip("PDF fixture not found")

        result = extractor.extract(pdf, options=None)
        assert result.success is True

    def test_extraction_with_empty_options(self, extractor, simple_pdf_path):
        """Test that extraction works with empty options dict."""
        pdf = simple_pdf_path / "text_only.pdf"

        if not pdf.exists():
            pytest.skip("PDF fixture not found")

        result = extractor.extract(pdf, options={})
        assert result.success is True
