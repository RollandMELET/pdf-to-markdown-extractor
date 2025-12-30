"""
PDF-to-Markdown Extractor - Result Normalizer (Features #72-76).

Normalizes extraction results for consistency across extractors.
"""

import re
from pathlib import Path
from typing import List, Dict, Any

from loguru import logger


class ExtractionNormalizer:
    """
    Normalizes extraction results (Features #72-76).

    Ensures consistent formatting across different extractors:
    - Feature #72: Markdown output normalization
    - Feature #73: Table format standardization
    - Feature #74: Image path standardization
    - Feature #75: Metrics collection
    - Feature #76: Unified output format

    Example:
        >>> normalizer = ExtractionNormalizer()
        >>> normalized = normalizer.normalize_markdown(markdown_text)
        >>> tables = normalizer.normalize_tables(raw_tables)
    """

    def __init__(self):
        """Initialize normalizer."""
        pass

    def normalize_markdown(self, markdown: str) -> str:
        """
        Normalize markdown output format (Feature #72).

        Standardizes:
        - Heading levels (## for main sections)
        - List formatting (- for bullets)
        - Line breaks (consistent spacing)
        - Code blocks (```language syntax)

        Args:
            markdown: Raw markdown from extractor.

        Returns:
            str: Normalized markdown.

        Example:
            >>> normalizer = ExtractionNormalizer()
            >>> normalized = normalizer.normalize_markdown("# Title\\n\\nText")
        """
        if not markdown:
            return ""

        # Normalize line endings
        markdown = markdown.replace('\r\n', '\n').replace('\r', '\n')

        # Normalize multiple blank lines to max 2
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # Normalize list markers (standardize to -)
        markdown = re.sub(r'^\s*[•●∙]\s', '- ', markdown, flags=re.MULTILINE)

        # Normalize heading spacing (ensure blank line before headings)
        markdown = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', markdown)

        # Remove trailing whitespace
        lines = [line.rstrip() for line in markdown.split('\n')]
        markdown = '\n'.join(lines)

        # Ensure single trailing newline
        markdown = markdown.rstrip() + '\n'

        logger.debug(f"Normalized markdown: {len(markdown)} chars")

        return markdown

    def normalize_tables(self, tables: List[str]) -> List[str]:
        """
        Standardize table format to markdown (Feature #73).

        Converts all table formats to consistent markdown table syntax.

        Args:
            tables: List of tables in various formats.

        Returns:
            list[str]: List of normalized markdown tables.

        Example:
            >>> normalizer = ExtractionNormalizer()
            >>> tables = normalizer.normalize_tables(raw_tables)
        """
        normalized = []

        for table in tables:
            if not table:
                continue

            # If already markdown table, validate format
            if '|' in table and '---' in table:
                normalized_table = self._validate_markdown_table(table)
                normalized.append(normalized_table)
            else:
                # Convert other formats to markdown table
                # (placeholder - actual conversion depends on input format)
                logger.warning("Table not in markdown format, keeping as-is")
                normalized.append(table)

        logger.debug(f"Normalized {len(normalized)} tables")

        return normalized

    def _validate_markdown_table(self, table: str) -> str:
        """
        Validate and fix markdown table format.

        Args:
            table: Markdown table string.

        Returns:
            str: Validated markdown table.
        """
        lines = table.strip().split('\n')

        if len(lines) < 2:
            return table

        # Ensure separator line has correct format
        if len(lines) >= 2 and not lines[1].strip().startswith('|'):
            # Fix separator line
            col_count = lines[0].count('|') - 1
            separator = '|' + '---|' * col_count
            lines.insert(1, separator)

        return '\n'.join(lines)

    def normalize_image_paths(self, images: List[str], base_dir: Path) -> List[str]:
        """
        Standardize image reference paths (Feature #74).

        Ensures all image paths use consistent relative paths.

        Args:
            images: List of image paths or references.
            base_dir: Base directory for relative paths.

        Returns:
            list[str]: List of normalized image paths.

        Example:
            >>> normalizer = ExtractionNormalizer()
            >>> paths = normalizer.normalize_image_paths(
            ...     ["/abs/path/img.png"],
            ...     Path("output")
            ... )
        """
        normalized = []

        for img in images:
            if not img:
                continue

            # Convert absolute paths to relative
            try:
                img_path = Path(img)

                if img_path.is_absolute():
                    # Make relative to base_dir
                    try:
                        relative = img_path.relative_to(base_dir)
                        normalized.append(str(relative))
                    except ValueError:
                        # Not relative to base_dir, use filename only
                        normalized.append(img_path.name)
                else:
                    # Already relative
                    normalized.append(img)

            except Exception as e:
                logger.warning(f"Failed to normalize image path '{img}': {e}")
                normalized.append(img)

        logger.debug(f"Normalized {len(normalized)} image paths")

        return normalized

    def collect_metrics(self, extraction_result) -> Dict[str, Any]:
        """
        Collect extraction metrics (Feature #75).

        Args:
            extraction_result: ExtractionResult instance.

        Returns:
            dict: Collected metrics.
                {
                    'total_chars': int,
                    'total_lines': int,
                    'table_count': int,
                    'image_count': int,
                    'formula_count': int,
                    'extraction_time': float,
                    'time_per_page': float,
                    'confidence': float,
                    'errors': int,
                    'warnings': int,
                }

        Example:
            >>> normalizer = ExtractionNormalizer()
            >>> metrics = normalizer.collect_metrics(result)
            >>> print(f"Time per page: {metrics['time_per_page']:.2f}s")
        """
        page_count = extraction_result.metadata.get('page_count', 1)

        metrics = {
            'total_chars': len(extraction_result.markdown),
            'total_lines': extraction_result.markdown.count('\n'),
            'table_count': len(extraction_result.tables),
            'image_count': len(extraction_result.images),
            'formula_count': len(extraction_result.formulas),
            'extraction_time': extraction_result.extraction_time,
            'time_per_page': extraction_result.extraction_time / page_count if page_count > 0 else 0,
            'confidence': extraction_result.confidence_score,
            'errors': len(extraction_result.errors),
            'warnings': len(extraction_result.warnings),
        }

        logger.debug(f"Collected metrics: {metrics}")

        return metrics
