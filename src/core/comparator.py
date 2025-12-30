"""
PDF-to-Markdown Extractor - Extraction Comparator (Features #76-82).

Compares extraction results to detect divergences and enable arbitration.
"""

import difflib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from src.extractors.base import ExtractionResult


class DivergenceType(Enum):
    """
    Types of divergences between extractions (Feature #80).

    Types:
        TEXT_MISMATCH: Text content differs
        TABLE_STRUCTURE: Table structure differs
        MISSING_BLOCK: Block present in one but not the other
        FORMULA_DIFF: Formula content differs
        IMAGE_DIFF: Image references differ
    """

    TEXT_MISMATCH = "text_mismatch"
    TABLE_STRUCTURE = "table_structure"
    MISSING_BLOCK = "missing_block"
    FORMULA_DIFF = "formula_diff"
    IMAGE_DIFF = "image_diff"


@dataclass
class Divergence:
    """
    Divergence between two extractions (Feature #81).

    Attributes:
        id: Unique divergence identifier.
        type: Type of divergence (DivergenceType).
        page: Page number where divergence occurs.
        block_id: Block identifier (paragraph, table, etc.).
        content_a: Content from extraction A.
        content_b: Content from extraction B.
        similarity: Similarity score (0.0-1.0).
        metadata: Additional context.

    Example:
        >>> div = Divergence(
        ...     id="div-1",
        ...     type=DivergenceType.TEXT_MISMATCH,
        ...     page=1,
        ...     block_id="para-3",
        ...     content_a="Text from Docling",
        ...     content_b="Text from MinerU",
        ...     similarity=0.75
        ... )
    """

    id: str
    type: DivergenceType
    page: int
    block_id: str
    content_a: str
    content_b: str
    similarity: float
    metadata: Optional[Dict[str, Any]] = None


class ExtractionComparator:
    """
    Compares extraction results (Features #76-82).

    Provides methods to compare extractions from multiple extractors,
    detect divergences, and enable human arbitration.

    Example:
        >>> comparator = ExtractionComparator(similarity_threshold=0.9)
        >>> similarity = comparator.text_similarity("text a", "text b")
        >>> divergences = comparator.compare(result_a, result_b)
    """

    def __init__(self, similarity_threshold: float = 0.9):
        """
        Initialize comparator (Feature #76, #82).

        Args:
            similarity_threshold: Threshold for flagging divergences (Feature #82).
                                 Default: 0.9 (90% similarity).
        """
        self.similarity_threshold = similarity_threshold
        logger.debug(f"ExtractionComparator initialized (threshold={similarity_threshold})")

    def text_similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculate text similarity using difflib (Feature #77).

        Args:
            text_a: First text.
            text_b: Second text.

        Returns:
            float: Similarity ratio (0.0 to 1.0).

        Example:
            >>> comparator = ExtractionComparator()
            >>> similarity = comparator.text_similarity("hello world", "hello earth")
            >>> print(f"Similarity: {similarity:.2%}")
        """
        if not text_a and not text_b:
            return 1.0

        if not text_a or not text_b:
            return 0.0

        # Use SequenceMatcher for similarity calculation
        matcher = difflib.SequenceMatcher(None, text_a, text_b)
        ratio = matcher.ratio()

        logger.debug(f"Text similarity: {ratio:.3f}")

        return ratio

    def align_blocks(
        self,
        result_a: ExtractionResult,
        result_b: ExtractionResult,
    ) -> List[Tuple[str, str, str]]:
        """
        Align semantic blocks across extractions (Feature #78).

        Aligns paragraphs, tables, images between two extraction results
        for comparison.

        Args:
            result_a: First extraction result.
            result_b: Second extraction result.

        Returns:
            list[tuple]: List of (block_id, content_a, content_b) tuples.

        Example:
            >>> comparator = ExtractionComparator()
            >>> blocks = comparator.align_blocks(result_docling, result_mineru)
            >>> for block_id, content_a, content_b in blocks:
            ...     similarity = comparator.text_similarity(content_a, content_b)
        """
        # Simple block alignment based on paragraphs
        # Split by double newlines (paragraphs)
        blocks_a = [b.strip() for b in result_a.markdown.split('\n\n') if b.strip()]
        blocks_b = [b.strip() for b in result_b.markdown.split('\n\n') if b.strip()]

        aligned = []
        max_blocks = max(len(blocks_a), len(blocks_b))

        for i in range(max_blocks):
            block_a = blocks_a[i] if i < len(blocks_a) else ""
            block_b = blocks_b[i] if i < len(blocks_b) else ""
            block_id = f"block-{i}"

            aligned.append((block_id, block_a, block_b))

        logger.debug(f"Aligned {len(aligned)} blocks")

        return aligned

    def compare_tables(
        self,
        tables_a: List[str],
        tables_b: List[str],
    ) -> List[Divergence]:
        """
        Compare tables cell by cell (Feature #79).

        Detects structural differences between tables.

        Args:
            tables_a: Tables from extraction A.
            tables_b: Tables from extraction B.

        Returns:
            list[Divergence]: List of table divergences.

        Example:
            >>> comparator = ExtractionComparator()
            >>> divergences = comparator.compare_tables(
            ...     result_a.tables,
            ...     result_b.tables
            ... )
        """
        divergences = []

        # Compare table counts
        if len(tables_a) != len(tables_b):
            divergences.append(
                Divergence(
                    id=f"table-count-diff",
                    type=DivergenceType.TABLE_STRUCTURE,
                    page=0,
                    block_id="tables",
                    content_a=f"{len(tables_a)} tables",
                    content_b=f"{len(tables_b)} tables",
                    similarity=0.0,
                    metadata={'reason': 'table_count_mismatch'},
                )
            )

        # Compare individual tables
        for i in range(min(len(tables_a), len(tables_b))):
            similarity = self.text_similarity(tables_a[i], tables_b[i])

            if similarity < self.similarity_threshold:
                divergences.append(
                    Divergence(
                        id=f"table-{i}-diff",
                        type=DivergenceType.TABLE_STRUCTURE,
                        page=0,
                        block_id=f"table-{i}",
                        content_a=tables_a[i][:200],  # First 200 chars
                        content_b=tables_b[i][:200],
                        similarity=similarity,
                    )
                )

        logger.debug(f"Found {len(divergences)} table divergences")

        return divergences

    def detect_divergences(
        self,
        result_a: ExtractionResult,
        result_b: ExtractionResult,
        extractor_a_name: str = "A",
        extractor_b_name: str = "B",
    ) -> List[Divergence]:
        """
        Detect and classify divergences (Feature #80).

        Identifies differences between two extraction results and
        classifies them by type.

        Args:
            result_a: First extraction result.
            result_b: Second extraction result.
            extractor_a_name: Name of first extractor (for logging).
            extractor_b_name: Name of second extractor (for logging).

        Returns:
            list[Divergence]: List of detected divergences.

        Example:
            >>> comparator = ExtractionComparator()
            >>> divergences = comparator.detect_divergences(
            ...     docling_result,
            ...     mineru_result,
            ...     "Docling",
            ...     "MinerU"
            ... )
        """
        logger.info(f"Detecting divergences between {extractor_a_name} and {extractor_b_name}")

        divergences = []

        # Align blocks
        aligned_blocks = self.align_blocks(result_a, result_b)

        # Compare each block
        for block_id, content_a, content_b in aligned_blocks:
            # Skip empty blocks on both sides
            if not content_a and not content_b:
                continue

            # Detect missing blocks
            if not content_a or not content_b:
                divergences.append(
                    Divergence(
                        id=f"{block_id}-missing",
                        type=DivergenceType.MISSING_BLOCK,
                        page=0,  # TODO: Determine actual page number
                        block_id=block_id,
                        content_a=content_a or "[MISSING]",
                        content_b=content_b or "[MISSING]",
                        similarity=0.0,
                    )
                )
                continue

            # Calculate similarity
            similarity = self.text_similarity(content_a, content_b)

            # Flag if below threshold
            if similarity < self.similarity_threshold:
                divergences.append(
                    Divergence(
                        id=f"{block_id}-mismatch",
                        type=DivergenceType.TEXT_MISMATCH,
                        page=0,
                        block_id=block_id,
                        content_a=content_a[:200],  # First 200 chars
                        content_b=content_b[:200],
                        similarity=similarity,
                    )
                )

        # Compare tables
        table_divergences = self.compare_tables(result_a.tables, result_b.tables)
        divergences.extend(table_divergences)

        logger.info(f"Detected {len(divergences)} divergences")

        return divergences

    def should_auto_merge(self, similarity: float) -> bool:
        """
        Check if blocks can be auto-merged (Feature #83).

        Blocks with >95% similarity are merged automatically without flagging.

        Args:
            similarity: Similarity score (0.0-1.0).

        Returns:
            bool: True if can auto-merge.

        Example:
            >>> comparator = ExtractionComparator()
            >>> if comparator.should_auto_merge(0.96):
            ...     print("Auto-merge approved")
        """
        # Feature #83: Auto-merge threshold
        AUTO_MERGE_THRESHOLD = 0.95

        return similarity >= AUTO_MERGE_THRESHOLD
