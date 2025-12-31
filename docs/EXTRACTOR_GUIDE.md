# Extractor Development Guide (Feature #151)

## Adding a New Extractor to PDF-to-Markdown Extractor

This guide explains how to create and integrate a new PDF extractor.

---

## 📋 Overview

An extractor is a Python class that implements the `BaseExtractor` interface and converts PDF documents to structured markdown.

**Existing extractors:**
- `DoclingExtractor` - Local extraction with Docling
- `MinerUExtractor` - High-precision local extraction
- `MistralExtractor` - API-based OCR with Mistral

---

## 🏗️ Step 1: Create Extractor Class

Create `src/extractors/your_extractor.py`:

```python
from pathlib import Path
from typing import Any, Dict, List, Optional
import time

from loguru import logger

from src.extractors.base import BaseExtractor, ExtractionResult, ExtractionError


class YourExtractor(BaseExtractor):
    \"\"\"
    Your custom PDF extractor.

    Description of what makes this extractor unique.
    \"\"\"

    name: str = "YourExtractor"
    version: str = "1.0.0"
    description: str = "Brief description"

    def __init__(self):
        \"\"\"Initialize extractor.\"\"\"
        self._available = None
        self._check_availability()

    def _check_availability(self) -> None:
        \"\"\"Check if dependencies are installed.\"\"\"
        try:
            # Try to import required packages
            import your_library
            self._available = True
            logger.info(f"{self.name} initialized")
        except ImportError as e:
            self._available = False
            logger.warning(f"{self.name} not available: {e}")

    def is_available(self) -> bool:
        \"\"\"Check if extractor is available.\"\"\"
        return self._available is True

    def extract(
        self,
        file_path: Path,
        options: Optional[Dict[str, Any]] = None,
    ) -> ExtractionResult:
        \"\"\"
        Extract PDF to markdown.

        Args:
            file_path: Path to PDF file.
            options: Extraction options.

        Returns:
            ExtractionResult: Extraction result.

        Raises:
            ExtractionError: If extraction fails.
        \"\"\"
        if not self.is_available():
            raise ExtractionError(
                extractor=self.name,
                message="Dependencies not installed",
                file_path=str(file_path)
            )

        # Validate file
        self.validate_file(file_path)

        # Parse options
        options = options or {}
        extract_tables = options.get("extract_tables", True)

        logger.info(f"Starting {self.name} extraction: {file_path.name}")

        start_time = time.time()

        try:
            # YOUR EXTRACTION LOGIC HERE
            # 1. Read PDF
            # 2. Extract content
            # 3. Convert to markdown

            markdown_content = "# Document\\n\\nExtracted content"
            metadata = {
                "filename": file_path.name,
                "file_size": file_path.stat().st_size,
            }

            extraction_time = time.time() - start_time

            return ExtractionResult(
                markdown=markdown_content,
                metadata=metadata,
                images=[],
                tables=[],
                formulas=[],
                confidence_score=0.90,
                extraction_time=extraction_time,
                extractor_name=self.name,
                extractor_version=self.version,
                success=True,
            )

        except Exception as e:
            logger.error(f"{self.name} failed: {e}")
            raise ExtractionError(
                extractor=self.name,
                message=str(e),
                file_path=str(file_path),
                original_error=e
            )

    def get_capabilities(self) -> Dict[str, Any]:
        \"\"\"Return extractor capabilities (Feature #149).\"\"\"
        return {
            "name": self.name,
            "version": self.version,
            "supports_tables": True,
            "supports_formulas": False,
            "supports_images": True,
            "supports_ocr": False,
            "precision": "medium",
            "speed": "fast",
        }
```

---

## 🔧 Step 2: Register in ExtractorRegistry

Edit `src/core/registry.py`:

```python
from src.extractors.your_extractor import YourExtractor

class ExtractorRegistry:
    def _discover_extractors(self) -> None:
        extractor_classes = [
            DoclingExtractor,
            MinerUExtractor,
            MistralExtractor,
            YourExtractor,  # Add your extractor
        ]
        # ... rest of discovery logic
```

---

## ⚙️ Step 3: Add Configuration

Edit `config/extractors.yaml`:

```yaml
your_extractor:
  enabled: true
  priority: 4  # Lower number = higher priority

  options:
    extract_tables: true
    extract_images: false
    your_custom_option: true

  timeout: 300
  max_pages: 100

  capabilities:
    supports_tables: true
    supports_formulas: false
    precision: "medium"
    speed: "fast"
```

---

## 🧪 Step 4: Add Tests

Create `tests/test_your_extractor.py`:

```python
import pytest
from pathlib import Path

from src.extractors.your_extractor import YourExtractor

@pytest.fixture
def extractor():
    return YourExtractor()

def test_extractor_init(extractor):
    assert extractor.name == "YourExtractor"
    assert extractor.version == "1.0.0"

def test_is_available(extractor):
    available = extractor.is_available()
    assert isinstance(available, bool)

@pytest.mark.requires_pdf
def test_extraction(extractor):
    pdf_path = Path("tests/fixtures/simple/text_only.pdf")

    if not pdf_path.exists() or not extractor.is_available():
        pytest.skip("PDF or extractor not available")

    result = extractor.extract(pdf_path)

    assert result.success is True
    assert len(result.markdown) > 0
```

---

## 📦 Step 5: Add Dependencies

Edit `requirements.txt`:

```txt
# Your Extractor
your-library==1.2.3
```

---

## ✅ Checklist

Before submitting your extractor:

- [ ] Implements `BaseExtractor` interface
- [ ] Has `is_available()` check
- [ ] Raises `ExtractionError` on failure
- [ ] Returns proper `ExtractionResult`
- [ ] Has `get_capabilities()` method (Feature #149)
- [ ] Includes comprehensive docstrings
- [ ] Has type hints
- [ ] Registered in `ExtractorRegistry`
- [ ] Configured in `config/extractors.yaml`
- [ ] Has tests (>80% coverage)
- [ ] Documented in CHANGELOG.md
- [ ] Works in Docker container

---

## 🎯 Best Practices

### Error Handling

Always use `ExtractionError`:

```python
raise ExtractionError(
    extractor=self.name,
    message="Descriptive error message",
    file_path=str(file_path),
    original_error=e
)
```

### Logging

Use loguru for structured logging:

```python
logger.info(f"Extraction started: {file_path.name}")
logger.debug(f"Options: {options}")
logger.warning("Issue detected")
logger.error(f"Extraction failed: {e}")
```

### Capabilities

Return complete capabilities dict (Feature #149):

```python
{
    "name": self.name,
    "version": self.version,
    "supports_tables": bool,
    "supports_formulas": bool,
    "supports_images": bool,
    "supports_ocr": bool,
    "supports_complex_layouts": bool,
    "precision": "low|medium|high",
    "speed": "slow|medium|fast",
    # Add custom fields as needed
}
```

---

## 🧪 Testing

Test your extractor:

```bash
# Run extractor tests
pytest tests/test_your_extractor.py -v

# Test with test-extractor endpoint (Feature #144)
curl -X POST http://localhost:8000/api/v1/test-extractor \
  -H "Content-Type: application/json" \
  -d '{
    "extractor_name": "your_extractor",
    "file_path": "tests/fixtures/simple/text_only.pdf",
    "options": {}
  }'
```

---

## 📊 Priority System

Extractors are selected by priority (lower = higher priority):

1. **Priority 1**: Docling (default, fast, local)
2. **Priority 2**: MinerU (high precision, local, requires installation)
3. **Priority 3**: Mistral (API, fallback, costs $0.002/page)
4. **Priority 4+**: Your custom extractors

---

## 🔗 Examples

See existing extractors for reference:
- Simple: `src/extractors/docling_extractor.py`
- Advanced: `src/extractors/mineru_extractor.py`
- API-based: `src/extractors/mistral_extractor.py`

---

For questions, open an issue on GitHub!
