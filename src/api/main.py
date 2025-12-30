"""
PDF-to-Markdown Extractor - Main API entry point.

This is a minimal stub to enable Dockerfile build testing.
Full implementation in later features.
"""

from fastapi import FastAPI

# Create FastAPI application
app = FastAPI(
    title="PDF-to-Markdown Extractor",
    description="Convert PDF documents to structured Markdown with LLM optimization",
    version="1.0.0",
)


@app.get("/")
async def root():
    """Root endpoint - API status."""
    return {
        "service": "pdf-to-markdown-extractor",
        "status": "initializing",
        "version": "1.0.0",
        "message": "API stub - full implementation pending"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
