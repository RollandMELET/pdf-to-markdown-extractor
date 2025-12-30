# Complex PDF Fixtures

This directory contains complex PDF files for testing advanced extraction scenarios.

## Characteristics

Complex PDFs have the following characteristics:
- **Highly structured** content with multiple elements
- Multi-column layouts (3+ columns, variable width)
- Complex tables (10+ columns, nested tables, complex merging)
- Heavy image content, embedded diagrams, charts
- Mathematical formulas or equations
- Technical drawings or CAD diagrams
- Multiple fonts, sizes, and styles
- Watermarks or background images
- Scanned pages (OCR required)
- Page count: 20+ pages

## Purpose

These fixtures are used to test:
- Complex layout detection and parsing
- OCR capabilities (for scanned pages)
- Table extraction in difficult scenarios
- Formula and equation handling
- Image extraction and description
- Multi-font and multi-size text handling
- Watermark removal or handling
- Performance with large documents

## Examples of Complex PDFs

- Scientific papers with formulas and figures
- Technical reports with CAD drawings
- Financial statements with complex tables
- Scanned book pages
- Legal documents with complex formatting
- Engineering specifications
- Research papers with extensive diagrams

## Usage

```python
from pathlib import Path

def test_complex_extraction(complex_pdf_path):
    pdf_file = complex_pdf_path / "scientific_paper_with_formulas.pdf"
    # Test formula extraction...
```

## Adding New Fixtures

When adding PDF files to this directory:
1. Ensure they represent genuinely complex extraction challenges
2. Include diverse complexity types: formulas, scans, nested tables, etc.
3. Name files very descriptively (e.g., `scanned_handwritten_notes.pdf`)
4. File size may be larger (< 5 MB acceptable for complex docs)
5. Document special extraction challenges in filename
6. Consider adding notes about expected extraction behavior

## Performance Note

Tests using complex fixtures may be marked with `@pytest.mark.slow` as they typically take longer to process.
