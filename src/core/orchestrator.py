"""
PDF-to-Markdown Extractor - Orchestrator.

Coordinates PDF extraction workflows, routes documents to appropriate
extractors based on complexity, and manages multi-extraction strategies.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from src.core.aggregator import ExtractionAggregator
from src.core.complexity import ComplexityAnalyzer, ComplexityScore
from src.core.config import settings
from src.core.parallel_executor import ParallelExecutor
from src.core.registry import ExtractorRegistry
from src.extractors.base import BaseExtractor, ExtractionResult


class Orchestrator:
    """
    Orchestrates PDF extraction workflows.

    The orchestrator is responsible for:
    - Routing documents to appropriate extractors
    - Managing single and multi-extraction strategies
    - Coordinating parallel extractions
    - Comparing results and detecting divergences

    Example:
        >>> orchestrator = Orchestrator()
        >>> result = orchestrator.extract_simple(Path("document.pdf"))
        >>> print(result.markdown)
    """

    def __init__(self):
        """Initialize orchestrator with ExtractorRegistry (Feature #56)."""
        self.registry = ExtractorRegistry()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.parallel_executor = ParallelExecutor()  # Feature #61
        self.aggregator = ExtractionAggregator()  # Feature #61
        logger.info(f"Orchestrator initialized with {self.registry.count()} extractors")

    def extract(
        self,
        file_path: Path,
        strategy: Optional[str] = None,
        force_complexity: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extract PDF with complexity-based routing (Feature #45).

        This is the main extraction method that analyzes document complexity
        and routes to appropriate extractors based on the strategy.

        Args:
            file_path: Path to PDF file.
            strategy: Extraction strategy (fallback, parallel_local, parallel_all, hybrid).
                     Defaults to settings.default_extraction_strategy.
            force_complexity: Force complexity level (simple, medium, complex).
                            Bypasses auto-detection (Feature #49).
            options: Extraction options to pass to extractors.

        Returns:
            dict: Extraction result with complexity analysis.
                {
                    "result": ExtractionResult,
                    "complexity": ComplexityScore.to_dict(),
                    "strategy_used": str,
                }

        Raises:
            FileNotFoundError: If file doesn't exist.

        Example:
            >>> orchestrator = Orchestrator()
            >>> result = orchestrator.extract(Path("doc.pdf"))
            >>> print(result["complexity"]["complexity_level"])
            medium
            >>> print(result["result"].markdown)
        """
        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        # Determine strategy
        strategy = strategy or settings.default_extraction_strategy

        # Analyze complexity (Feature #45)
        if force_complexity:
            # Feature #49: Force complexity option
            logger.info(f"Forcing complexity level: {force_complexity}")
            # Create a fake complexity score with forced level
            complexity_score = self._create_forced_complexity(force_complexity)
        else:
            # Normal complexity analysis
            logger.info(f"Analyzing document complexity: {file_path.name}")
            complexity_score = self.complexity_analyzer.analyze(file_path)
            logger.info(
                f"Complexity: {complexity_score.complexity_level} "
                f"(score: {complexity_score.total_score})"
            )

        # Route based on complexity and strategy (Feature #61)
        logger.info(f"Using extraction strategy: {strategy}")

        # Feature #61: Use parallel extraction for complex documents
        if strategy == "fallback":
            # Try extractors in order: Docling → MinerU → Mistral
            fallback_order = ["docling", "mineru", "mistral"]
            result = None
            last_error = None

            for extractor_name in fallback_order:
                if not self.registry.has_extractor(extractor_name):
                    logger.debug(f"Extractor '{extractor_name}' not available in fallback chain, skipping")
                    continue

                logger.info(f"Fallback: trying {extractor_name}...")
                try:
                    result = self.extract_simple(file_path, extractor_name=extractor_name, options=options)

                    if result.success:
                        logger.info(f"✅ Fallback successful with {extractor_name} (confidence: {result.confidence_score})")
                        break
                    else:
                        logger.warning(f"❌ {extractor_name} failed (success=False), trying next in chain")
                        last_error = f"{extractor_name} returned success=False"
                except Exception as e:
                    logger.warning(f"❌ {extractor_name} raised exception: {e}, trying next")
                    last_error = str(e)
                    continue

            # If all extractors failed, return last result or raise
            if not result or not result.success:
                logger.error(f"All extractors in fallback chain failed. Last error: {last_error}")
                # Return failed result if we have one, otherwise raise
                if result:
                    return {
                        "result": result,
                        "complexity": complexity_score.to_dict(),
                        "strategy_used": strategy,
                    }
                raise ValueError(f"All extractors in fallback chain failed: {last_error}")

            return {
                "result": result,
                "complexity": complexity_score.to_dict(),
                "strategy_used": strategy,
            }

        elif strategy == "parallel_local":
            # Parallel extraction with local extractors only (Docling + MinerU)
            extractors_to_use = []

            if self.registry.has_extractor("docling"):
                extractors_to_use.append(self.registry.get("docling"))
            if self.registry.has_extractor("mineru"):
                extractors_to_use.append(self.registry.get("mineru"))

            if len(extractors_to_use) < 2:
                logger.warning("Not enough local extractors available, using fallback")
                result = self.extract_simple(file_path, extractor_name="docling", options=options)
                return {
                    "result": result,
                    "complexity": complexity_score.to_dict(),
                    "strategy_used": "fallback",
                }

            # Run parallel extraction
            results = self.parallel_executor.execute(extractors_to_use, file_path, options)

            # Aggregate results
            aggregation = self.aggregator.aggregate(results)

            return {
                "result": aggregation["best_result"],
                "all_results": results,
                "aggregation": aggregation,
                "complexity": complexity_score.to_dict(),
                "strategy_used": strategy,
            }

        elif strategy == "parallel_all":
            # Parallel extraction with ALL extractors (Docling + MinerU + Mistral)
            extractors_to_use = []

            # Add all available extractors
            for extractor_name in ["docling", "mineru", "mistral"]:
                if self.registry.has_extractor(extractor_name):
                    extractors_to_use.append(self.registry.get(extractor_name))

            if len(extractors_to_use) < 2:
                logger.warning("Not enough extractors available for parallel_all, using fallback")
                result = self.extract_simple(file_path, extractor_name="docling", options=options)
                return {
                    "result": result,
                    "complexity": complexity_score.to_dict(),
                    "strategy_used": "fallback",
                }

            logger.info(f"Running parallel extraction with {len(extractors_to_use)} extractors: {[e.name for e in extractors_to_use]}")

            # Run parallel extraction
            results = self.parallel_executor.execute(extractors_to_use, file_path, options)

            # Aggregate results
            aggregation = self.aggregator.aggregate(results)

            return {
                "result": aggregation["best_result"],
                "all_results": results,
                "aggregation": aggregation,
                "complexity": complexity_score.to_dict(),
                "strategy_used": strategy,
            }

        else:
            # hybrid not yet implemented
            logger.warning(
                f"Strategy '{strategy}' not yet implemented, using fallback strategy"
            )
            result = self.extract_simple(file_path, extractor_name="docling", options=options)

            return {
                "result": result,
                "complexity": complexity_score.to_dict(),
                "strategy_used": "fallback",
            }

    def _create_forced_complexity(self, level: str) -> ComplexityScore:
        """
        Create a ComplexityScore with forced complexity level.

        This is used when force_complexity parameter is provided.

        Args:
            level: Forced complexity level (simple, medium, complex).

        Returns:
            ComplexityScore: Score with forced level.
        """
        # Map levels to scores that produce the desired classification
        score_map = {
            "simple": 0,    # <= 10 = simple
            "medium": 20,   # 11-35 = medium
            "complex": 50,  # > 35 = complex
        }

        total_score = score_map.get(level, 0)

        # Return ComplexityScore with all zeros except one component
        return ComplexityScore(
            page_count_score=total_score,
            table_score=0,
            column_score=0,
            image_score=0,
            formula_score=0,
            scan_score=0,
        )

    def extract_simple(
        self,
        file_path: Path,
        extractor_name: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> ExtractionResult:
        """
        Extract PDF using a single extractor (simple strategy).

        This is the simplest extraction method - uses one extractor only.
        By default, uses DoclingExtractor.

        Args:
            file_path: Path to PDF file.
            extractor_name: Name of extractor to use (default: "docling").
            options: Extraction options to pass to extractor.

        Returns:
            ExtractionResult: Extraction result.

        Raises:
            ValueError: If specified extractor is not available.
            FileNotFoundError: If file doesn't exist.

        Example:
            >>> orchestrator = Orchestrator()
            >>> result = orchestrator.extract_simple(Path("doc.pdf"))
            >>> print(result.markdown)
        """
        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        # Select extractor (Feature #56: use registry)
        extractor_name = extractor_name or "docling"

        extractor = self.registry.get(extractor_name)
        if not extractor:
            available = self.registry.get_names()
            raise ValueError(
                f"Extractor '{extractor_name}' not available. "
                f"Available extractors: {available}"
            )


        logger.info(
            f"Starting simple extraction: {file_path.name} "
            f"using {extractor.name}"
        )

        # Extract
        result = extractor.extract(file_path, options)

        logger.info(
            f"Simple extraction completed: {file_path.name} "
            f"(success={result.success}, confidence={result.confidence_score})"
        )

        return result

    def get_available_extractors(self) -> List[Dict[str, Any]]:
        """
        Get list of available extractors with their info (Feature #56).

        Returns:
            list[dict]: List of extractor info dictionaries.

        Example:
            >>> orchestrator = Orchestrator()
            >>> extractors = orchestrator.get_available_extractors()
            >>> for ext in extractors:
            ...     print(f"{ext['name']}: {ext['capabilities']}")
        """
        return [extractor.get_info() for extractor in self.registry.get_available()]

    def get_extractor(self, name: str) -> Optional[BaseExtractor]:
        """
        Get a specific extractor by name (Feature #56).

        Args:
            name: Extractor name.

        Returns:
            BaseExtractor: Extractor instance or None if not found.

        Example:
            >>> orchestrator = Orchestrator()
            >>> docling = orchestrator.get_extractor("docling")
            >>> if docling:
            ...     result = docling.extract(pdf_path)
        """
        return self.registry.get(name)
