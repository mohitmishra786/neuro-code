"""
NeuroCode API Main Application.

FastAPI application with CORS, error handling, and lifecycle management.
Requires Python 3.11+.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.dependencies import set_neo4j_client, get_neo4j_client
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
        await neo4j_client.connect()
        await neo4j_client.initialize_schema()
        set_neo4j_client(neo4j_client)
    except Exception as e:
        logger.error("neo4j_initialization_failed", error=str(e))
        # Continue without Neo4j for graceful degradation
        set_neo4j_client(None)

    yield

    # Cleanup
    logger.info("shutting_down_application")
    client = get_neo4j_client()
    if client:
        await client.close()


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

    # Global exception handler
    @application.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc) if settings.is_development else "An unexpected error occurred",
            },
        )

    # Health check endpoint
    @application.get("/health")
    async def health_check() -> dict[str, Any]:
        """Health check endpoint."""
        neo4j_status = "connected" if get_neo4j_client() else "disconnected"
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
