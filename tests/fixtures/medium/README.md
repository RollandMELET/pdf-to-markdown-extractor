# Medium Complexity PDF Fixtures

This directory contains medium complexity PDF files for testing intermediate extraction scenarios.

## Characteristics

Medium complexity PDFs have the following characteristics:
- **Mixed content**: text, tables, lists
- Multi-column layouts (2-3 columns)
- Tables with moderate complexity (3-10 columns, merged cells)
- Some images/diagrams (not heavily embedded)
- Headers and footers with page numbers
- Some formatting: bold, italic, bullet points
- Page count: 5-20 pages

## Purpose

These fixtures are used to test:
- Multi-column layout detection
- Table extraction and markdown table generation
- List detection (ordered and unordered)
- Text formatting preservation (bold, italic)
- Header/footer handling
- Page break detection
- Image placeholder insertion

## Examples of Medium PDFs

- Business reports with tables
- Academic papers with 2-column layout
- Technical documentation with diagrams
- Product catalogs with images and tables
- Magazine articles with mixed layouts

## Usage

```python
from pathlib import Path

def test_medium_extraction(medium_pdf_path):
    pdf_file = medium_pdf_path / "report_with_tables.pdf"
    # Test table extraction...
```

## Adding New Fixtures

When adding PDF files to this directory:
1. Ensure they have moderate complexity (not too simple, not too complex)
2. Include variety: tables, multi-column, lists, images
3. Name files descriptively (e.g., `two_column_with_tables.pdf`)
4. Keep file sizes reasonable (< 1 MB when possible)
5. Document any special characteristics in filename
