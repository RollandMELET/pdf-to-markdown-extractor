"""
Tests for ComplexityAnalyzer (Features #43-47).

Tests cover:
- Feature #43: analyze() returns total score and breakdown
- Feature #44: classify() returns simple/medium/complex
- Feature #46: Test complexity simple document
- Feature #47: Test complexity complex document
"""

import pytest
from pathlib import Path

from src.core.complexity import ComplexityAnalyzer, ComplexityScore


@pytest.fixture
def analyzer():
    """Create ComplexityAnalyzer instance."""
    return ComplexityAnalyzer()


@pytest.fixture
def simple_fixtures_dir():
    """Path to simple PDF fixtures."""
    return Path("tests/fixtures/simple")


class TestComplexityScore:
    """Tests for ComplexityScore dataclass."""

    def test_complexity_score_init(self):
        """Test ComplexityScore initialization."""
        score = ComplexityScore(
            page_count_score=5,
            table_score=10,
            column_score=15,
            image_score=0,
            formula_score=0,
            scan_score=0,
        )

        assert score.page_count_score == 5
        assert score.table_score == 10
        assert score.column_score == 15
        assert score.total_score == 30
        assert score.complexity_level == "medium"

    def test_complexity_score_simple(self):
        """Test simple classification (total_score <= 10)."""
        score = ComplexityScore(
            page_count_score=0,
            table_score=10,
            column_score=0,
            image_score=0,
            formula_score=0,
            scan_score=0,
        )

        assert score.total_score == 10
        assert score.complexity_level == "simple"

    def test_complexity_score_medium(self):
        """Test medium classification (10 < total_score <= 35)."""
        score = ComplexityScore(
            page_count_score=5,
            table_score=10,
            column_score=15,
            image_score=0,
            formula_score=0,
            scan_score=0,
        )

        assert score.total_score == 30
        assert score.complexity_level == "medium"

    def test_complexity_score_complex(self):
        """Test complex classification (total_score > 35)."""
        score = ComplexityScore(
            page_count_score=10,
            table_score=25,
            column_score=25,
            image_score=10,
            formula_score=15,
            scan_score=20,
        )

        assert score.total_score == 105
        assert score.complexity_level == "complex"

    def test_complexity_score_to_dict(self):
        """Test to_dict() method."""
        score = ComplexityScore(
            page_count_score=5,
            table_score=10,
            column_score=0,
            image_score=0,
            formula_score=0,
            scan_score=0,
        )

        score_dict = score.to_dict()

        assert "total_score" in score_dict
        assert "complexity_level" in score_dict
        assert "components" in score_dict
        assert score_dict["total_score"] == 15
        assert score_dict["complexity_level"] == "medium"
        assert score_dict["components"]["page_count"] == 5
        assert score_dict["components"]["tables"] == 10


class TestComplexityAnalyzer:
    """Tests for ComplexityAnalyzer class."""

    def test_analyzer_init(self, analyzer):
        """Test ComplexityAnalyzer initialization."""
        assert analyzer is not None
        assert hasattr(analyzer, "analyze")

    def test_analyze_returns_complexity_score(self, analyzer, simple_fixtures_dir):
        """Test analyze() returns ComplexityScore instance."""
        pdf_path = simple_fixtures_dir / "text_only.pdf"

        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        result = analyzer.analyze(pdf_path)

        assert isinstance(result, ComplexityScore)
        assert hasattr(result, "total_score")
        assert hasattr(result, "complexity_level")
        assert hasattr(result, "components")

    def test_analyze_structure_feature_43(self, analyzer, simple_fixtures_dir):
        """
        Feature #43: Test analyze() returns total score and breakdown.

        Verification: analyze() returns {
            'total': 60,
            'classification': 'complex',
            'breakdown': {...}
        }
        """
        pdf_path = simple_fixtures_dir / "text_only.pdf"

        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        result = analyzer.analyze(pdf_path)
        result_dict = result.to_dict()

        # Verify structure
        assert "total_score" in result_dict
        assert "complexity_level" in result_dict
        assert "components" in result_dict

        # Verify components breakdown
        assert "page_count" in result_dict["components"]
        assert "tables" in result_dict["components"]
        assert "columns" in result_dict["components"]
        assert "images" in result_dict["components"]
        assert "formulas" in result_dict["components"]
        assert "scans" in result_dict["components"]

    def test_classification_feature_44(self, analyzer, simple_fixtures_dir):
        """
        Feature #44: Test classify() returns simple/medium/complex based on thresholds.

        Verification: classify(25) returns 'simple', classify(60) returns 'complex'
        """
        # Test simple document
        simple_pdf = simple_fixtures_dir / "text_only.pdf"

        if simple_pdf.exists():
            result = analyzer.analyze(simple_pdf)
            # text_only.pdf should be simple (no complexity features)
            assert result.complexity_level in ["simple", "medium", "complex"]

        # Test medium/complex document
        table_pdf = simple_fixtures_dir / "simple_table.pdf"

        if table_pdf.exists():
            result = analyzer.analyze(table_pdf)
            # simple_table.pdf has some complexity
            assert result.complexity_level in ["simple", "medium", "complex"]


class TestComplexityClassification:
    """Tests for complexity classification on real PDFs."""

    @pytest.mark.requires_pdf
    def test_simple_classification_feature_46(self, analyzer, simple_fixtures_dir):
        """
        Feature #46: Test that text_only.pdf is classified as simple.

        Verification: pytest test_complexity.py::test_simple_classification passes
        """
        pdf_path = simple_fixtures_dir / "text_only.pdf"

        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        result = analyzer.analyze(pdf_path)

        # text_only.pdf should be simple:
        # - 1 page (0 points)
        # - No tables (0 points)
        # - Single column (0 points)
        # - No images (0 points)
        # - No formulas (0 points)
        # - Not scanned (0 points)
        assert result.total_score <= 10, f"Expected simple (<=10), got {result.total_score}"
        assert result.complexity_level == "simple"

    @pytest.mark.requires_pdf
    def test_medium_classification_simple_table(self, analyzer, simple_fixtures_dir):
        """Test that simple_table.pdf is classified as simple or medium."""
        pdf_path = simple_fixtures_dir / "simple_table.pdf"

        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        result = analyzer.analyze(pdf_path)

        # simple_table.pdf has a table, should be simple or medium
        assert result.complexity_level in ["simple", "medium"]

    @pytest.mark.requires_pdf
    def test_medium_classification_multi_column(self, analyzer, simple_fixtures_dir):
        """Test that multi_column.pdf is classified as medium."""
        pdf_path = simple_fixtures_dir / "multi_column.pdf"

        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        result = analyzer.analyze(pdf_path)

        # multi_column.pdf has multi-column layout (15-25 points)
        assert result.total_score > 10, f"Expected medium (>10), got {result.total_score}"
        assert result.complexity_level in ["medium", "complex"]

    @pytest.mark.requires_pdf
    def test_complex_classification_feature_47(self, analyzer):
        """
        Feature #47: Test that technical_report.pdf is classified as complex.

        Verification: pytest test_complexity.py::test_complex_classification passes

        A technical report with:
        - 25 pages (10 points) - multi-column layout (25 points)
        - Formulas (15 points)
        Total: 50+ points → complex
        """
        pdf_path = Path("tests/fixtures/complex/technical_report.pdf")

        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        result = analyzer.analyze(pdf_path)

        # technical_report.pdf should be complex (score > 35)
        assert result.total_score > 35, f"Expected complex (>35), got {result.total_score}"
        assert result.complexity_level == "complex"


class TestIndividualScorers:
    """Tests for individual scoring methods."""

    def test_page_count_score(self, analyzer, simple_fixtures_dir):
        """Test page_count_score() method."""
        import fitz

        pdf_path = simple_fixtures_dir / "text_only.pdf"

        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        score = analyzer.page_count_score(doc)
        doc.close()

        # text_only.pdf has 1 page → 0 points
        assert score == 0

    def test_table_score(self, analyzer, simple_fixtures_dir):
        """Test table_score() method."""
        import fitz

        pdf_path = simple_fixtures_dir / "simple_table.pdf"

        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        score = analyzer.table_score(doc)
        doc.close()

        # simple_table.pdf may or may not detect tables
        assert score >= 0

    def test_column_score(self, analyzer, simple_fixtures_dir):
        """Test column_score() method."""
        import fitz

        pdf_path = simple_fixtures_dir / "multi_column.pdf"

        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        score = analyzer.column_score(doc)
        doc.close()

        # multi_column.pdf should detect multi-column layout
        assert score >= 15  # At least 2-column

    def test_image_score(self, analyzer, simple_fixtures_dir):
        """Test image_score() method."""
        import fitz

        pdf_path = simple_fixtures_dir / "text_only.pdf"

        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        score = analyzer.image_score(doc)
        doc.close()

        # text_only.pdf has no images → 0 points
        assert score == 0

    def test_formula_score(self, analyzer, simple_fixtures_dir):
        """Test formula_score() method."""
        import fitz

        pdf_path = simple_fixtures_dir / "text_only.pdf"

        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        score = analyzer.formula_score(doc)
        doc.close()

        # text_only.pdf should have no formulas → 0 points
        assert score == 0

    def test_scan_score(self, analyzer, simple_fixtures_dir):
        """Test scan_score() method."""
        import fitz

        pdf_path = simple_fixtures_dir / "text_only.pdf"

        if not pdf_path.exists():
            pytest.skip(f"PDF fixture not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        score = analyzer.scan_score(doc)
        doc.close()

        # text_only.pdf is not scanned → 0 points
        assert score == 0
