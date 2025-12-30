"""
PDF-to-Markdown Extractor - Main API entry point.

FastAPI application with CORS, error handling, and health monitoring.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger


# ==========================================
# Application Lifecycle
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("Starting PDF-to-Markdown Extractor API")
    logger.info(f"Environment: {os.getenv('LOG_LEVEL', 'INFO')}")

    yield

    # Shutdown
    logger.info("Shutting down PDF-to-Markdown Extractor API")


# ==========================================
# FastAPI Application
# ==========================================
app = FastAPI(
    title="PDF-to-Markdown Extractor",
    description="Convert PDF documents to structured Markdown optimized for LLM processing",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ==========================================
# CORS Middleware
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Root Endpoints
# ==========================================
@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "service": "pdf-to-markdown-extractor",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "message": "PDF to Markdown conversion API - Ready for requests"
    }


@app.get("/health")
async def health():
    """
    Health check endpoint.

    Returns:
        dict: Service health status
    """
    return {
        "status": "healthy",
        "service": "pdf-to-markdown-extractor",
        "version": "1.0.0"
    }
