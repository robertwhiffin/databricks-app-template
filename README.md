# Databricks Chat App Template

A production-ready chat application template for Databricks with full infrastructure for building conversational AI applications.

## What's Included

This template provides enterprise-grade infrastructure out of the box:

### 🏗️ **Production Infrastructure**
- **Multi-user session management** with Lakebase persistence
- **Database-backed configuration** with hot-reload (no app restarts needed)
- **Automated deployment** to Databricks Apps with CLI tool
- **Development scripts** for local setup (`./start_app.sh`, `./stop_app.sh`)
- **Lakebase integration** with automatic instance creation and permissions
- **MLflow tracing** for observability
- **SSE streaming** with polling fallback for Databricks Apps
- **Profile management** UI for different AI configurations

### 🤖 **Direct Model Serving Integration**
- Clean wrapper around Databricks model serving endpoints (no LangChain complexity)
- Support for any chat model endpoint (Foundation Models or custom)
- Streaming responses ready
- Easy to customize and extend

### 📦 **Developer Experience**
- One-command setup for macOS (`./quickstart/setup.sh`)
- Automatic PostgreSQL setup for local development
- Frontend React app with TypeScript and Tailwind CSS
- Comprehensive error handling and logging
- Type-safe API with Pydantic validation

---

## Quick Start

### Prerequisites

- macOS (automated setup) or Linux/Windows (manual steps)
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (installed automatically on macOS)
- Databricks workspace with Apps enabled

### Local Development (macOS)

```bash
# 1. Clone and enter the directory
cd databricks-chat-app

# 2. Copy environment file and configure
cp .env.example .env
# Edit .env with your DATABRICKS_HOST and DATABRICKS_TOKEN

# 3. Run automated setup
./quickstart/setup.sh

# 4. Start the application
./start_app.sh

# 5. Open http://localhost:3000

# 6. Stop when done
./stop_app.sh
```

The setup script will:
- Install system dependencies (Homebrew, Python, PostgreSQL, Node.js)
- Create Python virtual environment
- Initialize PostgreSQL database
- Install frontend dependencies

### Deploy to Databricks

```bash
# 1. Copy deployment configuration
cp config/deployment.example.yaml config/deployment.yaml

# 2. Edit deployment.yaml with your workspace details

# 3. Deploy to development
./deploy.sh create --env development --profile my-profile

# Or update existing deployment
./deploy.sh update --env development --profile my-profile

# Validate before deploying
./deploy.sh create --env staging --profile my-profile --dry-run
```

---

## Architecture

```
┌────────────────────────────────────────────────────┐
│  Frontend (React + TypeScript + Vite)             │
│  └─ Chat UI with message history                  │
└────────────────┬───────────────────────────────────┘
                 │ REST API
┌────────────────▼───────────────────────────────────┐
│  Backend (FastAPI + Python)                        │
│  ├─ ChatModel: Direct model serving wrapper       │
│  ├─ SessionManager: Multi-user session management │
│  └─ ProfileService: Configuration management      │
└────────────────┬───────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────┐
│  Databricks Platform                               │
│  ├─ Model Serving Endpoint (LLM)                   │
│  ├─ Lakebase (session/config persistence)        │
│  └─ MLflow (tracing and observability)            │
└────────────────────────────────────────────────────┘
```

**Key Components:**
- **ChatModel** (`src/services/chat_model.py`): Clean wrapper for model serving - easy to customize
- **SessionManager** (`src/api/services/session_manager.py`): Database-backed session persistence
- **ProfileService** (`src/services/profile_service.py`): Hot-reloadable configuration
- **Settings** (`src/core/settings_db.py`): Database-first configuration (YAML seeds initial state)

---

## Project Structure

```
databricks-chat-app/
├── src/
│   ├── api/              # FastAPI application
│   │   ├── routes/       # API endpoints
│   │   ├── schemas/      # Pydantic models
│   │   └── services/     # Business logic
│   ├── core/             # Infrastructure (database, settings, clients)
│   ├── database/models/  # SQLAlchemy ORM models
│   ├── services/         # Chat model and configuration services
│   └── utils/            # Logging, error handling
├── frontend/             # React + TypeScript application
├── config/               # YAML configuration files
├── scripts/              # Database initialization scripts
├── quickstart/           # Setup automation
├── db_app_deployment/    # Databricks deployment CLI
└── tests/                # Unit and integration tests
```

---

## Customization Guide

### Replace the Chat Logic

The template uses a simple pattern that's easy to customize:

**1. Update the model serving endpoint:**

Edit `config/seed_profiles.yaml`:
```yaml
ai_infra:
  llm_endpoint: "your-custom-endpoint-name"
```

**2. Customize the system prompt:**

Edit `config/prompts.yaml`:
```yaml
system_prompt: |
  Your custom prompt here...
```

**3. Modify the chat model (advanced):**

Edit `src/services/chat_model.py` to add custom logic:
- Pre-processing user messages
- Post-processing model responses
- Adding RAG integration
- Implementing function calling

**4. Update the UI:**

Customize `frontend/src/components/` to match your needs.

### Example: Add RAG

```python
# src/services/chat_model.py

async def generate_with_context(self, messages, documents):
    """Generate response with RAG context."""
    # Add retrieved documents to context
    context_msg = {
        "role": "system",
        "content": f"Context: {documents}"
    }
    messages.insert(1, context_msg)

    return await self.generate(messages)
```

### Example: Add Function Calling

```python
# src/services/chat_model.py

async def generate_with_tools(self, messages, available_tools):
    """Generate response with function calling."""
    # Your tool-calling logic here
    pass
```

---

## Configuration

### Environment Variables

```bash
# Required
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...your-token

# Database (local development)
DATABASE_URL=postgresql://localhost:5432/chat_template

# Optional
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### Database-Backed Settings

All configuration is stored in the database for hot-reload:
- **Profiles**: Different LLM configurations
- **AI Infrastructure**: Model endpoints, parameters
- **MLflow**: Experiment tracking settings
- **Prompts**: System and user prompt templates

Manage via:
- UI: Settings page in the app
- API: `/api/settings/*` endpoints
- Database: Direct SQL queries

### YAML Configuration

YAML files in `config/` seed the initial database state:
- `seed_profiles.yaml` - Initial profiles
- `prompts.yaml` - Default prompts
- `config.yaml` - Default settings
- `deployment.yaml` - Deployment configurations

---

## Development Commands

```bash
# Backend (from project root)
source .venv/bin/activate
uvicorn src.api.main:app --reload --port 8000

# Frontend (from frontend/)
npm run dev           # Development server
npm run build         # Production build
npm run lint          # Lint TypeScript

# Database
python scripts/init_database.py    # Initialize/seed database
psql -d chat_template              # Connect to local database

# Tests
pytest                             # All tests
pytest tests/unit/                 # Unit tests only
pytest -m "not integration"        # Skip integration tests
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `DATABRICKS_HOST not set` | Create `.env` file with Databricks credentials |
| `Database connection failed` | Run `./quickstart/setup_database.sh` |
| `Port already in use` | Run `./stop_app.sh` to kill existing processes |
| Deployment fails | Run with `--dry-run` to validate configuration |

For more help, see [TEMPLATE_GUIDE.md](TEMPLATE_GUIDE.md).

---

## Tech Stack

**Backend:**
- Python 3.10+, FastAPI, SQLAlchemy
- Databricks SDK, MLflow
- PostgreSQL (local) / Lakebase (production)

**Frontend:**
- React 18, TypeScript, Vite
- Tailwind CSS

**Infrastructure:**
- Databricks Apps, Lakebase, Model Serving

---

## License

MIT License - feel free to use this template for your projects!

---

## What's Next?

- ✨ Customize the chat model for your use case
- 🔧 Add RAG, function calling, or other AI features
- 🎨 Customize the UI to match your branding
- 🚀 Deploy to Databricks and share with your team

Happy building! 🎉
