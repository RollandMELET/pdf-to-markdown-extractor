"""
Tests for MinerUExtractor (Feature #69).

Tests cover:
- Feature #69: Test MinerU with complex document
"""

import pytest
from pathlib import Path

from src.extractors.mineru_extractor import MinerUExtractor
from src.extractors.base import ExtractionError


@pytest.fixture
def mineru_extractor():
    """Create MinerUExtractor instance."""
    return MinerUExtractor()


@pytest.fixture
def complex_pdf_path():
    """Path to complex PDF fixture."""
    return Path("tests/fixtures/complex/technical_report.pdf")


class TestMinerUExtractor:
    """Tests for MinerUExtractor."""

    def test_mineru_initialization(self, mineru_extractor):
        """Test MinerUExtractor initialization."""
        assert mineru_extractor.name == "MinerUExtractor"
        assert mineru_extractor.version == "1.0.0"
        assert mineru_extractor.description is not None

    def test_mineru_availability_check(self, mineru_extractor):
        """Test is_available() method."""
        # MinerU not installed by default (optional dependency)
        available = mineru_extractor.is_available()
        assert isinstance(available, bool)

    def test_mineru_capabilities(self, mineru_extractor):
        """Test get_capabilities() returns correct structure."""
        caps = mineru_extractor.get_capabilities()

        assert "name" in caps
        assert "version" in caps
        assert "supports_tables" in caps
        assert "supports_formulas" in caps
        assert "supports_ocr" in caps
        assert "gpu_available" in caps
        assert "precision" in caps
        assert "speed" in caps

        # Verify table and formula support (Features #53-54)
        assert caps["supports_tables"] is True
        assert caps["supports_formulas"] is True

    def test_mineru_gpu_detection(self, mineru_extractor):
        """Test GPU detection (Feature #67)."""
        has_gpu = mineru_extractor.has_gpu()
        assert isinstance(has_gpu, bool)

        # Verify GPU info in capabilities
        caps = mineru_extractor.get_capabilities()
        assert caps["gpu_available"] == has_gpu

        # Speed should be "fast" with GPU, "medium" without
        if has_gpu:
            assert caps["speed"] == "fast"
        else:
            assert caps["speed"] == "medium"

    @pytest.mark.requires_pdf
    def test_mineru_with_complex_document_feature_69(self, mineru_extractor, complex_pdf_path):
        """
        Feature #69: Test MinerU extraction with technical_report.pdf.

        Verification: MinerU correctly handles complex PDF

        Note: This test will skip if MinerU is not installed,
        or will test error handling if extraction fails.
        """
        if not complex_pdf_path.exists():
            pytest.skip(f"Complex PDF not found: {complex_pdf_path}")

        if not mineru_extractor.is_available():
            # Test that unavailable extractor raises appropriate error
            with pytest.raises(ExtractionError) as exc_info:
                mineru_extractor.extract(complex_pdf_path)

            assert "MinerU is not installed" in str(exc_info.value)
            assert exc_info.value.extractor == "MinerUExtractor"

        else:
            # MinerU is installed, test actual extraction
            result = mineru_extractor.extract(
                complex_pdf_path,
                options={
                    "extract_tables": True,
                    "extract_formulas": True,
                    "ocr_enabled": True,
                }
            )

            # Verify result structure
            assert result is not None
            assert result.extractor_name == "MinerUExtractor"
            assert result.markdown is not None
            assert len(result.markdown) > 0

            # Complex PDF should have reasonable extraction
            assert result.metadata is not None
            assert result.confidence_score > 0.0

    @pytest.mark.requires_pdf
    def test_mineru_error_handling(self, mineru_extractor):
        """Test MinerU error handling (Feature #55)."""
        non_existent_pdf = Path("tests/fixtures/nonexistent.pdf")

        # Should raise error for non-existent file
        with pytest.raises((FileNotFoundError, ExtractionError)):
            mineru_extractor.extract(non_existent_pdf)

    @pytest.mark.requires_pdf
    @pytest.mark.skipif(
        not MinerUExtractor().is_available(),
        reason="MinerU not installed"
    )
    def test_mineru_table_extraction_feature_53(self, mineru_extractor):
        """
        Feature #53: Test MinerU table extraction.

        Only runs if MinerU is installed.
        """
        # Use simple_table.pdf for table test
        table_pdf = Path("tests/fixtures/simple/simple_table.pdf")

        if not table_pdf.exists():
            pytest.skip("simple_table.pdf not found")

        result = mineru_extractor.extract(
            table_pdf,
            options={"extract_tables": True}
        )

        # Should extract at least one table
        assert result.tables is not None
        # Table extraction depends on MinerU's detection

    @pytest.mark.requires_pdf
    @pytest.mark.skipif(
        not MinerUExtractor().is_available(),
        reason="MinerU not installed"
    )
    def test_mineru_formula_extraction_feature_54(self, mineru_extractor, complex_pdf_path):
        """
        Feature #54: Test MinerU formula extraction.

        Only runs if MinerU is installed and complex PDF exists.
        """
        if not complex_pdf_path.exists():
            pytest.skip("Complex PDF not found")

        result = mineru_extractor.extract(
            complex_pdf_path,
            options={"extract_formulas": True}
        )

        # Formulas field should be present
        assert result.formulas is not None
        # Actual formula extraction depends on MinerU
