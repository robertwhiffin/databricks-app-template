"""Database connection and session management.

Supports multiple database backends:
- PostgreSQL: Local development and staging
- Databricks Lakebase: Production on Databricks Apps (detected via PGHOST env var)
"""
import logging
import os
from contextlib import contextmanager
from typing import Generator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


def _get_lakebase_token() -> str:
    """Get OAuth token for Lakebase authentication using Databricks SDK."""
    try:
        from databricks.sdk import WorkspaceClient
        import uuid

        ws = WorkspaceClient()

        # Get instance name from env or try to derive it
        instance_name = os.getenv("LAKEBASE_INSTANCE")

        if instance_name:
            # Generate credential for specific instance
            cred = ws.database.generate_database_credential(
                request_id=str(uuid.uuid4()),
                instance_names=[instance_name],
            )
            return cred.token
        else:
            # Fallback: use workspace authentication token
            # This works when the app has database resource attached
            token = ws.config.authenticate()
            if hasattr(token, "token"):
                return token.token
            return str(token)
    except Exception as e:
        logger.error(f"Failed to get Lakebase token: {e}")
        raise


def _get_database_url() -> str:
    """
    Determine database URL based on environment.

    Priority:
    1. DATABASE_URL environment variable (explicit override)
    2. PGHOST (Lakebase on Databricks Apps - auto-set when database resource attached)
    3. Default local PostgreSQL

    Returns:
        Database connection URL string
    """
    # Check for explicit DATABASE_URL first
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url and not explicit_url.startswith("jdbc:"):
        return explicit_url

    # Check for Lakebase environment (PGHOST auto-set by Databricks Apps)
    pg_host = os.getenv("PGHOST")
    pg_user = os.getenv("PGUSER")

    if pg_host and pg_user:
        # Running on Databricks Apps with Lakebase
        logger.info(f"Detected Lakebase environment (PGHOST: {pg_host})")

        # Get OAuth token for authentication
        token = _get_lakebase_token()
        encoded_token = quote_plus(token)

        # Build PostgreSQL connection URL
        database = "databricks_postgres"
        schema = os.getenv("LAKEBASE_SCHEMA", "app_data")

        url = f"postgresql://{pg_user}:{encoded_token}@{pg_host}:5432/{database}?sslmode=require"

        # Add schema to search path
        if schema:
            url += f"&options=-csearch_path%3D{schema}"

        return url

    # Default to local PostgreSQL for development
    return "postgresql://localhost/chat_template"


def _create_engine():
    """Create SQLAlchemy engine based on database configuration.

    Returns:
        Engine configured for the appropriate database backend
    """
    database_url = _get_database_url()
    sql_echo = os.getenv("SQL_ECHO", "false").lower() == "true"

    # All backends use PostgreSQL-compatible connections
    # (Lakebase is PostgreSQL-compatible)
    logger.info("Configuring database connection")

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=sql_echo,
    )


# Create engine (lazy initialization to allow environment setup)
_engine = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


# Session factory (lazy initialization)
_session_local = None


def get_session_local():
    """Get or create the session factory."""
    global _session_local
    if _session_local is None:
        _session_local = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _session_local


# Base class for models
Base = declarative_base()

# Backwards compatibility aliases
engine = property(lambda self: get_engine())
SessionLocal = property(lambda self: get_session_local())


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes.
    Yields database session and ensures cleanup.
    """
    session_factory = get_session_local()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Use in standalone scripts and services.
    """
    session_factory = get_session_local()
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Create schema (if needed), all tables, and seed default profile.
    
    For Lakebase, creates the schema specified by LAKEBASE_SCHEMA env var
    before creating tables, since SQLAlchemy's create_all() only creates tables.
    
    Also seeds a default profile if the database is empty, so the app
    works out-of-the-box on first deployment.
    """
    engine = get_engine()
    
    # Check if running on Lakebase and need to create schema
    pg_host = os.getenv("PGHOST")
    if pg_host:
        # Running on Lakebase - ensure schema exists
        schema = os.getenv("LAKEBASE_SCHEMA", "app_data")
        logger.info(f"Ensuring Lakebase schema exists: {schema}")
        
        with engine.connect() as conn:
            # Create schema if it doesn't exist
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            conn.commit()
            logger.info(f"Schema '{schema}' ready")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Seed default profile if database is empty
    _seed_default_profile_if_empty()


def _seed_default_profile_if_empty():
    """Seed a default profile if no profiles exist in the database.
    
    This ensures the app works out-of-the-box on first deployment without
    requiring manual database seeding.
    """
    # Import here to avoid circular imports
    from src.database.models import (
        ConfigAIInfra,
        ConfigMLflow,
        ConfigProfile,
        ConfigPrompts,
    )
    
    with get_db_session() as db:
        # Check if any profiles exist
        existing = db.query(ConfigProfile).first()
        if existing:
            logger.info("Database already has profiles, skipping seed")
            return
        
        logger.info("No profiles found, seeding default profile...")
        
        # Get username for MLflow experiment name
        try:
            from src.core.databricks_client import get_databricks_client
            client = get_databricks_client()
            username = client.current_user.me().user_name
        except Exception:
            username = os.getenv("USER", "default_user")
        
        # Create default profile
        profile = ConfigProfile(
            name="Default Chat",
            description="Standard chat assistant with helpful, informative responses",
            is_default=True,
            created_by="system",
        )
        db.add(profile)
        db.flush()  # Get profile ID
        
        # Create AI infrastructure settings
        ai_infra = ConfigAIInfra(
            profile_id=profile.id,
            llm_endpoint="databricks-claude-sonnet-4-5",  # Default Databricks Foundation Model
            llm_temperature=0.7,
            llm_max_tokens=2048,
        )
        db.add(ai_infra)
        
        # Create MLflow settings
        experiment_name = f"/Users/{username}/chat-template-experiments"
        mlflow_config = ConfigMLflow(
            profile_id=profile.id,
            experiment_name=experiment_name,
        )
        db.add(mlflow_config)
        
        # Create prompts settings
        prompts = ConfigPrompts(
            profile_id=profile.id,
            system_prompt="""You are a helpful AI assistant powered by Databricks. You provide clear,
accurate, and concise responses to user questions.

Format your responses using markdown for better readability:
- Use **bold** for emphasis
- Use bullet points for lists
- Use code blocks for code snippets
- Use headings to organize longer responses

Be friendly, professional, and helpful.""",
            user_prompt_template="{question}",
        )
        db.add(prompts)
        
        db.commit()
        logger.info(f"Default profile created successfully (id={profile.id})")
