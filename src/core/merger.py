"""
PDF-to-Markdown Extractor - Result Merger (Features #84-87).

Merges extraction results using various strategies.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger

from src.core.comparator import Divergence, ExtractionComparator
from src.extractors.base import ExtractionResult


class MergeStrategy(Enum):
    """
    Merge strategies (Feature #85).

    Strategies:
        PREFER_DOCLING: Always prefer Docling results
        PREFER_MINERU: Always prefer MinerU results
        HIGHEST_CONFIDENCE: Select based on confidence scores
        BEST_PER_BLOCK: Select best block from each extractor
    """

    PREFER_DOCLING = "prefer_docling"
    PREFER_MINERU = "prefer_mineru"
    HIGHEST_CONFIDENCE = "highest_confidence"
    BEST_PER_BLOCK = "best_per_block"


class ExtractionMerger:
    """
    Merges extraction results (Features #84-87).

    Combines results from multiple extractors using configurable strategies.

    Example:
        >>> merger = ExtractionMerger(strategy=MergeStrategy.HIGHEST_CONFIDENCE)
        >>> merged = merger.merge(results_dict)
        >>> print(merged.markdown)
    """

    def __init__(
        self,
        strategy: MergeStrategy = MergeStrategy.HIGHEST_CONFIDENCE,
        comparator: Optional[ExtractionComparator] = None,
    ):
        """
        Initialize merger.

        Args:
            strategy: Merge strategy to use (Feature #85).
            comparator: ExtractionComparator instance (optional).
        """
        self.strategy = strategy
        self.comparator = comparator or ExtractionComparator()
        logger.debug(f"ExtractionMerger initialized (strategy={strategy.value})")

    def select_best_extraction(
        self,
        results: Dict[str, ExtractionResult],
    ) -> ExtractionResult:
        """
        Select best extraction result (Feature #84).

        When extractions differ, selects one based on confidence scores
        or configured strategy.

        Args:
            results: Dictionary of {extractor_name: ExtractionResult}.

        Returns:
            ExtractionResult: Best extraction result.

        Example:
            >>> merger = ExtractionMerger()
            >>> best = merger.select_best_extraction({
            ...     'docling': result1,
            ...     'mineru': result2
            ... })
        """
        if not results:
            logger.warning("No results to select from")
            return None

        # Filter successful results
        successful = {
            name: result
            for name, result in results.items()
            if result.success
        }

        if not successful:
            logger.error("No successful results to select from")
            return None

        # Apply strategy (Feature #85)
        if self.strategy == MergeStrategy.PREFER_DOCLING:
            if "docling" in successful:
                logger.info("Selected Docling (strategy: prefer_docling)")
                return successful["docling"]

        elif self.strategy == MergeStrategy.PREFER_MINERU:
            if "mineru" in successful:
                logger.info("Selected MinerU (strategy: prefer_mineru)")
                return successful["mineru"]

        # Default: HIGHEST_CONFIDENCE (Feature #84)
        best_name, best_result = max(
            successful.items(),
            key=lambda item: item[1].confidence_score
        )

        logger.info(
            f"Selected {best_name} (confidence={best_result.confidence_score}, "
            f"strategy={self.strategy.value})"
        )

        return best_result

    def merge_documents(
        self,
        results: Dict[str, ExtractionResult],
        divergences: Optional[List[Divergence]] = None,
    ) -> str:
        """
        Generate merged markdown document (Feature #86).

        Merges best blocks from each extraction to create final document.

        Args:
            results: Dictionary of extraction results.
            divergences: Optional list of divergences to consider.

        Returns:
            str: Merged markdown document.

        Example:
            >>> merger = ExtractionMerger()
            >>> merged_markdown = merger.merge_documents({
            ...     'docling': result1,
            ...     'mineru': result2
            ... })
        """
        if not results:
            logger.warning("No results to merge")
            return ""

        # If only one result, return it
        if len(results) == 1:
            result = list(results.values())[0]
            return result.markdown

        # For multiple results, use strategy
        best_result = self.select_best_extraction(results)

        if best_result:
            logger.info(
                f"Using {best_result.extractor_name} as base for merged document "
                f"(strategy={self.strategy.value})"
            )
            return best_result.markdown

        return ""

    def check_needs_review(
        self,
        divergences: List[Divergence],
        threshold: int = 5,
    ) -> bool:
        """
        Check if divergences require human review (Feature #87).

        Sets job status to needs_review when divergences exceed threshold.

        Args:
            divergences: List of detected divergences.
            threshold: Maximum divergences before requiring review (default: 5).

        Returns:
            bool: True if needs human review.

        Example:
            >>> merger = ExtractionMerger()
            >>> if merger.check_needs_review(divergences):
            ...     print("Human arbitration required")
        """
        needs_review = len(divergences) > threshold

        if needs_review:
            logger.warning(
                f"Human review needed: {len(divergences)} divergences "
                f"(threshold: {threshold})"
            )
        else:
            logger.info(
                f"No review needed: {len(divergences)} divergences "
                f"(threshold: {threshold})"
            )

        return needs_review
