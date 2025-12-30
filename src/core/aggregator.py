"""
PDF-to-Markdown Extractor - Extraction Result Aggregator (Feature #59).

Aggregates and analyzes results from multiple extractors.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.extractors.base import ExtractionResult


class ExtractionAggregator:
    """
    Aggregates results from parallel extractors (Feature #59).

    Collects extraction results from multiple extractors and provides
    analysis of consensus, divergences, and quality metrics.

    Example:
        >>> aggregator = ExtractionAggregator()
        >>> results = {'docling': result1, 'mineru': result2}
        >>> summary = aggregator.aggregate(results)
        >>> print(summary['consensus_available'])
        True
    """

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize aggregator.

        Args:
            similarity_threshold: Threshold for considering results similar (0.0-1.0).
                                 Default: 0.85 (85% similarity).
        """
        self.similarity_threshold = similarity_threshold

    def aggregate(
        self,
        results: Dict[str, ExtractionResult],
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple extractors (Feature #59).

        Args:
            results: Dictionary of {extractor_name: ExtractionResult}.

        Returns:
            dict: Aggregated results with analysis.
                {
                    'extractor_count': int,
                    'successful_count': int,
                    'failed_count': int,
                    'extractors': dict,
                    'best_result': ExtractionResult,
                    'consensus_available': bool,
                    'average_confidence': float,
                    'total_extraction_time': float,
                }

        Example:
            >>> aggregator = ExtractionAggregator()
            >>> results = {'docling': result1, 'mineru': result2}
            >>> summary = aggregator.aggregate(results)
            >>> print(summary['successful_count'])
            2
        """
        if not results:
            logger.warning("No results to aggregate")
            return self._empty_aggregation()

        logger.info(f"Aggregating results from {len(results)} extractors")

        # Separate successful and failed results
        successful = {
            name: result
            for name, result in results.items()
            if result.success
        }

        failed = {
            name: result
            for name, result in results.items()
            if not result.success
        }

        # Calculate metrics
        extractor_count = len(results)
        successful_count = len(successful)
        failed_count = len(failed)

        # Get best result (highest confidence)
        best_result = self._get_best_result(successful) if successful else None

        # Check consensus
        consensus_available = successful_count >= 2

        # Calculate average confidence
        if successful:
            avg_confidence = sum(r.confidence_score for r in successful.values()) / len(successful)
        else:
            avg_confidence = 0.0

        # Calculate total extraction time
        total_time = sum(r.extraction_time for r in results.values())

        # Build aggregation summary
        aggregation = {
            'extractor_count': extractor_count,
            'successful_count': successful_count,
            'failed_count': failed_count,
            'extractors': {
                name: {
                    'success': result.success,
                    'confidence': result.confidence_score,
                    'extraction_time': result.extraction_time,
                    'char_count': len(result.markdown),
                }
                for name, result in results.items()
            },
            'best_result': best_result,
            'consensus_available': consensus_available,
            'average_confidence': avg_confidence,
            'total_extraction_time': total_time,
        }

        logger.info(
            f"Aggregation: {successful_count}/{extractor_count} successful, "
            f"avg_confidence={avg_confidence:.2f}, total_time={total_time:.2f}s"
        )

        return aggregation

    def _get_best_result(
        self,
        results: Dict[str, ExtractionResult],
    ) -> Optional[ExtractionResult]:
        """
        Get the best result based on confidence score.

        Args:
            results: Dictionary of successful results.

        Returns:
            ExtractionResult: Result with highest confidence, or None.
        """
        if not results:
            return None

        best_name, best_result = max(
            results.items(),
            key=lambda item: item[1].confidence_score
        )

        logger.debug(
            f"Best result: {best_name} "
            f"(confidence={best_result.confidence_score})"
        )

        return best_result

    def _empty_aggregation(self) -> Dict[str, Any]:
        """
        Return empty aggregation result.

        Returns:
            dict: Empty aggregation structure.
        """
        return {
            'extractor_count': 0,
            'successful_count': 0,
            'failed_count': 0,
            'extractors': {},
            'best_result': None,
            'consensus_available': False,
            'average_confidence': 0.0,
            'total_extraction_time': 0.0,
        }

    def get_divergences(
        self,
        results: Dict[str, ExtractionResult],
    ) -> List[Dict[str, Any]]:
        """
        Detect divergences between extraction results.

        Compares results to find significant differences that may
        require human arbitration.

        Args:
            results: Dictionary of successful results.

        Returns:
            list[dict]: List of divergences found.

        Note:
            Full divergence detection will be implemented in Phase 4.
            This is a placeholder for now.
        """
        divergences = []

        if len(results) < 2:
            return divergences

        # Simple divergence check: compare char counts
        char_counts = {name: len(r.markdown) for name, r in results.items()}
        avg_chars = sum(char_counts.values()) / len(char_counts)

        for name, count in char_counts.items():
            diff_ratio = abs(count - avg_chars) / avg_chars if avg_chars > 0 else 0

            if diff_ratio > 0.2:  # 20% difference
                divergences.append({
                    'extractor': name,
                    'metric': 'char_count',
                    'value': count,
                    'average': avg_chars,
                    'diff_ratio': diff_ratio,
                })

        if divergences:
            logger.warning(f"Detected {len(divergences)} divergences")

        return divergences
