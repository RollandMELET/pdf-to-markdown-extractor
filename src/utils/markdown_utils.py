"""
PDF-to-Markdown Extractor - Markdown Utilities.

Utilities for markdown generation and formatting with YAML frontmatter.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from loguru import logger

from src.extractors.base import ExtractionResult


def write_markdown(
    result: ExtractionResult,
    output_path: Path,
    include_frontmatter: bool = True,
    frontmatter_data: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Write extraction result to markdown file with YAML frontmatter.

    Args:
        result: ExtractionResult to write.
        output_path: Path to output markdown file.
        include_frontmatter: Whether to include YAML frontmatter (default: True).
        frontmatter_data: Additional frontmatter data to include.

    Returns:
        Path: Path to written markdown file.

    Example:
        >>> result = ExtractionResult(markdown="# Title\\n\\nContent")
        >>> output = write_markdown(result, Path("output.md"))
        >>> print(output.read_text())
        ---
        title: ...
        ---
        # Title

        Content
    """
    # Build frontmatter
    if include_frontmatter:
        frontmatter = _build_frontmatter(result, frontmatter_data)
        content = f"{frontmatter}\n{result.markdown}"
    else:
        content = result.markdown

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    logger.info(f"Markdown written: {output_path} ({len(content)} chars)")

    return output_path


def _build_frontmatter(
    result: ExtractionResult,
    additional_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build YAML frontmatter from extraction result.

    Args:
        result: ExtractionResult.
        additional_data: Additional data to include in frontmatter.

    Returns:
        str: YAML frontmatter block.
    """
    frontmatter_dict = {
        "title": result.metadata.get("title", "Untitled"),
        "extractor": result.extractor_name,
        "extractor_version": result.extractor_version,
        "extraction_date": result.extraction_timestamp.isoformat(),
        "extraction_time_seconds": round(result.extraction_time, 2),
        "page_count": result.page_count,
        "confidence_score": result.confidence_score,
        "table_count": result.table_count,
        "image_count": result.image_count,
    }

    # Add author if available
    if "author" in result.metadata:
        frontmatter_dict["author"] = result.metadata["author"]

    # Add file info
    if "filename" in result.metadata:
        frontmatter_dict["source_file"] = result.metadata["filename"]

    if "file_size" in result.metadata:
        frontmatter_dict["source_file_size"] = result.metadata["file_size"]

    # Add additional data
    if additional_data:
        frontmatter_dict.update(additional_data)

    # Convert to YAML
    yaml_content = yaml.dump(
        frontmatter_dict,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    return f"---\n{yaml_content}---"


def add_section_divider(
    markdown: str,
    section_title: str,
    level: int = 2,
) -> str:
    """
    Add a section divider to markdown content.

    Args:
        markdown: Existing markdown content.
        section_title: Title for new section.
        level: Heading level (1-6, default: 2).

    Returns:
        str: Markdown with added section.

    Example:
        >>> md = "# Doc\\n\\nContent"
        >>> md = add_section_divider(md, "New Section")
        >>> print(md)
        # Doc

        Content

        ## New Section
    """
    heading = "#" * level
    return f"{markdown}\n\n{heading} {section_title}\n"


def format_table_markdown(table_data: list[list[str]]) -> str:
    """
    Format table data as markdown table.

    Args:
        table_data: 2D list of table cells.

    Returns:
        str: Markdown table string.

    Example:
        >>> table = [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
        >>> md = format_table_markdown(table)
        >>> print(md)
        | Name | Age |
        |------|-----|
        | Alice | 30 |
        | Bob | 25 |
    """
    if not table_data or len(table_data) < 2:
        return ""

    # Header row
    header = table_data[0]
    separator = ["-" * max(len(cell), 3) for cell in header]
    data_rows = table_data[1:]

    # Build markdown
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]

    for row in data_rows:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def strip_frontmatter(markdown: str) -> tuple[Optional[dict], str]:
    """
    Extract YAML frontmatter from markdown.

    Args:
        markdown: Markdown content potentially with frontmatter.

    Returns:
        tuple: (frontmatter_dict, content_without_frontmatter)

    Example:
        >>> md = "---\\ntitle: Test\\n---\\n# Content"
        >>> frontmatter, content = strip_frontmatter(md)
        >>> print(frontmatter['title'])
        Test
        >>> print(content)
        # Content
    """
    if not markdown.startswith("---"):
        return None, markdown

    # Find end of frontmatter
    try:
        parts = markdown.split("---", 2)
        if len(parts) >= 3:
            frontmatter_yaml = parts[1]
            content = parts[2].lstrip("\n")

            # Parse YAML
            frontmatter_dict = yaml.safe_load(frontmatter_yaml)

            return frontmatter_dict, content
        else:
            return None, markdown
    except Exception as e:
        logger.warning(f"Failed to parse frontmatter: {e}")
        return None, markdown


def clean_markdown(markdown: str) -> str:
    """
    Clean and normalize markdown content.

    Removes excessive whitespace, normalizes line endings, etc.

    Args:
        markdown: Raw markdown content.

    Returns:
        str: Cleaned markdown content.

    Example:
        >>> md = "# Title\\n\\n\\n\\nContent\\n\\n\\n"
        >>> clean = clean_markdown(md)
        >>> # Excessive newlines removed
    """
    # Normalize line endings
    markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive blank lines (max 2 consecutive)
    while "\n\n\n" in markdown:
        markdown = markdown.replace("\n\n\n", "\n\n")

    # Remove trailing whitespace from lines
    lines = [line.rstrip() for line in markdown.split("\n")]
    markdown = "\n".join(lines)

    # Ensure single trailing newline
    markdown = markdown.rstrip() + "\n"

    return markdown
