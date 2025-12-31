# API Documentation (Feature #115)

## PDF-to-Markdown Extractor REST API

Version: 1.0.0

Base URL: `http://localhost:8000`

---

## Authentication (Feature #113)

Optional API key authentication via header:

```
X-API-Key: your-api-key-here
```

If `API_KEY` environment variable is set, all requests require this header.

---

## Rate Limiting (Feature #112)

- **Limit:** 10 requests per minute per IP
- **Response:** `429 Too Many Requests` if exceeded

---

## Endpoints

### POST /api/v1/extract

Extract PDF document (Features #101, #110-111).

**Request:**
- Method: POST
- Content-Type: `multipart/form-data` or `application/json`
- Max file size: 50 MB (Feature #110)
- Allowed MIME type: `application/pdf` (Feature #111)

**Parameters:**
- `file` (file): PDF file to extract (multipart upload)
- `url` (string): URL to PDF file (alternative to file)
- `strategy` (string): Extraction strategy (`fallback`, `parallel_local`, `parallel_all`, `hybrid`)
- `force_complexity` (string): Force complexity level (`simple`, `medium`, `complex`)
- `extract_tables` (boolean): Extract tables (default: true)
- `extract_images` (boolean): Extract images (default: false)
- `extract_formulas` (boolean): Extract formulas (default: true)
- `callback_url` (string): Webhook URL for completion notification (Feature #107)

**Response:**
```json
{
  "job_id": "abc-123",
  "status": "pending",
  "message": "Extraction job queued successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -H "X-API-Key: your-key" \
  -F "file=@document.pdf" \
  -F "strategy=parallel_local"
```

---

### GET /api/v1/status/{job_id}

Get job status and progress (Feature #102).

**Parameters:**
- `job_id` (path): Job identifier

**Response:**
```json
{
  "job_id": "abc-123",
  "status": "extracting",
  "progress_percentage": 45.0,
  "updated_at": "2025-12-30T14:30:00",
  "metadata": {
    "file_path": "document.pdf",
    "strategy": "parallel_local"
  }
}
```

**Status values:**
- `pending`: Job queued
- `extracting`: Extraction in progress
- `comparing`: Comparing results (parallel strategies)
- `needs_review`: Divergences require human review
- `completed`: Job finished successfully
- `failed`: Job failed with error

---

### GET /api/v1/result/{job_id}

Get extraction result (Feature #103).

**Parameters:**
- `job_id` (path): Job identifier

**Response:**
```json
{
  "job_id": "abc-123",
  "result": {
    "markdown": "# Document\n\nExtracted content...",
    "metadata": {...},
    "confidence_score": 0.95,
    "extraction_time": 45.2,
    "success": true
  },
  "complexity": {
    "total_score": 35,
    "complexity_level": "medium",
    "components": {...}
  },
  "aggregation": {
    "extractor_count": 2,
    "successful_count": 2,
    "average_confidence": 0.925
  }
}
```

---

### GET /api/v1/review/{job_id}

Get divergences for review (Feature #105).

**Parameters:**
- `job_id` (path): Job identifier

**Response:**
```json
{
  "job_id": "abc-123",
  "divergences": [
    {
      "id": "div-1",
      "type": "text_mismatch",
      "page": 3,
      "similarity": 0.75,
      "content_a": "Content from Docling",
      "content_b": "Content from MinerU"
    }
  ],
  "divergence_count": 7
}
```

---

### POST /api/v1/arbitrate/{job_id}

Submit arbitration choices (Feature #104).

**Parameters:**
- `job_id` (path): Job identifier

**Request Body:**
```json
{
  "choices": [
    {
      "divergence_id": "div-1",
      "choice": "A"
    },
    {
      "divergence_id": "div-2",
      "choice": "manual",
      "content": "Custom edited text"
    }
  ]
}
```

**Choice values:**
- `A`: Use extraction A (typically Docling)
- `B`: Use extraction B (typically MinerU)
- `manual`: Use custom edited content

**Response:**
```json
{
  "job_id": "abc-123",
  "status": "completed",
  "choices_applied": 2,
  "message": "Arbitration choices applied successfully"
}
```

---

### GET /api/v1/download/{job_id}/{file_type}

Download result file (Feature #106).

**Parameters:**
- `job_id` (path): Job identifier
- `file_type` (path): File type (`markdown` or `metadata`)

**Response:**
- `markdown`: Returns `.md` file with extracted content
- `metadata`: Returns `.json` file with extraction metadata

---

## Webhooks (Features #107-108)

When `callback_url` is provided in extraction request:

**Webhook sent on:**
- Job completion (status: `completed`)
- Job failure (status: `failed`)

**Payload:**
```json
{
  "job_id": "abc-123",
  "status": "completed",
  "result": {...}
}
```

**Retry policy (Feature #108):**
- Max attempts: 3
- Delay: 5 seconds
- Backoff: Exponential (5s, 10s, 20s)

---

## Error Responses (Feature #119)

All errors return consistent JSON:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

**Common status codes:**
- `400`: Bad Request (invalid input)
- `401`: Unauthorized (invalid API key)
- `404`: Not Found (job not found)
- `413`: Payload Too Large (file > 50MB)
- `429`: Too Many Requests (rate limit)
- `500`: Internal Server Error

---

## OpenAPI Documentation (Feature #114)

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Examples

### Basic Extraction

```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -F "file=@document.pdf"
```

### Parallel Extraction with Callback

```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -F "file=@document.pdf" \
  -F "strategy=parallel_local" \
  -F "callback_url=https://example.com/webhook"
```

### Check Status

```bash
curl http://localhost:8000/api/v1/status/abc-123
```

### Download Result

```bash
curl http://localhost:8000/api/v1/download/abc-123/markdown \
  -o result.md
```

---

For more information, see the OpenAPI documentation at `/docs`.
