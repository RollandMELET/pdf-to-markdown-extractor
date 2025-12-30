# PDF-to-Markdown Extractor

> PDF to Markdown conversion module for LLM, with automatic complexity evaluation, parallel multi-extraction, and human arbitration for divergences.

## 🚧 Status: In Development

This project is currently being developed using the [Agent Harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) methodology.

## Features (Planned)

- **Automatic complexity evaluation** - Documents are scored and routed appropriately
- **Multiple extraction engines** - Docling, MinerU, Mistral OCR
- **Parallel extraction** - Run multiple extractors simultaneously for best results
- **Smart comparison** - Detect divergences between extraction results
- **Human arbitration** - Resolve conflicts via web UI when extractors disagree
- **n8n integration** - Webhooks for workflow automation
- **Docker deployment** - Portable across Mac M4 and Linux VPS

## Extraction Strategies

| Strategy | Behavior | Cost |
|----------|----------|------|
| `fallback` | Docling → MinerU → Mistral (on failure) | Minimal |
| `parallel_local` | Docling + MinerU in parallel | Free |
| `parallel_all` | Docling + MinerU + Mistral in parallel | ~$0.002/page |
| `hybrid` | Local first, Mistral if divergences | Variable |

## Documentation

- [SPEC.md](SPEC.md) - Full technical specifications
- [CLAUDE.md](CLAUDE.md) - Development instructions for Claude Code

## Quick Start

```bash
# Clone the repository
git clone https://github.com/RollandMELET/pdf-to-markdown-extractor.git
cd pdf-to-markdown-extractor

# Start with Docker
docker-compose up -d

# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## API Usage

```bash
# Extract a PDF
curl -X POST http://localhost:8000/api/v1/extract \
  -F "file=@document.pdf" \
  -F 'options={"extraction_strategy": "parallel_local"}'

# Check status
curl http://localhost:8000/api/v1/status/{job_id}

# Get result
curl http://localhost:8000/api/v1/result/{job_id}
```

## License

MIT

## Author

Rolland MELET - [RoRworld](https://github.com/RollandMELET)
