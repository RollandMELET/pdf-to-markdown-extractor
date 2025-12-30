"""
PDF-to-Markdown Extractor - Extractor Registry (Feature #56).

Centralized registry pattern for managing available extractors.
"""

from typing import Dict, List, Optional

from loguru import logger

from src.extractors.base import BaseExtractor
from src.extractors.docling_extractor import DoclingExtractor
from src.extractors.mineru_extractor import MinerUExtractor


class ExtractorRegistry:
    """
    Registry for managing PDF extractors (Feature #56).

    The registry auto-discovers and manages all available extractors,
    providing a centralized way to access and query extractors.

    Example:
        >>> registry = ExtractorRegistry()
        >>> extractors = registry.get_available()
        >>> print([e.name for e in extractors])
        ['DoclingExtractor', 'MinerUExtractor']

        >>> docling = registry.get('docling')
        >>> result = docling.extract(pdf_path)
    """

    def __init__(self):
        """Initialize extractor registry and auto-discover extractors."""
        self._extractors: Dict[str, BaseExtractor] = {}
        self._discover_extractors()

    def _discover_extractors(self) -> None:
        """
        Auto-discover and register all available extractors.

        Attempts to instantiate each known extractor and registers
        those that are available (dependencies installed).
        """
        # List of all known extractor classes
        extractor_classes = [
            DoclingExtractor,
            MinerUExtractor,
            # Future extractors will be added here:
            # MistralExtractor (Feature #66+)
        ]

        logger.info("Discovering extractors...")

        for extractor_class in extractor_classes:
            try:
                # Instantiate extractor
                extractor = extractor_class()

                # Check if available (dependencies installed)
                if extractor.is_available():
                    # Register with normalized key
                    key = extractor.name.lower().replace("extractor", "")
                    self._extractors[key] = extractor

                    logger.info(
                        f"Registered extractor: {extractor.name} v{extractor.version} "
                        f"(key: '{key}')"
                    )
                else:
                    logger.debug(
                        f"Extractor {extractor_class.__name__} not available "
                        f"(dependencies not installed)"
                    )

            except Exception as e:
                logger.warning(
                    f"Failed to instantiate {extractor_class.__name__}: {e}"
                )

        logger.info(f"Total extractors registered: {len(self._extractors)}")

    def get_available(self) -> List[BaseExtractor]:
        """
        Get list of available extractors (Feature #56 verification).

        Returns:
            list[BaseExtractor]: List of available extractor instances.

        Example:
            >>> registry = ExtractorRegistry()
            >>> extractors = registry.get_available()
            >>> for extractor in extractors:
            ...     print(f"{extractor.name}: {extractor.description}")
        """
        return list(self._extractors.values())

    def get(self, name: str) -> Optional[BaseExtractor]:
        """
        Get a specific extractor by name.

        Args:
            name: Extractor name or key (case-insensitive).
                  Examples: "docling", "mineru", "DoclingExtractor"

        Returns:
            BaseExtractor: Extractor instance or None if not found.

        Example:
            >>> registry = ExtractorRegistry()
            >>> docling = registry.get("docling")
            >>> if docling:
            ...     result = docling.extract(pdf_path)
        """
        # Normalize key
        key = name.lower().replace("extractor", "")
        return self._extractors.get(key)

    def get_names(self) -> List[str]:
        """
        Get list of registered extractor names.

        Returns:
            list[str]: List of extractor names.

        Example:
            >>> registry = ExtractorRegistry()
            >>> print(registry.get_names())
            ['docling', 'mineru']
        """
        return list(self._extractors.keys())

    def has_extractor(self, name: str) -> bool:
        """
        Check if an extractor is available.

        Args:
            name: Extractor name or key.

        Returns:
            bool: True if extractor is available.

        Example:
            >>> registry = ExtractorRegistry()
            >>> if registry.has_extractor('docling'):
            ...     print("Docling is available")
        """
        key = name.lower().replace("extractor", "")
        return key in self._extractors

    def get_capabilities(self) -> Dict[str, Dict]:
        """
        Get capabilities of all registered extractors.

        Returns:
            dict: Dictionary mapping extractor names to their capabilities.

        Example:
            >>> registry = ExtractorRegistry()
            >>> caps = registry.get_capabilities()
            >>> print(caps['docling']['supports_tables'])
            True
        """
        return {
            name: extractor.get_capabilities()
            for name, extractor in self._extractors.items()
        }

    def count(self) -> int:
        """
        Get count of registered extractors.

        Returns:
            int: Number of registered extractors.
        """
        return len(self._extractors)
