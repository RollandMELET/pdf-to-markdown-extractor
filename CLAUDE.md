# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🎯 Project: PDF-to-Markdown Extractor

**Repository**: https://github.com/RollandMELET/pdf-to-markdown-extractor
**Version**: 1.0.0
**Owner**: Rolland MELET

PDF to Markdown conversion module optimized for LLMs, featuring:
- Automatic document complexity evaluation
- Parallel multi-extraction for complex documents
- Human arbitration interface for divergence resolution
- REST API compatible with n8n and webhooks
- Portable Docker deployment (Mac M4 + VPS)

---

## 🏗️ Development Strategy: Agent Harness

This project uses the **Agent Harness** pattern for incremental, robust development.

### Session Startup Protocol (MANDATORY)

**Execute these steps at the start of EVERY session:**

```bash
# 1. Confirm working directory
pwd

# 2. Run initialization script (shows project status)
./init.sh

# 3. Read progress log
cat claude-progress.txt

# 4. Check recent commits
git log --oneline -10

# 5. Identify next pending feature
# Look for "status": "pending" in feature_list.json
cat feature_list.json | grep -A 5 '"status": "pending"' | head -20
```

### Core Rules

1. **ONE FEATURE PER SESSION** - Never work on multiple features simultaneously
2. **COMMIT BEFORE END** - Each session ends with a functional commit
3. **UPDATE TRACKING** - Update both `feature_list.json` and `claude-progress.txt` after each feature
4. **TESTS BEFORE VALIDATION** - A feature is "passing" only when tests pass
5. **ALWAYS MERGE-READY** - Code must always be in a deployable state

---

## 💻 Development Commands

### Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (once created)
pip install -r requirements.txt

# Run initialization check
./init.sh
```

### Running the Application

```bash
# Start all services with Docker
docker-compose up -d

# Start only API (after docker-compose up)
docker-compose up api

# View logs
docker-compose logs -f api
docker-compose logs -f worker

# Stop services
docker-compose down
```

### Development Mode (without Docker)

```bash
# Start FastAPI in dev mode (auto-reload)
uvicorn src.api.main:app --reload --port 8000

# Start Celery worker
celery -A src.core.celery_app worker --loglevel=info

# Start Streamlit arbitration UI
streamlit run src/arbitration/streamlit_app.py

# Start Redis (required for Celery)
redis-server
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_extractors.py -v

# Run single test function
pytest tests/test_api.py::test_extract_endpoint -v

# Run tests matching pattern
pytest tests/ -k "complexity" -v
```

### Docker Commands

```bash
# Build image
docker build -t pdf-extractor .

# Rebuild services
docker-compose build

# Rebuild specific service
docker-compose build api

# Check running containers
docker-compose ps

# Execute command in container
docker-compose exec api python --version
docker-compose exec worker celery -A src.core.celery_app inspect active

# View resource usage
docker stats
```

### Git Workflow

```bash
# Check status
git status

# Stage changes
git add .

# Commit with conventional format
git commit -m "feat(extractors): add Docling base implementation"

# View commit history
git log --oneline -10
```

---

## 🏛️ Architecture Overview

### High-Level Structure

The project follows a plugin-based architecture:

```
┌─────────────────────────────────────────────────┐
│              FastAPI REST API                   │
│          (src/api/main.py + routes/)            │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│           Orchestrator (src/core/)              │
│  - Routes by complexity                         │
│  - Manages extraction strategies                │
│  - Coordinates parallel extractions             │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│         Extractor Plugins                       │
│         (src/extractors/)                       │
│  - DoclingExtractor (primary)                   │
│  - MinerUExtractor (high precision)             │
│  - MistralExtractor (API fallback)              │
└─────────────────────────────────────────────────┘
```

### Key Components

- **API Layer** (`src/api/`): FastAPI endpoints, request validation, response formatting
- **Core Logic** (`src/core/`): Orchestrator, complexity evaluator, result comparator
- **Extractors** (`src/extractors/`): Plugin system with `BaseExtractor` interface
- **Arbitration** (`src/arbitration/`): Streamlit UI for human divergence resolution
- **Workers** (Celery): Async task execution, parallel extraction management

### Extractor Plugin System

All extractors implement `BaseExtractor` interface:

```python
class BaseExtractor(ABC):
    name: str
    version: str

    @abstractmethod
    def extract(file_path: Path, options: dict) -> ExtractionResult:
        """Extract PDF to markdown"""

    @abstractmethod
    def is_available() -> bool:
        """Check if dependencies are installed"""

    @abstractmethod
    def get_capabilities() -> dict:
        """Return extractor capabilities"""
```

Key insight: The system uses **similarity scoring** between multiple extractions to detect divergences. When similarity falls below threshold, human arbitration is triggered.

### Extraction Strategies

Four strategies control extractor usage:

1. **fallback**: Docling → MinerU → Mistral (sequential, on failure)
2. **parallel_local**: Docling + MinerU parallel (free)
3. **parallel_all**: All three extractors parallel (~$0.002/page)
4. **hybrid**: Local first, Mistral if divergences detected

Strategy selection impacts cost vs accuracy tradeoff.

---

## 📋 Code Conventions

### Python Style

- **Docstrings**: Google style (see examples in SPEC.md)
- **Type hints**: Required for all function signatures
- **Line length**: 88 characters (Black default)
- **Import order**: stdlib → third-party → local (separated by blank lines)

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Git Commit Format

```
<type>(<scope>): <description>

Types: feat, fix, docs, test, refactor, chore
Scopes: api, extractors, core, arbitration, docker

Examples:
feat(extractors): add Docling extractor base implementation
fix(api): handle large file uploads correctly
test(core): add complexity evaluation tests
docs(readme): update installation instructions
```

---

## ⚙️ Configuration

Configuration uses 3-level priority (highest to lowest):

1. **API request parameters** - Per-job override
2. **config/settings.yaml** - Detailed configuration
3. **.env file** - Global environment variables

### Key Environment Variables

```env
# API
API_PORT=8000
LOG_LEVEL=INFO

# Redis/Celery
REDIS_URL=redis://redis:6379/0

# External APIs
MISTRAL_API_KEY=your_api_key_here

# Limits
MAX_FILE_SIZE_MB=50
MAX_PAGES=100
EXTRACTION_TIMEOUT_SECONDS=600
```

See `.env.example` for full list (created in Feature #5).

---

## 🧪 Testing Strategy

### Test Structure

```
tests/
├── fixtures/          # PDF test files
│   ├── simple/       # Text-only, simple tables
│   ├── medium/       # Multi-column, mixed content
│   ├── complex/      # Technical reports, scans
│   └── edge_cases/   # Empty, corrupted, formulas
├── test_api.py       # API endpoint tests
├── test_extractors.py # Extractor unit tests
└── test_complexity.py # Complexity evaluation tests
```

### Test Coverage Goals

- **Unit tests**: 80%+ coverage
- **Integration tests**: All API endpoints
- **E2E tests**: Complete extraction workflows

Use `pytest --cov=src --cov-report=html` to generate coverage report.

---

## ⚠️ Critical Constraints

### Technical Limits

1. **Memory**: Extractors consume 4-8GB RAM (MinerU especially)
2. **GPU**: MinerU benefits from GPU but works CPU-only (slower)
3. **Timeout**: Long documents (50+ pages) can take several minutes
4. **Disk**: Docling models require ~500MB

### Security Requirements

- Sandbox uploaded files (validate MIME, limit size)
- No shell injection in filenames (sanitize paths)
- Validate PDF structure before processing
- Rate limiting on API endpoints

### Priorities

**PRECISION > Speed** - This is a quality-first tool. Accuracy matters more than fast results.

---

## 📚 Key Resources

- **SPEC.md**: Complete functional and technical specifications
- **feature_list.json**: Source of truth for project scope (152 features)
- **claude-progress.txt**: Session-by-session progress log
- **Docling**: https://github.com/docling-project/docling
- **MinerU**: https://github.com/opendatalab/MinerU
- **Mistral OCR API**: https://docs.mistral.ai/capabilities/document_ai/basic_ocr

---

## 🔄 Session End Checklist

Before ending each session:

- [ ] Feature implementation complete and tested
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Code committed with conventional commit message
- [ ] `feature_list.json` updated (status: "passing" or "failing")
- [ ] `claude-progress.txt` updated with session notes
- [ ] Code is in merge-ready state

**Last updated**: 2025-12-30
