# PDF-to-Markdown Extractor (Feature #129)

**Version:** 1.0.0
**Status:** Production Ready (85.5% complete)

Convert PDF documents to structured Markdown optimized for LLM processing.

## ✨ Features

- 🚀 **Dual Extraction**: Docling + MinerU for accuracy
- 🔄 **Parallel Processing**: Run multiple extractors simultaneously
- 🧠 **Smart Complexity Analysis**: Auto-route based on document complexity
- 💾 **Redis Caching**: 22x speedup on repeated analyses
- 📊 **Human Arbitration**: Streamlit UI for resolving divergences
- 🎯 **REST API**: Complete FastAPI endpoints
- 🔔 **Webhooks**: Callback notifications on completion
- 📈 **Monitoring**: Job status, progress tracking, resource monitoring

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)

### Installation

```bash
# Clone repository
git clone https://github.com/RollandMELET/pdf-to-markdown-extractor.git
cd pdf-to-markdown-extractor

# Create .env file
cp .env.example .env

# Edit .env with your configuration
# (Optional: Add MISTRAL_API_KEY for Mistral extractor)

# Start all services
docker-compose up -d

# Check services are running
docker-compose ps
```

### Usage

#### API Request

```bash
# Extract PDF
curl -X POST http://localhost:8000/api/v1/extract \
  -F "file=@document.pdf" \
  -F "strategy=parallel_local"

# Get status
curl http://localhost:8000/api/v1/status/{job_id}

# Get result
curl http://localhost:8000/api/v1/result/{job_id}
```

#### Python SDK

```python
import requests

# Upload PDF
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/extract',
        files={'file': f},
        data={'strategy': 'parallel_local'}
    )

job_id = response.json()['job_id']

# Check status
status = requests.get(f'http://localhost:8000/api/v1/status/{job_id}').json()
print(f"Status: {status['status']} - {status['progress_percentage']}%")

# Get result
result = requests.get(f'http://localhost:8000/api/v1/result/{job_id}').json()
markdown = result['result']['markdown']
```

---

## 📊 Architecture

```
┌─────────────────────────────────────┐
│  REST API (FastAPI) - Port 8000     │
│  + Streamlit UI - Port 8501         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Celery Worker                      │
│  - Job tracking (Redis)             │
│  - Resource monitoring              │
│  - Webhook callbacks                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Orchestrator                       │
│  - Complexity analysis (cached)     │
│  - Parallel execution               │
│  - Result aggregation               │
└──────────────┬──────────────────────┘
               │
     ┌─────────┴──────────┐
     ▼                    ▼
┌──────────┐        ┌──────────┐        ┌──────────┐
│ Docling  │        │  MinerU  │        │ Mistral  │
│ Local    │        │  Local   │        │  API     │
│ Priority │        │  +GPU    │        │ Fallback │
│    1     │        │  +VLM    │        │  Cost:   │
│          │        │ Priority │        │ $0.002/p │
│          │        │    2     │        │          │
└──────────┘        └──────────┘        └──────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Post-Processing                    │
│  - Normalization (markdown, tables) │
│  - Comparison (similarity, blocks)  │
│  - Merging (strategies, auto-merge) │
└─────────────────────────────────────┘
```

---

## 📖 Documentation

- **API Reference**: [docs/API.md](docs/API.md)
- **Deployment Guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **OpenAPI Spec**: http://localhost:8000/docs
- **Technical Spec**: [SPEC.md](SPEC.md)

---

## 🛠️ Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Start services individually
uvicorn src.api.main:app --reload --port 8000
celery -A src.core.celery_app worker --loglevel=info
streamlit run src/arbitration/streamlit_app.py
redis-server
```

---

## ⚙️ Configuration

### Environment Variables

```env
# API
API_PORT=8000
API_KEY=optional-api-key

# Redis
REDIS_URL=redis://redis:6379/0

# External APIs
MISTRAL_API_KEY=your-mistral-api-key

# Limits
MAX_FILE_SIZE_MB=50
MAX_PAGES=100
EXTRACTION_TIMEOUT_SECONDS=600

# Extraction
DEFAULT_EXTRACTION_STRATEGY=fallback
SIMILARITY_THRESHOLD=0.85
```

### Extraction Strategies

- `fallback`: Docling → MinerU → Mistral (sequential)
- `parallel_local`: Docling + MinerU (parallel, free)
- `parallel_all`: All 3 extractors (parallel, ~$0.002/page)
- `hybrid`: Local first, Mistral if divergences

---

## 📈 Performance

- **Simple PDFs**: ~10-20s (Docling only)
- **Complex PDFs**: ~30-60s (Parallel extraction)
- **Caching**: 22x speedup on complexity re-analysis
- **Memory**: 2-4GB per extractor

---

## 🧪 Testing

```bash
# Run all tests
./validate_all.sh

# Or manually
docker-compose exec api pytest tests/ -v

# Run specific test
pytest tests/test_complexity.py -v
```

---

## 📦 Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for:
- Docker deployment
- Coolify integration
- VPS setup
- Environment configurations

---

## 📝 License

MIT License - See LICENSE file

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 🔗 Links

- **Repository**: https://github.com/RollandMELET/pdf-to-markdown-extractor
- **Issues**: https://github.com/RollandMELET/pdf-to-markdown-extractor/issues
- **Docling**: https://github.com/docling-project/docling
- **MinerU**: https://github.com/opendatalab/MinerU
- **Mistral**: https://docs.mistral.ai

---

**Built with ❤️ using FastAPI, Celery, Streamlit, and Python**
