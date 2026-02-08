"""
NeuroCode API Main Application.

FastAPI application with CORS, error handling, rate limiting, and lifecycle management.
Requires Python 3.11+.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.dependencies import set_neo4j_client, get_neo4j_client
from api.middleware.request_id import RequestIDMiddleware
from api.middleware.rate_limit import RateLimitMiddleware, rate_limit
from graph_db.neo4j_client import Neo4jClient
from utils.config import get_settings
from utils.logger import configure_logging, get_logger


# Initialize logging
configure_logging()
logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Handles startup and shutdown tasks.
    """
    settings = get_settings()
    logger.info(
        "starting_application",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    # Initialize Neo4j client
    neo4j_client = Neo4jClient()
    try:
        connected = await neo4j_client.connect(timeout=10.0)
        if connected:
            await neo4j_client.initialize_schema()
            set_neo4j_client(neo4j_client)
        else:
            logger.warning("neo4j_connection_failed_or_incomplete")
            set_neo4j_client(None)
    except Exception as e:
        logger.error("neo4j_initialization_failed", error=str(e))
        # Continue without Neo4j for graceful degradation
        await neo4j_client.close()
        set_neo4j_client(None)

    yield

    # Cleanup - close all Neo4j clients to prevent leaks
    logger.info("shutting_down_application")
    await Neo4jClient.close_all()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance
    """
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        description="Interactive Hierarchical Code Visualization System",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID middleware for distributed tracing
    application.add_middleware(RequestIDMiddleware)

    # Rate limiting middleware (if enabled)
    if settings.api.rate_limit_enabled:
        from api.middleware.rate_limit import RateLimitMiddleware
        application.add_middleware(RateLimitMiddleware)

    # Global exception handler
    @application.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        error_id = str(id(exc))
        logger.exception(
            "unhandled_exception",
            error_id=error_id,
            path=request.url.path,
            method=request.method,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "error_id": error_id,
                "message": str(exc) if settings.is_development else "An unexpected error occurred",
            },
        )

    # HTTPException handler for better error responses
    @application.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail if isinstance(exc.detail, dict) else {"message": exc.detail},
            },
        )

    # Health check endpoint (with rate limiting)
    @application.get("/health")
    @rate_limit(requests_per_window=30, window_seconds=60)
    async def health_check() -> dict[str, Any]:
        """
        Health check endpoint.

        Rate limited to prevent abuse and information leakage.
        Returns limited information to prevent intelligence gathering.
        """
        client = get_neo4j_client()
        neo4j_status = "connected" if client else "disconnected"

        # In production, return limited information
        if not settings.is_development:
            return {
                "status": "healthy",
            }

        # Development: include more details
        return {
            "status": "healthy",
            "version": settings.app_version,
            "neo4j": neo4j_status,
        }

    # Import and include routers here to avoid circular imports
    from api.routes import graph, search, websocket
    
    application.include_router(graph.router, prefix="/graph", tags=["Graph"])
    application.include_router(search.router, prefix="/search", tags=["Search"])
    application.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])

    return application


# Create the application instance
app = create_app()
