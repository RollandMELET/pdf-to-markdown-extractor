"""
Tests for parallel extraction (Features #62-63).

Tests cover:
- Feature #62: Test parallel extraction returns results from both extractors
- Feature #63: Test extractor fallback when one fails
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.parallel_executor import ParallelExecutor
from src.core.aggregator import ExtractionAggregator
from src.core.orchestrator import Orchestrator
from src.extractors.base import ExtractionResult, ExtractionError


@pytest.fixture
def pdf_path():
    """Get test PDF path."""
    return Path("tests/fixtures/simple/text_only.pdf")


@pytest.fixture
def mock_docling_result():
    """Create mock Docling extraction result."""
    return ExtractionResult(
        markdown="# Document\n\nContent from Docling",
        metadata={"extractor": "docling"},
        images=[],
        tables=[],
        formulas=[],
        confidence_score=0.95,
        extraction_time=1.5,
        extractor_name="DoclingExtractor",
        extractor_version="1.0.0",
        success=True,
    )


@pytest.fixture
def mock_mineru_result():
    """Create mock MinerU extraction result."""
    return ExtractionResult(
        markdown="# Document\n\nContent from MinerU",
        metadata={"extractor": "mineru"},
        images=[],
        tables=[],
        formulas=[],
        confidence_score=0.90,
        extraction_time=2.0,
        extractor_name="MinerUExtractor",
        extractor_version="1.0.0",
        success=True,
    )


class TestParallelExecution:
    """Tests for parallel extraction executor."""

    def test_parallel_executor_init(self):
        """Test ParallelExecutor initialization."""
        executor = ParallelExecutor(max_workers=3, timeout=600)

        assert executor.max_workers == 3
        assert executor.timeout == 600

    @pytest.mark.requires_pdf
    def test_parallel_extraction_feature_62(self, pdf_path, mock_docling_result, mock_mineru_result):
        """
        Feature #62: Test parallel extraction returns results from both extractors.

        Verification: extract_parallel(['docling', 'mineru'], pdf) returns both results
        """
        # Mock extractors
        mock_docling = Mock()
        mock_docling.name = "DoclingExtractor"
        mock_docling.extract.return_value = mock_docling_result

        mock_mineru = Mock()
        mock_mineru.name = "MinerUExtractor"
        mock_mineru.extract.return_value = mock_mineru_result

        # Create executor and run
        executor = ParallelExecutor(max_workers=2)
        results = executor.execute([mock_docling, mock_mineru], pdf_path)

        # Verify both extractors returned results
        assert len(results) == 2
        assert "docling" in results
        assert "mineru" in results

        # Verify results are correct
        assert results["docling"].success
        assert results["mineru"].success
        assert results["docling"].confidence_score == 0.95
        assert results["mineru"].confidence_score == 0.90

    @pytest.mark.requires_pdf
    def test_extractor_fallback_feature_63(self, pdf_path, mock_docling_result):
        """
        Feature #63: Test that if one extractor fails, other results are still used.

        Verification: pytest test_extractors.py::test_extractor_fallback passes
        """
        # Mock extractors: one succeeds, one fails
        mock_docling = Mock()
        mock_docling.name = "DoclingExtractor"
        mock_docling.extract.return_value = mock_docling_result

        mock_mineru = Mock()
        mock_mineru.name = "MinerUExtractor"
        mock_mineru.extract.side_effect = ExtractionError(
            extractor="MinerUExtractor",
            message="MinerU not installed",
            file_path=str(pdf_path),
        )

        # Create executor and run
        executor = ParallelExecutor(max_workers=2)
        results = executor.execute([mock_docling, mock_mineru], pdf_path)

        # Verify only successful extractor returned result
        assert len(results) == 1
        assert "docling" in results
        assert "mineru" not in results

        # Verify successful result is correct
        assert results["docling"].success
        assert results["docling"].confidence_score == 0.95


class TestExtractionAggregator:
    """Tests for extraction aggregator."""

    def test_aggregator_init(self):
        """Test ExtractionAggregator initialization."""
        aggregator = ExtractionAggregator(similarity_threshold=0.85)

        assert aggregator.similarity_threshold == 0.85

    def test_aggregate_with_results(self, mock_docling_result, mock_mineru_result):
        """Test aggregate() with multiple results."""
        aggregator = ExtractionAggregator()

        results = {
            "docling": mock_docling_result,
            "mineru": mock_mineru_result,
        }

        aggregation = aggregator.aggregate(results)

        # Verify structure
        assert "extractor_count" in aggregation
        assert "successful_count" in aggregation
        assert "failed_count" in aggregation
        assert "best_result" in aggregation
        assert "consensus_available" in aggregation

        # Verify counts
        assert aggregation["extractor_count"] == 2
        assert aggregation["successful_count"] == 2
        assert aggregation["failed_count"] == 0
        assert aggregation["consensus_available"] is True

        # Verify best result (highest confidence = Docling 0.95)
        assert aggregation["best_result"].confidence_score == 0.95

    def test_aggregate_empty_results(self):
        """Test aggregate() with no results."""
        aggregator = ExtractionAggregator()

        aggregation = aggregator.aggregate({})

        assert aggregation["extractor_count"] == 0
        assert aggregation["successful_count"] == 0
        assert aggregation["best_result"] is None


class TestOrchestratorParallel:
    """Tests for orchestrator parallel extraction."""

    @pytest.mark.integration
    @pytest.mark.requires_pdf
    def test_orchestrator_with_registry(self):
        """Test orchestrator uses ExtractorRegistry."""
        orchestrator = Orchestrator()

        # Verify registry is initialized
        assert orchestrator.registry is not None
        assert orchestrator.registry.count() >= 1  # At least Docling

        # Verify can get extractors
        docling = orchestrator.get_extractor("docling")
        assert docling is not None
        assert docling.name == "DoclingExtractor"
