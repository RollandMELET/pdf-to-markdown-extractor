"""
PDF-to-Markdown Extractor - Complexity Analyzer.

Analyzes PDF complexity to determine optimal extraction strategy.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional

import fitz  # PyMuPDF
from loguru import logger

from src.utils.redis_client import get_redis_client


class ComplexityScore:
    """
    Container for complexity scoring results.

    Attributes:
        total_score: Total complexity score (sum of all component scores).
        page_count_score: Score based on page count.
        table_score: Score based on table detection.
        column_score: Score based on multi-column layout.
        image_score: Score based on image density.
        formula_score: Score based on formula detection.
        scan_score: Score based on scan detection.
        components: Dict of individual component scores.
        complexity_level: Categorized complexity (simple/medium/complex).
    """

    def __init__(
        self,
        page_count_score: int = 0,
        table_score: int = 0,
        column_score: int = 0,
        image_score: int = 0,
        formula_score: int = 0,
        scan_score: int = 0,
    ):
        """Initialize complexity score."""
        self.page_count_score = page_count_score
        self.table_score = table_score
        self.column_score = column_score
        self.image_score = image_score
        self.formula_score = formula_score
        self.scan_score = scan_score

        self.total_score = sum([
            page_count_score,
            table_score,
            column_score,
            image_score,
            formula_score,
            scan_score,
        ])

        self.components = {
            "page_count": page_count_score,
            "tables": table_score,
            "columns": column_score,
            "images": image_score,
            "formulas": formula_score,
            "scans": scan_score,
        }

        # Categorize complexity level
        if self.total_score <= 10:
            self.complexity_level = "simple"
        elif self.total_score <= 35:
            self.complexity_level = "medium"
        else:
            self.complexity_level = "complex"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_score": self.total_score,
            "complexity_level": self.complexity_level,
            "components": self.components,
        }


class ComplexityAnalyzer:
    """
    Analyzes PDF complexity to determine extraction strategy.

    Uses multiple heuristics to score document complexity:
    - Page count
    - Table detection
    - Multi-column layouts
    - Image density
    - Formula/equation presence
    - Scan detection (OCR needed)

    Example:
        >>> analyzer = ComplexityAnalyzer()
        >>> score = analyzer.analyze(Path("document.pdf"))
        >>> print(score.complexity_level)
        medium
        >>> print(score.total_score)
        25
    """

    def __init__(self, use_cache: bool = True, cache_ttl: int = 3600):
        """
        Initialize complexity analyzer.

        Args:
            use_cache: Whether to use Redis cache for results (Feature #48).
            cache_ttl: Cache TTL in seconds (default: 1 hour).
        """
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl

        if use_cache:
            try:
                self.redis_client = get_redis_client()
            except Exception as e:
                logger.warning(f"Redis unavailable, disabling cache: {e}")
                self.use_cache = False

    def analyze(self, file_path: Path) -> ComplexityScore:
        """
        Analyze PDF complexity with Redis caching (Feature #48).

        Args:
            file_path: Path to PDF file.

        Returns:
            ComplexityScore: Complexity scoring result.

        Example:
            >>> analyzer = ComplexityAnalyzer()
            >>> score = analyzer.analyze(Path("doc.pdf"))
            >>> if score.complexity_level == "complex":
            ...     # Use parallel extraction
        """
        logger.info(f"Analyzing complexity: {file_path.name}")

        # Check cache (Feature #48)
        if self.use_cache:
            cached_score = self._get_cached_score(file_path)
            if cached_score:
                logger.info(
                    f"Complexity from cache: {file_path.name} - "
                    f"level={cached_score.complexity_level}, total={cached_score.total_score}"
                )
                return cached_score

        # Open PDF
        doc = fitz.open(file_path)

        try:
            # Calculate individual scores
            page_count_score = self.page_count_score(doc)
            table_score = self.table_score(doc)
            column_score = self.column_score(doc)
            image_score = self.image_score(doc)
            formula_score = self.formula_score(doc)
            scan_score = self.scan_score(doc)

            # Build complexity score
            score = ComplexityScore(
                page_count_score=page_count_score,
                table_score=table_score,
                column_score=column_score,
                image_score=image_score,
                formula_score=formula_score,
                scan_score=scan_score,
            )

            logger.info(
                f"Complexity analysis: {file_path.name} - "
                f"level={score.complexity_level}, total={score.total_score}"
            )

            # Store in cache (Feature #48)
            if self.use_cache:
                self._cache_score(file_path, score)

            return score

        finally:
            doc.close()

    def page_count_score(self, doc: fitz.Document) -> int:
        """
        Score based on page count (Feature #37).

        Scoring:
        - 1-5 pages: 0 points (simple)
        - 6-20 pages: 5 points (medium)
        - 21-50 pages: 10 points (complex)
        - 51+ pages: 15 points (very complex)

        Args:
            doc: PyMuPDF document.

        Returns:
            int: Page count score.
        """
        page_count = len(doc)

        if page_count <= 5:
            return 0
        elif page_count <= 20:
            return 5
        elif page_count <= 50:
            return 10
        else:
            return 15

    def table_score(self, doc: fitz.Document) -> int:
        """
        Score based on table detection (Feature #38).

        Uses layout analysis to detect tables.

        Scoring:
        - 0 tables: 0 points
        - 1-3 tables: 10 points
        - 4+ tables: 25 points

        Args:
            doc: PyMuPDF document.

        Returns:
            int: Table score.
        """
        table_count = 0

        # Sample first 10 pages for table detection
        sample_pages = min(10, len(doc))

        for page_num in range(sample_pages):
            page = doc[page_num]

            # Use layout analysis to detect tables
            # Look for grid-like structures (multiple horizontal/vertical lines)
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                # Simple heuristic: check for table-like structures
                # (This is a simplified approach - more sophisticated in future)
                if "lines" in block and len(block.get("lines", [])) > 3:
                    # Multiple lines suggest potential table
                    table_count += 1

        # Average over sampled pages
        avg_tables = table_count / sample_pages if sample_pages > 0 else 0

        # Scale to full document
        total_tables = int(avg_tables * len(doc))

        if total_tables == 0:
            return 0
        elif total_tables <= 3:
            return 10
        else:
            return 25

    def column_score(self, doc: fitz.Document) -> int:
        """
        Score based on multi-column detection (Feature #39).

        Detects if document uses multi-column layout.

        Scoring:
        - Single column: 0 points
        - 2 columns: 15 points
        - 3+ columns: 25 points

        Args:
            doc: PyMuPDF document.

        Returns:
            int: Column score.
        """
        # Sample first 5 pages
        sample_pages = min(5, len(doc))
        multi_column_pages = 0

        for page_num in range(sample_pages):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            # Group blocks by x-coordinate to detect columns
            x_positions = []
            for block in blocks:
                if "bbox" in block:
                    x = block["bbox"][0]  # Left x-coordinate
                    x_positions.append(x)

            # Simple heuristic: if we have blocks at significantly different x positions,
            # it suggests multi-column layout
            if len(x_positions) >= 2:
                x_positions.sort()
                # Check for gaps that suggest column boundaries
                gaps = [x_positions[i+1] - x_positions[i] for i in range(len(x_positions)-1)]
                large_gaps = [g for g in gaps if g > 100]  # Significant gap (100+ points)

                if len(large_gaps) >= 1:
                    multi_column_pages += 1

        # If majority of sampled pages are multi-column
        if multi_column_pages >= sample_pages * 0.5:
            return 25  # Assume 3+ columns (complex)
        elif multi_column_pages > 0:
            return 15  # Assume 2 columns
        else:
            return 0  # Single column

    def image_score(self, doc: fitz.Document) -> int:
        """
        Score based on image density (Feature #40).

        Scoring:
        - < 0.1 images/page: 0 points
        - 0.1-0.5 images/page: 10 points
        - 0.5-1.0 images/page: 20 points
        - > 1.0 images/page: 30 points

        Args:
            doc: PyMuPDF document.

        Returns:
            int: Image score.
        """
        total_images = 0
        page_count = len(doc)

        # Count images across all pages
        for page in doc:
            image_list = page.get_images()
            total_images += len(image_list)

        # Calculate images per page
        images_per_page = total_images / page_count if page_count > 0 else 0

        if images_per_page < 0.1:
            return 0
        elif images_per_page < 0.5:
            return 10
        elif images_per_page < 1.0:
            return 20
        else:
            return 30

    def formula_score(self, doc: fitz.Document) -> int:
        """
        Score based on formula/equation detection (Feature #41).

        Detects LaTeX-like patterns or MathML.

        Scoring:
        - No formulas detected: 0 points
        - 1-5 formulas: 15 points
        - 6+ formulas: 30 points

        Args:
            doc: PyMuPDF document.

        Returns:
            int: Formula score.
        """
        formula_count = 0

        # Sample first 10 pages
        sample_pages = min(10, len(doc))

        # Patterns that suggest mathematical formulas
        math_patterns = [
            r'\$[^$]+\$',  # LaTeX inline math
            r'\\\[.+?\\\]',  # LaTeX display math
            r'\\begin\{equation\}',  # LaTeX equation environment
            r'∑|∫|∏|√|∞|≤|≥|≠|≈|±',  # Mathematical symbols
            r'\^[0-9]|\_{[0-9]}',  # Superscripts/subscripts
        ]

        for page_num in range(sample_pages):
            page = doc[page_num]
            text = page.get_text()

            # Check for math patterns
            for pattern in math_patterns:
                matches = re.findall(pattern, text)
                formula_count += len(matches)

        # Estimate for full document
        total_formulas = int(formula_count * len(doc) / sample_pages) if sample_pages > 0 else 0

        if total_formulas == 0:
            return 0
        elif total_formulas <= 5:
            return 15
        else:
            return 30

    def scan_score(self, doc: fitz.Document) -> int:
        """
        Score based on scan detection (Feature #42).

        Detects if document is scanned (low text extractability).

        Scoring:
        - Not scanned (high text ratio): 0 points
        - Partially scanned: 20 points
        - Fully scanned (OCR needed): 40 points

        Args:
            doc: PyMuPDF document.

        Returns:
            int: Scan score.
        """
        # Sample first 5 pages
        sample_pages = min(5, len(doc))
        low_text_pages = 0

        for page_num in range(sample_pages):
            page = doc[page_num]

            # Get text and image count
            text = page.get_text().strip()
            images = page.get_images()

            # Heuristic: if page has images but very little text, likely scanned
            if len(images) > 0 and len(text) < 100:
                low_text_pages += 1

        # Calculate scan ratio
        scan_ratio = low_text_pages / sample_pages if sample_pages > 0 else 0

        if scan_ratio == 0:
            return 0  # Not scanned
        elif scan_ratio < 0.5:
            return 20  # Partially scanned
        else:
            return 40  # Fully scanned (OCR needed)

    def _get_cache_key(self, file_path: Path) -> str:
        """
        Generate cache key for PDF file (Feature #48).

        Uses file hash to ensure cache invalidation when file changes.

        Args:
            file_path: Path to PDF file.

        Returns:
            str: Redis cache key.
        """
        # Calculate file hash for cache key
        file_hash = hashlib.md5(file_path.read_bytes()).hexdigest()
        return f"complexity:{file_hash}"

    def _get_cached_score(self, file_path: Path) -> Optional[ComplexityScore]:
        """
        Get complexity score from Redis cache (Feature #48).

        Args:
            file_path: Path to PDF file.

        Returns:
            ComplexityScore: Cached score or None if not found.
        """
        try:
            cache_key = self._get_cache_key(file_path)
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                # Deserialize from JSON
                data = json.loads(cached_data)
                return ComplexityScore(
                    page_count_score=data["page_count"],
                    table_score=data["tables"],
                    column_score=data["columns"],
                    image_score=data["images"],
                    formula_score=data["formulas"],
                    scan_score=data["scans"],
                )

        except Exception as e:
            logger.warning(f"Failed to get cached complexity score: {e}")

        return None

    def _cache_score(self, file_path: Path, score: ComplexityScore) -> None:
        """
        Store complexity score in Redis cache (Feature #48).

        Args:
            file_path: Path to PDF file.
            score: ComplexityScore to cache.
        """
        try:
            cache_key = self._get_cache_key(file_path)

            # Serialize to JSON
            data = json.dumps(score.components)

            # Store with TTL
            self.redis_client.set(cache_key, data, ex=self.cache_ttl)

            logger.debug(f"Cached complexity score: {cache_key} (TTL: {self.cache_ttl}s)")

        except Exception as e:
            logger.warning(f"Failed to cache complexity score: {e}")
