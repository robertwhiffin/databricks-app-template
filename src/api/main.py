"""FastAPI application for Databricks Chat Template."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import chat, sessions
from src.api.routes.settings import (
    ai_infra_router,
    mlflow_router,
    profiles_router,
    prompts_router,
)
from src.core.database import init_db
from src.utils.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


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

# Register routers
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(profiles_router)
app.include_router(ai_infra_router)
app.include_router(mlflow_router)
app.include_router(prompts_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Databricks Chat App Template",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
