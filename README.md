# Databricks Chat App Template

A production-ready chat application template for Databricks with multi-user session management and a simple built-in UI.

## What's Included

This template provides enterprise-grade infrastructure out of the box:

### 🏗️ **Production Infrastructure**
- **Multi-user session management** with Lakebase persistence
- **Environment-based configuration** (no database config needed)
- **Automated deployment** to Databricks Apps with CLI tool
- **Development scripts** for local setup (`./start_app.sh`, `./stop_app.sh`)
- **Lakebase integration** with automatic schema creation
- **Built-in chat UI** - no frontend build required

### 🤖 **Direct Model Serving Integration**
- Clean wrapper around Databricks model serving endpoints (no LangChain complexity)
- Support for any chat model endpoint (Foundation Models or custom)
- Streaming responses ready
- Easy to customize and extend

### 📦 **Developer Experience**
- One-command setup for macOS (`./quickstart/setup.sh`)
- Automatic PostgreSQL setup for local development
- Comprehensive error handling and logging
- Type-safe API with Pydantic validation

---

## Quick Start

### Prerequisites

- macOS (automated setup) or Linux/Windows (manual steps)
- Python 3.10+
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

# 5. Open http://localhost:8000

# 6. Stop when done
./stop_app.sh
```

The setup script will:
- Install system dependencies (Homebrew, Python, PostgreSQL)
- Create Python virtual environment
- Initialize PostgreSQL database

### Deploy to Databricks

```bash
# 1. Copy deployment configuration
cp config/deployment.example.yaml config/deployment.yaml

# 2. Edit deployment.yaml with your workspace details
#    - Update workspace_path with your email
#    - Update permissions with your email
#    - Optionally change LLM_ENDPOINT

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
│  Built-in Chat UI (HTML/CSS/JS)                   │
│  └─ Simple chat interface with session management │
└────────────────┬───────────────────────────────────┘
                 │ REST API
┌────────────────▼───────────────────────────────────┐
│  Backend (FastAPI + Python)                        │
│  ├─ ChatModel: Direct model serving wrapper       │
│  └─ SessionManager: Multi-user session management │
└────────────────┬───────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────┐
│  Databricks Platform                               │
│  ├─ Model Serving Endpoint (LLM)                   │
│  └─ Lakebase (session persistence)                │
└────────────────────────────────────────────────────┘
```

**Key Components:**
- **ChatModel** (`src/services/chat_model.py`): Clean wrapper for model serving - easy to customize
- **SessionManager** (`src/api/services/session_manager.py`): Database-backed session persistence
- **Settings** (`src/core/settings.py`): Environment-based configuration

---

## Project Structure

```
databricks-chat-app/
├── src/
│   ├── api/              # FastAPI application
│   │   ├── routes/       # API endpoints
│   │   ├── schemas/      # Pydantic models
│   │   ├── services/     # Business logic (SessionManager)
│   │   └── static/       # Built-in chat UI
│   ├── core/             # Infrastructure (database, settings, clients)
│   ├── database/models/  # SQLAlchemy ORM models (sessions only)
│   ├── services/         # Chat model service
│   └── utils/            # Logging, error handling
├── config/               # Deployment configuration
├── scripts/              # Database initialization scripts
├── quickstart/           # Setup automation
├── db_app_deployment/    # Databricks deployment CLI
└── tests/                # Unit and integration tests
```

---

## Configuration

### Environment Variables

All configuration is done via environment variables:

```bash
# Required for local development
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...your-token

# Database (local development)
DATABASE_URL=postgresql://localhost:5432/chat_template

# LLM Configuration
LLM_ENDPOINT=databricks-claude-sonnet-4-5    # Model serving endpoint
LLM_TEMPERATURE=0.7                           # Sampling temperature (0.0-2.0)
LLM_MAX_TOKENS=2048                           # Maximum response tokens

# Optional
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### Deployment Configuration

Edit `config/deployment.yaml` to configure:
- App name and workspace path
- Permissions (who can access the app)
- Environment variables for the deployed app
- Lakebase database settings

---

## Customization Guide

### Change the LLM Endpoint

Set the `LLM_ENDPOINT` environment variable in your deployment config:

```yaml
env_vars:
  LLM_ENDPOINT: "your-custom-endpoint-name"
```

Available Databricks Foundation Model endpoints:
- `databricks-claude-sonnet-4-5`
- `databricks-meta-llama-3-1-70b-instruct`
- `databricks-meta-llama-3-1-405b-instruct`
- `databricks-dbrx-instruct`
- `databricks-mixtral-8x7b-instruct`

### Customize the System Prompt

Set the `SYSTEM_PROMPT` environment variable, or edit the default in `src/core/settings.py`.

### Modify the Chat Model (Advanced)

Edit `src/services/chat_model.py` to add custom logic:
- Pre-processing user messages
- Post-processing model responses
- Adding RAG integration
- Implementing function calling

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

### Customize the UI

Edit `src/api/static/index.html` to customize the chat interface. It's a single HTML file with embedded CSS and JavaScript - no build step required.

---

## Databricks Apps Reverse Proxy Timeout

⚠️ **Important for Production:** Databricks Apps uses a reverse proxy with a ~60 second timeout. If your LLM calls take longer than this, requests will fail even though processing continues in the background.

### Current Behavior

This template uses a simple synchronous request/response pattern. For most chat interactions with fast models, this works fine. However, if you're using:
- Slower models (e.g., 405B parameter models)
- Complex prompts with long responses
- RAG with large context retrieval

...you may hit the reverse proxy timeout.

### Solution: Polling Pattern

For long-running LLM calls, implement a polling pattern where:
1. Client submits a job and gets back a `job_id` immediately
2. Server processes the job in a background worker
3. Client polls for status until complete

Here's a minimal example:

```python
import asyncio
import uuid
from typing import Any, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# In-memory store (use database in production)
job_queue: asyncio.Queue = asyncio.Queue()
jobs: Dict[str, Dict[str, Any]] = {}

class ChatJobRequest(BaseModel):
    message: str
    session_id: str

# Background worker processes jobs from queue
async def worker():
    while True:
        job_id, payload = await job_queue.get()
        jobs[job_id]["status"] = "running"
        try:
            # Your long-running LLM call here
            result = await call_llm(payload["message"])
            jobs[job_id]["status"] = "done"
            jobs[job_id]["result"] = result
        except Exception as exc:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = str(exc)
        finally:
            job_queue.task_done()

# Start worker on app startup
@app.on_event("startup")
async def startup():
    app.state.worker_task = asyncio.create_task(worker())

@app.on_event("shutdown")
async def shutdown():
    app.state.worker_task.cancel()

# Submit job - returns immediately with job_id
@app.post("/api/chat/async")
async def submit_chat_job(req: ChatJobRequest):
    job_id = uuid.uuid4().hex
    jobs[job_id] = {"status": "pending", "result": None, "error": None}
    await job_queue.put((job_id, req.model_dump()))
    return {"job_id": job_id, "status": "pending"}

# Poll for job status/result
@app.get("/api/chat/jobs/{job_id}")
async def get_job_status(job_id: str):
    meta = jobs.get(job_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **meta}
```

**Frontend polling:**

```javascript
async function sendMessageAsync(message, sessionId) {
    // 1. Submit job
    const submitRes = await fetch('/api/chat/async', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message, session_id: sessionId})
    });
    const {job_id} = await submitRes.json();
    
    // 2. Poll until complete
    while (true) {
        await new Promise(r => setTimeout(r, 1000)); // Wait 1 second
        const statusRes = await fetch(`/api/chat/jobs/${job_id}`);
        const job = await statusRes.json();
        
        if (job.status === 'done') {
            return job.result;
        } else if (job.status === 'error') {
            throw new Error(job.error);
        }
        // else: still pending/running, continue polling
    }
}
```

**Note:** This template includes database models for job tracking (`ChatRequest` table) that you can use instead of in-memory storage. See `src/api/services/session_manager.py` for `create_chat_request()`, `update_chat_request_status()`, and `get_chat_request()` methods.

---

## Development Commands

```bash
# Backend (from project root)
source .venv/bin/activate
uvicorn src.api.main:app --reload --port 8000

# Database
python scripts/init_database.py    # Initialize database tables
psql -d chat_template              # Connect to local database

# Tests
pytest                             # All tests
pytest tests/unit/                 # Unit tests only
```

---

## Multi-User Testing

The built-in UI supports testing multi-user behavior:

1. Open the app in multiple browser tabs
2. Each tab gets a unique session ID (shown in header)
3. Use "New Session" to start fresh in any tab
4. Watch different conversations happen in parallel
5. Sessions persist in the database

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `DATABRICKS_HOST not set` | Create `.env` file with Databricks credentials |
| `Database connection failed` | Run `./quickstart/setup_database.sh` |
| `Port already in use` | Run `./stop_app.sh` to kill existing processes |
| Deployment fails | Run with `--dry-run` to validate configuration |
| Chat hangs | Check LLM_ENDPOINT is valid in your workspace |

---

## Tech Stack

**Backend:**
- Python 3.10+, FastAPI, SQLAlchemy
- Databricks SDK
- PostgreSQL (local) / Lakebase (production)

**Frontend:**
- Built-in HTML/CSS/JS (no build required)

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
