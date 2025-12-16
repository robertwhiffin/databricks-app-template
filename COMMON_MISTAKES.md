# Common Mistakes and Solutions

This guide covers the most common issues users encounter when setting up and running the Databricks Chat App Template, along with step-by-step solutions.

---

## Table of Contents

1. [Environment Configuration Errors](#environment-configuration-errors)
2. [Database Connection Issues](#database-connection-issues)
3. [Databricks Authentication Problems](#databricks-authentication-problems)
4. [Model Serving Endpoint Errors](#model-serving-endpoint-errors)
5. [Port Conflicts](#port-conflicts)
6. [Deployment Issues](#deployment-issues)
7. [Runtime Errors](#runtime-errors)

---

## Environment Configuration Errors

### ❌ Problem: `.env` file not found

**Error message:**
```
Error: DATABRICKS_HOST environment variable not set
```

**Why this happens:**
You haven't created a `.env` file yet, or it's in the wrong location.

**✅ Solution:**
```bash
# Step 1: Navigate to project root
cd /path/to/databricks-chat-app

# Step 2: Copy the example file
cp .env.example .env

# Step 3: Edit with your credentials
nano .env  # or use your favorite editor
```

**✅ Verify:**
```bash
# Check file exists
ls -la .env

# Should output: -rw-r--r--  1 user  staff  xxx Dec 10 10:00 .env
```

---

### ❌ Problem: Wrong `DATABRICKS_HOST` format

**Error message:**
```
Error: Invalid workspace URL format
```

**Common mistakes:**

1. **Missing `https://` prefix:**
   ```bash
   ❌ DATABRICKS_HOST=my-workspace.cloud.databricks.com
   ✅ DATABRICKS_HOST=https://my-workspace.cloud.databricks.com
   ```

2. **Using `http://` instead of `https://`:**
   ```bash
   ❌ DATABRICKS_HOST=http://my-workspace.cloud.databricks.com
   ✅ DATABRICKS_HOST=https://my-workspace.cloud.databricks.com
   ```

3. **Trailing slash:**
   ```bash
   ❌ DATABRICKS_HOST=https://my-workspace.cloud.databricks.com/
   ✅ DATABRICKS_HOST=https://my-workspace.cloud.databricks.com
   ```

4. **Using generic databricks.com URL:**
   ```bash
   ❌ DATABRICKS_HOST=https://databricks.com
   ✅ DATABRICKS_HOST=https://my-workspace.cloud.databricks.com
   ```

**How to find your workspace URL:**
1. Log into Databricks
2. Copy URL from browser address bar (everything before `/workspace/`)
3. Example: `https://e2-demo-west.cloud.databricks.com`

---

### ❌ Problem: Invalid `DATABRICKS_TOKEN`

**Error message:**
```
Error: Authentication failed
Error: 401 Unauthorized
```

**Common mistakes:**

1. **Token doesn't start with `dapi`:**
   ```bash
   ❌ DATABRICKS_TOKEN=abc123xyz789
   ✅ DATABRICKS_TOKEN=dapi....
   ```
   All valid Databricks personal access tokens start with `dapi`.

2. **Token copied incorrectly (spaces or newlines):**
   ```bash
   ❌ DATABRICKS_TOKEN=dapi1234 567890abcdef  # Space in middle
   ❌ DATABRICKS_TOKEN=dapi1234
              567890abcdef                    # Newline in middle
   ✅ DATABRICKS_TOKEN=dapi...
   ```

3. **Token expired:**
   Tokens can have expiration dates. Generate a new one if yours expired.

**✅ How to create a valid token:**
1. Databricks UI → Click your username (top right)
2. Settings → Developer → Access Tokens
3. Click "Generate New Token"
4. Comment: "Chat App Development"
5. Lifetime: 90 days (or blank for no expiration)
6. Click "Generate"
7. **COPY IMMEDIATELY** - you won't see it again!
8. Paste into `.env` file

**✅ Test your token:**
```bash
# Using curl
curl -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  "$DATABRICKS_HOST/api/2.0/clusters/list"

# Should return JSON, not "401 Unauthorized"
```

---

## Database Connection Issues

### ❌ Problem: PostgreSQL not installed

**Error message:**
```
Error: Database connection failed
psql: command not found
```

**✅ Solution (macOS):**
```bash
# Install PostgreSQL via Homebrew
brew install postgresql@14

# Start PostgreSQL
brew services start postgresql@14

# Verify it's running
brew services list | grep postgresql
# Should show: postgresql@14  started
```

**✅ Solution (Linux - Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**✅ Verify installation:**
```bash
psql --version
# Should output: psql (PostgreSQL) 14.x
```

---

### ❌ Problem: Database doesn't exist

**Error message:**
```
psycopg2.OperationalError: FATAL: database "databricks_chat_app" does not exist
```

**✅ Solution:**
```bash
# Step 1: Create the database
createdb databricks_chat_app

# Step 2: Verify it was created
psql -l | grep databricks_chat_app
# Should see: databricks_chat_app | user | ...

# Step 3: Initialize schema and seed data
python scripts/init_database.py
```

**✅ Alternative (if createdb doesn't work):**
```bash
# Connect to PostgreSQL
psql postgres

# Inside psql shell:
CREATE DATABASE databricks_chat_app;
\q  # Exit

# Then run init script
python scripts/init_database.py
```

---

### ❌ Problem: PostgreSQL not running

**Error message:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**✅ Check if PostgreSQL is running:**
```bash
# macOS
brew services list | grep postgresql

# Linux
sudo systemctl status postgresql
```

**✅ Start PostgreSQL:**
```bash
# macOS
brew services start postgresql@14

# Linux
sudo systemctl start postgresql
```

**✅ Verify it's listening:**
```bash
# Check if port 5432 is open
lsof -i :5432
# Should show: postgres ... (LISTEN)
```

---

### ❌ Problem: Wrong database URL format

**Error message:**
```
ValueError: Invalid DATABASE_URL format
```

**Common mistakes:**

```bash
❌ DATABASE_URL=localhost:5432/databricks_chat_app
✅ DATABASE_URL=postgresql://localhost:5432/databricks_chat_app

❌ DATABASE_URL=postgres://localhost:5432/databricks_chat_app
✅ DATABASE_URL=postgresql://localhost:5432/databricks_chat_app
   (note: postgresql, not postgres)

❌ DATABASE_URL=postgresql://localhost/databricks_chat_app
✅ DATABASE_URL=postgresql://localhost:5432/databricks_chat_app
   (include port number)
```

---

## Databricks Authentication Problems

### ❌ Problem: Permission denied to query endpoint

**Error message:**
```
Error: User does not have permission to query endpoint 'my-endpoint'
403 Forbidden
```

**Why this happens:**
Your Databricks user/token doesn't have permission to access the model serving endpoint.

**✅ Solution:**
1. Go to Databricks UI → Serving → Serving Endpoints
2. Click on your endpoint
3. Go to "Permissions" tab
4. Add your user with "Can Query" permission
5. Save changes
6. Wait 1-2 minutes for permissions to propagate
7. Try again

**✅ Alternative:** Use a service principal token with proper permissions.

---

### ❌ Problem: Token from wrong workspace

**Error message:**
```
Error: Authentication failed
Error: Token is not valid for this workspace
```

**Why this happens:**
You're using a token generated from a different Databricks workspace.

**✅ Solution:**
1. Make sure `DATABRICKS_HOST` matches the workspace where you created the token
2. If you need to use a different workspace:
   - Log into the correct workspace
   - Generate a NEW token for that workspace
   - Update `.env` with the new token

**⚠️ Remember:** Tokens are workspace-specific. A token from workspace A won't work on workspace B.

---

## Model Serving Endpoint Errors

### ❌ Problem: Endpoint not found

**Error message:**
```
Error: Model serving endpoint 'my-endpoint' not found
404 Not Found
```

**Common causes:**

1. **Typo in endpoint name:**
   ```yaml
   ❌ llm_endpoint: "databricks-meta-llama-3-1-70b"
   ✅ llm_endpoint: "databricks-meta-llama-3-1-70b-instruct"
   ```
   Note the `-instruct` suffix!

2. **Endpoint doesn't exist in your workspace:**
   - Go to Databricks UI → Serving → Serving Endpoints
   - Check if the endpoint exists
   - Copy the EXACT name (case-sensitive)

3. **Wrong workspace:**
   - You're pointing to workspace A but endpoint exists in workspace B

**✅ How to find correct endpoint name:**
```bash
# List all available endpoints
databricks serving-endpoints list --profile my-profile

# Or via UI:
# Databricks → Serving → Serving Endpoints → Copy name
```

**✅ Update configuration:**
```yaml
# config/seed_profiles.yaml
ai_infra:
  llm_endpoint: "exact-endpoint-name-here"  # Copy-paste from UI
```

Then re-run `python scripts/init_database.py` or update via Settings UI.

---

### ❌ Problem: Endpoint is stopped or failed

**Error message:**
```
Error: Endpoint 'my-endpoint' is not ready (current state: STOPPED)
```

**✅ Solution:**
1. Go to Databricks UI → Serving → Serving Endpoints
2. Find your endpoint
3. Check status column:
   - ✅ "Ready" = Good to use
   - ❌ "Stopped" = Click "Start" button
   - ❌ "Failed" = Check error logs, may need to recreate
4. Wait for status to change to "Ready" (may take 1-5 minutes)
5. Try your app again

**⚠️ Note:** Stopped endpoints save compute costs but must be started before use.

---

### ❌ Problem: Endpoint response format doesn't match

**Error message:**
```
ValueError: Unexpected response format from model endpoint
KeyError: 'choices'
```

**Why this happens:**
Different model serving endpoints return different response formats. The template expects OpenAI-compatible format.

**✅ Solution:**

Check the response format in `src/services/chat_model.py` around line 156:

```python
# Current format (OpenAI-compatible):
if "choices" in response:
    return response["choices"][0]["message"]["content"]

# If your endpoint uses a different format, add handling:
elif "predictions" in response:
    return response["predictions"][0]
elif "output" in response:
    return response["output"]["text"]
```

**How to find your endpoint's format:**
1. Databricks UI → Serving → Your Endpoint
2. Click "Query Endpoint" button
3. Send a test request
4. Look at the response structure
5. Update `chat_model.py` to handle that structure

---

## Port Conflicts

### ❌ Problem: Port 8000 already in use

**Error message:**
```
Error: [Errno 48] Address already in use: ('127.0.0.1', 8000)
OSError: [Errno 48] Address already in use
```

**✅ Solution 1: Stop the existing app**
```bash
./stop_app.sh
```

**✅ Solution 2: Kill the process manually**
```bash
# Find process using port 8000
lsof -i :8000

# Output will show PID, then:
kill <PID>

# Or force kill:
kill -9 <PID>
```

**✅ Solution 3: Use a different port**
```bash
# Edit start_app.sh and change port 8000 to 8001
uvicorn src.api.main:app --reload --port 8001

# Update frontend to match:
# frontend/.env: VITE_API_BASE_URL=http://localhost:8001
```

---

### ❌ Problem: Port 3000 already in use

**Error message:**
```
Error: Port 3000 is already in use
```

**✅ Solution 1: Stop the frontend**
```bash
# Find process
lsof -i :3000

# Kill it
kill <PID>
```

**✅ Solution 2: Use different port**
```bash
cd frontend
PORT=3001 npm run dev
```

---

## Deployment Issues

### ❌ Problem: Deployment fails with "App name already exists"

**Error message:**
```
Error: App 'my-chat-app' already exists in environment 'development'
```

**✅ Solution:**

If you want to UPDATE existing app:
```bash
./deploy.sh update --env development --profile my-profile
```

If you want to create a NEW app with different name:
```bash
# Edit config/deployment.yaml
development:
  app_name: "my-chat-app-v2"  # Change name

./deploy.sh create --env development --profile my-profile
```

---

### ❌ Problem: Lakebase instance creation fails

**Error message:**
```
Error: Failed to create Lakebase instance
Permission denied
```

**Common causes:**

1. **No Unity Catalog access:**
   - You need permissions to create catalogs/schemas in Unity Catalog
   - Contact your workspace admin

2. **Catalog name conflict:**
   - Catalog name is already taken
   - Edit `config/deployment.yaml` to use different catalog name

**✅ Solution:**
```yaml
# config/deployment.yaml
development:
  lakebase:
    catalog: "my_unique_catalog_name"  # Change this
    schema: "chat_app"
```

---

### ❌ Problem: Deployment dry-run shows errors

**Error message:**
```
Validation failed: Missing required field 'warehouse_id'
```

**✅ Solution:**
Always run dry-run first to catch configuration issues:

```bash
# Step 1: Dry-run to validate config
./deploy.sh create --env development --profile my-profile --dry-run

# Step 2: Fix any errors shown
# Edit config/deployment.yaml

# Step 3: Dry-run again until no errors
./deploy.sh create --env development --profile my-profile --dry-run

# Step 4: Actually deploy
./deploy.sh create --env development --profile my-profile
```

---

## Runtime Errors

### ❌ Problem: "Module not found" errors

**Error message:**
```
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'databricks'
```

**Why this happens:**
Python dependencies not installed or wrong virtual environment.

**✅ Solution:**
```bash
# Step 1: Activate virtual environment
source .venv/bin/activate

# Step 2: Verify you're in the venv
which python
# Should show: /path/to/project/.venv/bin/python

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: Verify installation
pip list | grep fastapi
pip list | grep databricks
```

**If .venv doesn't exist:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### ❌ Problem: Import errors in Python

**Error message:**
```
ImportError: attempted relative import with no known parent package
ImportError: cannot import name 'ChatModel' from 'src.services'
```

**Why this happens:**
Running Python files directly instead of as a module.

**❌ Wrong way:**
```bash
python src/api/main.py  # Don't do this
```

**✅ Correct way:**
```bash
# Run via uvicorn
uvicorn src.api.main:app --reload

# Or via script
./start_app.sh
```

---

### ❌ Problem: Frontend not loading / blank page

**Possible causes:**

1. **Backend not running:**
   ```bash
   # Check backend
   curl http://localhost:8000/health
   # Should return: {"status":"ok"}
   ```

2. **Frontend not built:**
   ```bash
   cd frontend
   npm run build
   npm run dev
   ```

3. **Wrong API URL:**
   ```bash
   # Check frontend/.env or frontend/.env.local
   VITE_API_BASE_URL=http://localhost:8000
   ```

4. **CORS issues:**
   Check browser console (F12) for CORS errors.
   Backend should allow frontend origin in `src/api/main.py`.

---

## Quick Troubleshooting Checklist

When something isn't working, go through this checklist:

### ✅ Environment Setup
- [ ] `.env` file exists in project root
- [ ] `DATABRICKS_HOST` starts with `https://` (no trailing slash)
- [ ] `DATABRICKS_TOKEN` starts with `dapi`
- [ ] `DATABASE_URL` starts with `postgresql://`

### ✅ Database
- [ ] PostgreSQL is installed: `psql --version`
- [ ] PostgreSQL is running: `brew services list` or `systemctl status postgresql`
- [ ] Database exists: `psql -l | grep databricks_chat_app`
- [ ] Schema initialized: `python scripts/init_database.py`

### ✅ Databricks
- [ ] Can access workspace in browser
- [ ] Token hasn't expired
- [ ] Model serving endpoint exists and is "Ready"
- [ ] Have permission to query endpoint

### ✅ Application
- [ ] Virtual environment activated: `source .venv/bin/activate`
- [ ] Dependencies installed: `pip list | grep fastapi`
- [ ] Backend running: `curl http://localhost:8000/health`
- [ ] Frontend running: `curl http://localhost:3000`
- [ ] No port conflicts: `lsof -i :8000` and `lsof -i :3000`

### ✅ Configuration
- [ ] Profile exists in database: `SELECT * FROM profiles;`
- [ ] Endpoint name is correct in profile
- [ ] MLflow experiment path is valid

---

## Still Having Issues?

If you've tried everything above and still have problems:

1. **Check the logs:**
   ```bash
   # Backend logs
   tail -f logs/backend.log

   # If no logs directory, check console output
   ```

2. **Test individual components:**
   ```bash
   # Test database connection
   psql -d databricks_chat_app -c "SELECT 1;"

   # Test Databricks connection
   python -c "from databricks.sdk import WorkspaceClient; print(WorkspaceClient().current_user.me())"

   # Test model endpoint
   python test_chat_live.py
   ```

3. **Re-run setup:**
   ```bash
   # Nuclear option - start fresh
   ./stop_app.sh
   dropdb databricks_chat_app  # WARNING: Deletes all data!
   createdb databricks_chat_app
   python scripts/init_database.py
   ./start_app.sh
   ```

4. **Check documentation:**
   - `README.md` - Setup guide
   - `TEMPLATE_GUIDE.md` - Customization guide
   - `CLAUDE.md` - Technical details

---

## Reporting Issues

If you find a bug or need help:

1. Check if issue already exists in project issues
2. Gather relevant information:
   - Error message (full stack trace)
   - Steps to reproduce
   - Environment (OS, Python version, etc.)
   - Relevant configuration (redact secrets!)
3. Create a new issue with this information

---

**Remember:** Most issues are configuration problems, not code bugs. Double-check your `.env` file and database setup first!
