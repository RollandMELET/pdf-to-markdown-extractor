# Simple PDF Fixtures

This directory contains simple PDF files for testing basic extraction functionality.

## Characteristics

Simple PDFs have the following characteristics:
- **Text-only** or minimal formatting
- Single column layout
- No or simple tables (max 2-3 columns)
- No images or diagrams
- Standard fonts (Times, Arial, Helvetica)
- No complex structures (headers/footers are simple)
- Page count: 1-5 pages

## Purpose

These fixtures are used to test:
- Basic text extraction
- Simple paragraph detection
- Basic markdown conversion
- Single-column layout handling
- Standard font rendering

## Examples of Simple PDFs

- Plain text documents
- Simple letters or memos
- Basic reports with text only
- Simple forms (text fields only)
- Single-page summaries

## Usage

```python
from pathlib import Path

def test_simple_extraction(simple_pdf_path):
    pdf_file = simple_pdf_path / "example.pdf"
    # Test basic extraction...
```

## Adding New Fixtures

When adding PDF files to this directory:
1. Ensure they match the "simple" criteria above
2. Name files descriptively (e.g., `text_only_single_page.pdf`)
3. Keep file sizes small (< 100 KB when possible)
4. Include a variety of simple cases
