# Edge Cases PDF Fixtures

This directory contains edge case PDF files for testing error handling, boundary conditions, and unusual scenarios.

## Characteristics

Edge case PDFs include unusual or problematic scenarios:
- **Empty PDFs** (0 pages or blank pages)
- Corrupted or malformed PDFs
- Password-protected PDFs
- PDFs with unusual encodings
- Non-standard page sizes (A0, custom dimensions)
- PDFs with only images (no text)
- PDFs with unusual fonts or missing fonts
- Right-to-left text (Arabic, Hebrew)
- Mixed language content
- Extremely large files (100+ pages)
- PDFs with form fields
- PDFs with JavaScript or interactive elements

## Purpose

These fixtures are used to test:
- Error handling and graceful degradation
- Edge case detection and reporting
- Boundary condition handling
- Security (password protection, malicious PDFs)
- Performance limits (very large files)
- Encoding and language support
- Robustness and stability

## Examples of Edge Case PDFs

- `empty.pdf` - Zero content
- `corrupted.pdf` - Malformed structure
- `password_protected.pdf` - Requires password
- `images_only.pdf` - No extractable text
- `rtl_arabic.pdf` - Right-to-left text
- `huge_file.pdf` - 500+ pages
- `non_standard_size.pdf` - A0 or custom dimensions
- `missing_fonts.pdf` - Uses non-standard fonts
- `form_fields.pdf` - Interactive form

## Usage

```python
from pathlib import Path
import pytest

def test_empty_pdf_handling(edge_case_pdf_path):
    empty_pdf = edge_case_pdf_path / "empty.pdf"
    # Test that empty PDF is handled gracefully...

def test_corrupted_pdf_error(edge_case_pdf_path):
    corrupted = edge_case_pdf_path / "corrupted.pdf"
    with pytest.raises(PDFExtractionError):
        # Test that corrupted PDF raises appropriate error...
```

## Adding New Fixtures

When adding PDF files to this directory:
1. Clearly identify the edge case being tested
2. Name files very specifically (e.g., `zero_width_characters.pdf`)
3. Include a comment or note about expected behavior
4. Test both error cases and unusual-but-valid cases
5. Document the edge case in the filename

## Testing Guidelines

- Edge case tests should verify **error handling**, not just success
- Use `pytest.raises()` for expected errors
- Check that error messages are informative
- Verify that the application doesn't crash on edge cases
- Test that resources are properly cleaned up on errors

## Edge Case Categories

### 1. Empty/Blank
- Zero pages
- Blank pages only
- Zero-byte files

### 2. Corrupted
- Truncated files
- Invalid PDF headers
- Broken references

### 3. Security
- Password-protected
- Encrypted PDFs
- Potentially malicious content

### 4. Size/Performance
- Very large (100+ pages)
- Very small (< 1 KB)
- Extremely high resolution

### 5. Encoding/Language
- Non-Latin scripts
- Mixed languages
- Unusual character encodings
- Missing fonts

### 6. Structure
- No text (images only)
- No images (text only)
- Form fields
- Interactive elements
- JavaScript

### 7. Format
- Non-standard page sizes
- Rotated pages
- Mixed orientations
