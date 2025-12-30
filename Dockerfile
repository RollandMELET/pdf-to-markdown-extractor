# PDF-to-Markdown Extractor - Dockerfile
# Multi-stage build for optimized image size

# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM python:3.11-slim

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PDF processing
    poppler-utils \
    # OCR engine
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    # Image processing
    libmagic1 \
    # Fonts for rendering
    fonts-liberation \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ /app/src/
COPY tests/ /app/tests/
COPY README.md SPEC.md pytest.ini /app/

# Create necessary directories
RUN mkdir -p /app/data/uploads /app/data/outputs /app/data/cache && \
    chmod -R 755 /app/data

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check placeholder (will be configured based on service type)
# Overridden in docker-compose.yml for each service

# Expose API port (default for API service)
EXPOSE 8000

# Default command (overridden in docker-compose.yml)
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
