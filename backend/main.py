"""
DocSetu AI - Main Application
AI Document Intelligence Platform for India.
FastAPI backend with CORS, routers, middleware, and startup events.
"""

import os
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from db import init_db

# Configure logging
settings = get_settings()

os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.log_file, encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events for startup and shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.api_version}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Database: {settings.database_url.split('://')[0]}")

    # Initialize database
    init_db()
    logger.info("Database initialized successfully")

    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info(f"Upload directory: {settings.upload_dir}")

    # Ensure ChromaDB directory exists
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)

    logger.info(f"{settings.app_name} started successfully!")

    yield

    # Shutdown
    logger.info(f"{settings.app_name} shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description=(
        "AI Document Intelligence Platform for India. "
        "Extract entities, check compliance, and analyze documents "
        "with support for Indian languages and regulations."
    ),
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Rate Limiting
from routers.rate_limit import setup_rate_limiting
setup_rate_limiting(app)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware (OWASP recommended)
from middleware.security import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions globally."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# Import and include routers
from routers.auth import router as auth_router
from routers.documents import router as documents_router
from routers.analysis import router as analysis_router
from routers.compliance import router as compliance_router
from routers.admin import router as admin_router
from routers.payments import router as payments_router

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(analysis_router)
app.include_router(compliance_router)
app.include_router(admin_router)
app.include_router(payments_router)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Application health check endpoint.

    Returns:
        Health status with database connectivity info.
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.api_version,
        "environment": settings.app_env,
        "timestamp": datetime.utcnow().isoformat(),
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        API welcome message and documentation links.
    """
    return {
        "app": settings.app_name,
        "description": "AI Document Intelligence Platform for India",
        "version": settings.api_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "endpoints": {
            "auth": "/api/auth",
            "documents": "/api/documents",
            "analysis": "/api/analysis",
            "compliance": "/api/compliance",
            "admin": "/api/admin",
            "payments": "/api/payments",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
