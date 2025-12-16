# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Databricks Chat App Template**: A production-ready foundation for building conversational AI applications on Databricks. Features direct model serving integration (no LangChain), multi-user sessions, database-backed configuration, and automated deployment.

**Stack**: Python 3.10 (FastAPI, SQLAlchemy), React 18 (TypeScript, Vite, Tailwind), Databricks SDK, PostgreSQL/Lakebase

## Essential Commands

### Local Development

```bash
# Setup (macOS automated)
cp .env.example .env  # Configure DATABRICKS_HOST and DATABRICKS_TOKEN
./quickstart/setup.sh

# Start/stop
./start_app.sh        # Backend: :8000, Frontend: :3000
./stop_app.sh

# Manual backend
source .venv/bin/activate
uvicorn src.api.main:app --reload --port 8000

# Manual frontend
cd frontend && npm run dev
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
cd frontend && npm run lint      # Frontend lint
```

### Build & Deploy

```bash
cd frontend && npm run build     # Frontend: frontend/dist/

# Databricks deployment
cp config/deployment.example.yaml config/deployment.yaml
./deploy.sh create --env development --profile my-profile
./deploy.sh update --env production --profile prod-profile
./deploy.sh create --env staging --profile my-profile --dry-run
```

### Database

```bash
createdb chat_template           # Create local DB
python scripts/init_database.py  # Initialize schema and seed profiles
psql -d chat_template -c "\dt"   # Check tables
```

## Architecture Overview

### Request Flow

```
User Message (Frontend)
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
Response → Frontend
```

### Backend Structure

- **`src/api/`**: FastAPI routes, schemas (Pydantic), services
- **`src/services/chat_model.py`**: Direct model serving wrapper - **THIS IS WHERE YOU CUSTOMIZE CHAT LOGIC**
- **`src/core/`**: Database abstraction, Databricks client singleton, settings management
- **`src/database/models/`**: SQLAlchemy ORM (sessions, profiles, config)
- **`src/api/services/session_manager.py`**: Multi-user session CRUD with database persistence

### Frontend Structure

- **`frontend/src/components/ChatPanel/`**: Chat UI components
- **`frontend/src/components/config/`**: Profile and settings management UI
- **`frontend/src/contexts/`**: ProfileContext, SessionContext (React Context API)
- **`frontend/src/services/api.ts`**: All backend API calls
- **`frontend/src/types/`**: TypeScript interfaces

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

### Database-Backed Configuration

Settings stored in database, hot-reload without restart:

```python
# src/core/settings_db.py
from src.core.settings_db import get_settings

settings = get_settings()  # Loads from database
# Changes via UI or API immediately affect next request
```

YAML files (`config/*.yaml`) only seed initial state. Database is source of truth.

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
5. Add frontend call in `frontend/src/services/api.ts`
6. Update TypeScript types in `frontend/src/types/`

### Add Configuration Option

1. Add field to database model in `src/database/models/`
2. Update seed profiles in `config/seed_profiles.yaml`
3. Update settings service in `src/core/settings_db.py`
4. Add UI in `frontend/src/components/config/`
5. Run `python scripts/init_database.py` to update schema

### Debug Issues

1. **Check MLflow traces**: Agent execution traced to Databricks MLflow
2. **Inspect session state**: `SELECT * FROM user_sessions WHERE session_id = '...'`
3. **Check logs**: `tail -f logs/backend.log`
4. **Database issues**: `psql -d chat_template` to inspect directly

## Environment Configuration

### Required Environment Variables

```bash
# .env file
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
DATABASE_URL=postgresql://localhost:5432/chat_template
```

### Databricks Resources

- **Model Serving Endpoint**: Chat model (Foundation Model API or custom)
- **Lakebase** (production): For session/config persistence in Unity Catalog
- **MLflow**: For tracing (auto-configured in Databricks)

### Configuration Files

- `config/config.yaml`: LLM endpoint defaults (seeds initial profile)
- `config/prompts.yaml`: System prompts (seeds initial profile)
- `config/seed_profiles.yaml`: Initial configuration profiles
- `config/deployment.yaml`: Databricks App deployment settings (dev/staging/prod)

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
- Check endpoint name in profile settings
- Verify endpoint is deployed and running in Databricks
- Check model input format matches your endpoint

### Frontend build fails
Ensure Node.js 18+ and run `cd frontend && npm install`

## Template Customization Guide

This is a **template** - meant to be customized for your use case:

1. **Chat Logic**: Modify `src/services/chat_model.py`
2. **System Prompts**: Edit `config/prompts.yaml`
3. **UI**: Customize `frontend/src/components/`
4. **Deployment**: Update `config/deployment.yaml` with your workspace details

The infrastructure (database, sessions, deployment) is production-ready and typically doesn't need changes.

## Testing Notes

- Unit tests mock Databricks connections
- Integration tests require valid `DATABRICKS_HOST` and `DATABRICKS_TOKEN`
- Use `pytest -m "not integration"` to skip integration tests in CI
- No live test scripts included (add as needed for your use case)
