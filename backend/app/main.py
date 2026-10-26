"""FastAPI Main Application entry point for ResearchRadar."""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes_admin import router as admin_router
from app.api.routes_episodes import router as episodes_router
from app.api.routes_health import router as health_router
from app.api.routes_programs import router as programs_router
from app.api.routes_search import router as search_router
from app.config import settings
from app.core.database import Base, engine
from app.core.logging import logger
from app.search.client import check_meili_health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    logger.info("Initializing Tamasha Catalog Explorer backend services...")
    # Ensure database schemas are created
    Base.metadata.create_all(bind=engine)

    # Check Meilisearch connectivity
    if check_meili_health():
        logger.info(f"Connected successfully to Meilisearch at {settings.meili_http_addr}")
    else:
        logger.warning(
            f"Could not reach Meilisearch at {settings.meili_http_addr}. Is the engine running?"
        )

    yield
    logger.info("Tamasha Catalog Explorer backend shutting down...")


app = FastAPI(
    title="Tamasha Catalog Explorer API",
    description="Dedicated OTT media catalog discovery and search platform powered by Meilisearch.",
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Injects unique Request-ID and logs latency with structured JSON logs."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        # Skip high-frequency health checks from verbose logging
        if "/api/health" not in request.url.path:
            logger.info(
                f"{request.method} {request.url.path} returned {response.status_code} in {duration_ms}ms",
                extra={
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                },
            )
        return response
    except Exception as exc:
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        logger.exception(
            f"Unhandled exception during {request.method} {request.url.path}: {exc}",
            extra={"request_id": request_id, "duration_ms": duration_ms},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred while processing your request.",
                    "request_id": request_id,
                }
            },
        )


# Global Exception Handler for consistent error schemas
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc),
            }
        },
    )


# Include API Routers under /api
app.include_router(health_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(episodes_router, prefix="/api")
app.include_router(programs_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
