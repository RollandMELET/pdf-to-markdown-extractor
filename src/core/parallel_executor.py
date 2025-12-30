"""
PDF-to-Markdown Extractor - Parallel Extraction Executor (Feature #57).

Executes multiple extractors in parallel using ThreadPoolExecutor.
"""

import psutil
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from src.extractors.base import BaseExtractor, ExtractionResult


class ParallelExecutor:
    """
    Parallel extraction executor (Feature #57).

    Runs multiple extractors in parallel using ThreadPoolExecutor,
    collecting results as they complete.

    Example:
        >>> executor = ParallelExecutor(max_workers=3)
        >>> results = executor.execute(
        ...     extractors=[docling, mineru],
        ...     file_path=Path("document.pdf")
        ... )
        >>> print(results.keys())
        dict_keys(['docling', 'mineru'])
    """

    def __init__(
        self,
        max_workers: int = 3,
        timeout: Optional[int] = None,
        memory_threshold_gb: float = 2.0,
    ):
        """
        Initialize parallel executor.

        Args:
            max_workers: Maximum number of parallel extractors (default: 3).
            timeout: Global timeout for all extractions in seconds (Feature #58).
                    None means no timeout.
            memory_threshold_gb: Minimum available memory in GB (Feature #60).
                                Default: 2.0 GB.
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.memory_threshold_gb = memory_threshold_gb

    def execute(
        self,
        extractors: List[BaseExtractor],
        file_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, ExtractionResult]:
        """
        Execute multiple extractors in parallel (Feature #57).

        Args:
            extractors: List of extractor instances to run.
            file_path: Path to PDF file.
            options: Extraction options to pass to all extractors.

        Returns:
            dict: Dictionary mapping extractor names to their results.
                  {extractor_name: ExtractionResult}

        Example:
            >>> executor = ParallelExecutor()
            >>> results = executor.execute(
            ...     extractors=[docling, mineru],
            ...     file_path=Path("doc.pdf")
            ... )
            >>> for name, result in results.items():
            ...     print(f"{name}: {result.success}")
        """
        if not extractors:
            logger.warning("No extractors provided for parallel execution")
            return {}

        # Feature #60: Memory management check
        if not self._check_memory():
            logger.warning(
                f"Low memory warning: Available memory below threshold "
                f"({self.memory_threshold_gb} GB). Parallel extraction may fail."
            )

        logger.info(
            f"Starting parallel extraction: {file_path.name} "
            f"with {len(extractors)} extractors (max_workers={self.max_workers})"
        )

        results: Dict[str, ExtractionResult] = {}
        start_time = time.time()

        # Create extraction tasks
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all extraction tasks
            future_to_extractor = {
                executor.submit(
                    self._extract_with_logging,
                    extractor,
                    file_path,
                    options
                ): extractor
                for extractor in extractors
            }

            # Collect results as they complete
            for future in as_completed(future_to_extractor, timeout=self.timeout):
                extractor = future_to_extractor[future]
                extractor_key = extractor.name.lower().replace("extractor", "")

                try:
                    result = future.result()
                    results[extractor_key] = result

                    logger.info(
                        f"Extractor {extractor.name} completed "
                        f"(success={result.success}, time={result.extraction_time:.2f}s)"
                    )

                except TimeoutError:
                    # Feature #58: Timeout handling
                    logger.error(
                        f"Extractor {extractor.name} timed out "
                        f"(timeout={self.timeout}s)"
                    )

                except Exception as e:
                    logger.error(
                        f"Extractor {extractor.name} failed: {e}",
                        exc_info=True
                    )

        total_time = time.time() - start_time

        logger.info(
            f"Parallel extraction completed: {len(results)}/{len(extractors)} "
            f"extractors succeeded in {total_time:.2f}s"
        )

        return results

    def _extract_with_logging(
        self,
        extractor: BaseExtractor,
        file_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> ExtractionResult:
        """
        Extract with logging wrapper.

        This is called in the thread pool to extract with proper logging.

        Args:
            extractor: Extractor instance.
            file_path: Path to PDF.
            options: Extraction options.

        Returns:
            ExtractionResult: Extraction result.
        """
        logger.info(f"Starting {extractor.name} extraction: {file_path.name}")

        try:
            result = extractor.extract(file_path, options)
            return result

        except Exception as e:
            logger.error(
                f"{extractor.name} extraction failed: {e}",
                exc_info=True
            )
            raise

    def _check_memory(self) -> bool:
        """
        Check available memory before parallel extraction (Feature #60).

        Returns:
            bool: True if sufficient memory available, False otherwise.

        Example:
            >>> executor = ParallelExecutor(memory_threshold_gb=2.0)
            >>> if executor._check_memory():
            ...     print("Sufficient memory")
        """
        try:
            # Get available memory
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024 ** 3)

            logger.debug(
                f"Memory check: {available_gb:.2f} GB available "
                f"(threshold: {self.memory_threshold_gb} GB)"
            )

            if available_gb < self.memory_threshold_gb:
                logger.warning(
                    f"Low memory: {available_gb:.2f} GB available "
                    f"(threshold: {self.memory_threshold_gb} GB)"
                )
                return False

            return True

        except Exception as e:
            logger.warning(f"Memory check failed: {e}")
            # Assume memory is sufficient if check fails
            return True
