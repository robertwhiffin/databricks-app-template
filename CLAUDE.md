# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Databricks Chat App Template**: A production-ready foundation for building conversational AI applications on Databricks. Features direct model serving integration (no LangChain), multi-user sessions, environment-based configuration, and automated deployment.

**Stack**: Python 3.10 (FastAPI, SQLAlchemy), Databricks SDK, PostgreSQL/Lakebase, Built-in HTML/CSS/JS UI

## Essential Commands

### Local Development

```bash
# Setup (macOS automated)
cp .env.example .env  # Configure DATABRICKS_HOST and DATABRICKS_TOKEN
./quickstart/setup.sh

# Start/stop
./start_app.sh        # Backend: :8000
./stop_app.sh

# Manual backend
source .venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
```

### Testing

```bash
pytest                           # All tests
pytest tests/unit/               # Unit only
pytest -m "not integration"      # Skip integration
pytest --cov=src tests/          # With coverage
```

### Code Quality

```bash
ruff check src/ tests/           # Lint
ruff check --fix src/            # Fix issues
mypy src/                        # Type check
```

### Deploy

```bash
# Databricks deployment
cp config/deployment.example.yaml config/deployment.yaml
./deploy.sh create --env development --profile my-profile
./deploy.sh update --env production --profile prod-profile
./deploy.sh create --env staging --profile my-profile --dry-run
```

### Database

```bash
createdb chat_template           # Create local DB
python scripts/init_database.py  # Initialize schema
psql -d chat_template -c "\dt"   # Check tables
```

## Architecture Overview

### Request Flow

```
User Message (Built-in Chat UI)
    ↓
POST /api/chat (routes/chat.py)
    ↓
ChatModel.generate() (services/chat_model.py)
    - Formats conversation context
    - Calls WorkspaceClient.serving_endpoints.query()
    - No LangChain - direct Databricks SDK calls
    ↓
SessionManager.add_message() (api/services/session_manager.py)
    - Persists to PostgreSQL/Lakebase
    ↓
Response → Chat UI
```

### Backend Structure

- **`src/api/`**: FastAPI routes, schemas (Pydantic), services
- **`src/api/static/`**: Built-in chat UI (single HTML file)
- **`src/services/chat_model.py`**: Direct model serving wrapper - **THIS IS WHERE YOU CUSTOMIZE CHAT LOGIC**
- **`src/core/`**: Database abstraction, Databricks client singleton, settings management
- **`src/core/settings.py`**: Environment-based configuration
- **`src/database/models/`**: SQLAlchemy ORM (sessions only)
- **`src/api/services/session_manager.py`**: Multi-user session CRUD with database persistence

### UI

The chat UI is a single HTML file at `src/api/static/index.html`:
- No build step required
- Embedded CSS and JavaScript
- Session management (each browser tab = unique session)
- "New Session" button to start fresh conversations

## Critical Patterns

### Direct Model Serving (No LangChain)

```python
# src/services/chat_model.py
from src.core.databricks_client import get_databricks_client

class ChatModel:
    async def generate(self, messages):
        # Direct SDK call - easy to customize
        response = await asyncio.to_thread(
            self.client.serving_endpoints.query,
            name=self.settings.llm.endpoint,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response["choices"][0]["message"]["content"]
```

**Key point**: Replace this method to add RAG, function calling, or custom logic.

### Environment-Based Configuration

Settings loaded from environment variables:

```python
# src/core/settings.py
from src.core.settings import get_settings

settings = get_settings()  # Loads from environment
# LLM_ENDPOINT, LLM_TEMPERATURE, LLM_MAX_TOKENS, SYSTEM_PROMPT
```

### Session Persistence

```python
# src/api/services/session_manager.py
session_manager = SessionManager()

# Auto-create on first message
session = session_manager.create_session(user_id="user123")

# Add messages
session_manager.add_message(session_id, role="user", content="Hello")

# Survives app restarts (PostgreSQL/Lakebase)
history = session_manager.get_messages(session_id)
```

### Singleton Databricks Client

```python
# src/core/databricks_client.py
from src.core.databricks_client import get_databricks_client

client = get_databricks_client()  # Thread-safe singleton
```

Never instantiate `WorkspaceClient` directly.

### Multi-Backend Database

```python
# src/core/database.py
# Automatically switches between:
# - PostgreSQL (local: DATABASE_URL)
# - Lakebase (production: PGHOST env var set by Databricks Apps)
from src.core.database import get_db_session

with get_db_session() as db:
    # Works in both environments
    sessions = db.query(UserSession).all()
```

## Common Development Tasks

### Customize Chat Model Behavior

Edit `src/services/chat_model.py`:

```python
async def generate(self, messages, ...):
    # Add custom pre-processing
    messages = self._preprocess(messages)

    # Add RAG context
    if self.use_rag:
        context = await self._retrieve_context(messages[-1]["content"])
        messages.insert(1, {"role": "system", "content": f"Context: {context}"})

    # Call model
    response = await asyncio.to_thread(...)

    # Post-process response
    return self._postprocess(response)
```

### Add New API Endpoint

1. Create route in `src/api/routes/`
2. Define Pydantic schemas in `src/api/schemas/`
3. Add business logic in `src/services/` or `src/api/services/`
4. Register router in `src/api/main.py`

### Debug Issues

1. **Check logs**: Backend logs with `LOG_LEVEL=DEBUG`
2. **Inspect session state**: `SELECT * FROM user_sessions WHERE session_id = '...'`
3. **Database issues**: `psql -d chat_template` to inspect directly

## Environment Configuration

### Required Environment Variables

```bash
# .env file (local development)
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
DATABASE_URL=postgresql://localhost:5432/chat_template

# LLM settings (optional - have defaults)
LLM_ENDPOINT=databricks-claude-sonnet-4-5
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048
```

### Databricks Resources

- **Model Serving Endpoint**: Chat model (Foundation Model API or custom)
- **Lakebase** (production): For session persistence
- **Databricks Apps**: For hosting the application

### Configuration Files

- `config/deployment.yaml`: Databricks App deployment settings (dev/staging/prod)
- `config/deployment.example.yaml`: Template with placeholder values

## Troubleshooting

### "DATABRICKS_HOST not set"
Ensure `.env` exists with valid credentials.

### "Database connection failed"
Run `./quickstart/setup_database.sh` or `createdb chat_template && python scripts/init_database.py`

### "Port already in use"
Run `./stop_app.sh`

### Deployment fails
Run with `--dry-run`: `./deploy.sh create --env dev --profile my-profile --dry-run`

### Model serving errors
- Check `LLM_ENDPOINT` in deployment config
- Verify endpoint is deployed and running in Databricks
- Check model input format matches your endpoint

### Chat hangs or times out
- LLM endpoint may be starting up (cold start)
- Check the endpoint exists in your workspace
- Look at app logs for detailed errors

## Template Customization Guide

This is a **template** - meant to be customized for your use case:

1. **Chat Logic**: Modify `src/services/chat_model.py`
2. **System Prompt**: Set `SYSTEM_PROMPT` env var or edit default in `src/core/settings.py`
3. **UI**: Customize `src/api/static/index.html`
4. **Deployment**: Update `config/deployment.yaml` with your workspace details

The infrastructure (database, sessions, deployment) is production-ready and typically doesn't need changes.

## Testing Notes

- Unit tests mock Databricks connections
- Integration tests require valid `DATABRICKS_HOST` and `DATABRICKS_TOKEN`
- Use `pytest -m "not integration"` to skip integration tests in CI
