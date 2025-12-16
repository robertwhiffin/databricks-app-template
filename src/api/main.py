"""FastAPI application for Databricks Chat Template."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from src.api.routes import chat, sessions
from src.core.database import init_db
# Import models to register them with SQLAlchemy Base before init_db() is called
from src.database.models import (  # noqa: F401
    ChatRequest,
    SessionMessage,
    UserSession,
)
from src.utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Path to static files
STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Databricks Chat Template")

    # Initialize database tables
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Databricks Chat Template")


# Create FastAPI app
app = FastAPI(
    title="Databricks Chat App Template",
    description="A production-ready chat application template for Databricks",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(chat.router)
app.include_router(sessions.router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/info")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Databricks Chat App Template",
        "version": "1.0.0",
        "status": "running"
    }


# Serve static frontend
@app.get("/")
async def serve_frontend():
    """Serve the chat frontend."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "Frontend not found", "path": str(index_path)}


@app.get("/favicon.ico")
async def favicon():
    """Return empty response for favicon to prevent 404."""
    return Response(status_code=204)
