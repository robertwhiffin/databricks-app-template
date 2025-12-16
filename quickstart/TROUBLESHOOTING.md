# Troubleshooting Guide

Common issues and solutions for the Databricks Chat Template.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Database Issues](#database-issues)
- [Databricks Connection Issues](#databricks-connection-issues)
- [Frontend Issues](#frontend-issues)
- [Backend Issues](#backend-issues)
- [Performance Issues](#performance-issues)

---

## Installation Issues

### "No .env file found" Warning

**Problem:** Application can't find environment configuration.

**Solution:**
```bash
# Copy template and edit
cp .env.example .env
nano .env  # Add your Databricks credentials
```

### "Virtual environment not found"

**Problem:** Python virtual environment hasn't been created.

**Solution:**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Database Issues

### "Database connection failed"

**Problem:** Can't connect to PostgreSQL database.

**Diagnosis:**
```bash
# Check if PostgreSQL is running
pg_isready

# Check if database exists
psql -l | grep chat_template

# Test connection manually
psql -d chat_template -c "\conninfo"
```

**Solutions:**

**1. PostgreSQL not running:**
```bash
# macOS
brew services start postgresql@14

# Linux
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Start on boot
```

**2. Database doesn't exist:**
```bash
# Run setup script
./quickstart/setup_database.sh

# Or manually
createdb chat_template
```

**3. Permission issues:**
```bash
# Create PostgreSQL user (if needed)
createuser -s $(whoami)

# Or with sudo (Linux)
sudo -u postgres createuser -s $(whoami)
```

**4. Wrong DATABASE_URL:**
Check `.env` file has correct format:
```
DATABASE_URL=postgresql://localhost:5432/chat_template
```

### "Default profile already exists"

**Problem:** Database already initialized.

**Solution:** This is normal! The database is already set up. If you need to reset:
```bash
# Reset database (WARNING: deletes all data)
dropdb chat_template
./quickstart/setup_database.sh
```

---

## Databricks Connection Issues

### "DATABRICKS_HOST and DATABRICKS_TOKEN environment variables not set"

**Problem:** Missing Databricks credentials.

**Solution:**

1. **Check .env file exists:**
   ```bash
   ls -la .env
   cat .env
   ```

2. **Verify values are set correctly:**
   ```bash
   # .env should contain (no quotes):
   DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
   DATABRICKS_TOKEN=dapi...your-token-here
   ```

3. **Test credentials:**
   ```bash
   source .env
   curl -H "Authorization: Bearer $DATABRICKS_TOKEN" \
        "$DATABRICKS_HOST/api/2.0/clusters/list"
   ```

### "DATABRICKS_HOST should start with https://"

**Problem:** Invalid workspace URL format.

**Solution:** Ensure your `.env` has:
```bash
# Correct
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com

# Wrong
DATABRICKS_HOST=your-workspace.cloud.databricks.com
DATABRICKS_HOST=http://your-workspace.cloud.databricks.com
```

### "Authentication failed"

**Problem:** Invalid or expired Databricks token.

**Solution:**

1. **Generate new token:**
   - Go to Databricks workspace
   - Click User icon - Settings
   - Developer - Access Tokens
   - Generate New Token
   - Copy and update `.env`

2. **Check token format:**
   - Should start with `dapi`
   - No spaces or quotes
   - Full token copied

### "Model serving endpoint not found"

**Problem:** Configured LLM endpoint doesn't exist or you don't have access.

**Solution:**

1. **Verify endpoint exists:**
   - Go to Databricks workspace
   - Navigate to Serving - Model Serving
   - Confirm endpoint name matches configuration

2. **Check configuration:**
   ```bash
   psql -d chat_template -c "SELECT llm_endpoint FROM config_ai_infra;"
   ```

3. **Update endpoint:**
   - Use Settings UI in the application
   - Or update database directly

---

## Frontend Issues

### "Frontend won't start"

**Problem:** npm/node issues.

**Solution:**
```bash
cd frontend

# Clear and reinstall
rm -rf node_modules package-lock.json
npm install

# Try starting
npm run dev
```

### "Port 3000 already in use"

**Problem:** Another process using port 3000.

**Solution:**
```bash
# Find and kill process
lsof -ti:3000 | xargs kill -9

# Or use different port
cd frontend
npm run dev -- --port 3001
```

### "Failed to fetch from backend"

**Problem:** Frontend can't reach backend API.

**Diagnosis:**
```bash
# Check backend is running
curl http://localhost:8000/api/health

# Check backend logs
tail -f logs/backend.log
```

**Solutions:**

1. **Backend not running:**
   ```bash
   ./start_app.sh
   ```

2. **CORS issues:**
   Check `src/api/main.py` has correct CORS configuration

3. **Wrong API URL:**
   Check `frontend/.env` or `vite.config.ts`

### "Chat messages not appearing"

**Problem:** WebSocket or API issues.

**Solutions:**

1. **Check browser console** for JavaScript errors
2. **Check network tab** for failed API requests
3. **Verify backend logs** for errors
4. **Restart the application**

---

## Backend Issues

### "Port 8000 already in use"

**Problem:** Another process using port 8000.

**Solution:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or start on different port
source .venv/bin/activate
uvicorn src.api.main:app --reload --port 8001
```

### "Import errors" or "Module not found"

**Problem:** Dependencies not installed or virtual environment not activated.

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Verify it's activated (should show .venv in prompt)
which python

# Reinstall dependencies
pip install -r requirements.txt
```

### "MLflow connection errors"

**Problem:** MLflow tracking issues.

**Solution:**

1. **Check MLflow configuration:**
   ```bash
   psql -d chat_template -c "SELECT experiment_name FROM config_mlflow;"
   ```

2. **Verify experiment path exists** in Databricks workspace

3. **Test MLflow connection:**
   ```bash
   source .venv/bin/activate
   python -c "import mlflow; print(mlflow.get_tracking_uri())"
   ```

### "LLM generation timeout"

**Problem:** Model serving calls taking too long.

**Solutions:**

1. **Check model endpoint** is running in Databricks
2. **Reduce max_tokens** in configuration
3. **Simplify prompt** (less complex requests)
4. **Check backend logs** for specific errors:
   ```bash
   tail -f logs/backend.log
   ```

---

## Performance Issues

### "Slow response times"

**Causes & Solutions:**

1. **Model endpoint latency:**
   - Check Databricks model serving metrics
   - Consider using a different model
   - Reduce max_tokens parameter

2. **Database queries:**
   - Check database connection pooling
   - Run `VACUUM ANALYZE` on PostgreSQL

3. **Network latency:**
   - Verify network connectivity to Databricks
   - Check for proxy/firewall issues

### "High memory usage"

**Solutions:**

1. **Restart application:**
   ```bash
   ./stop_app.sh
   ./start_app.sh
   ```

2. **Clear MLflow artifacts:**
   ```bash
   rm -rf mlruns/
   ```

3. **Check for memory leaks** in logs

### "Database growing large"

**Solution:**
```bash
# Check database size
psql -d chat_template -c "SELECT pg_size_pretty(pg_database_size('chat_template'));"

# Vacuum database
psql -d chat_template -c "VACUUM FULL;"

# Archive old settings history
psql -d chat_template -c "DELETE FROM config_history WHERE timestamp < NOW() - INTERVAL '30 days';"
```

---

## Advanced Debugging

### Enable Debug Logging

**Backend:**
```python
# In src/utils/logging_config.py, change level:
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```typescript
// In src/services/api.ts, add console logs
console.log('API request:', request);
console.log('API response:', response);
```

### Database Query Debugging

```bash
# Connect to database
psql -d chat_template

# Check current profile
SELECT * FROM config_profiles WHERE is_default = true;

# Check all configuration
SELECT p.name, ai.llm_endpoint
FROM config_profiles p
JOIN config_ai_infra ai ON p.id = ai.profile_id;

# View recent settings changes
SELECT * FROM config_history ORDER BY timestamp DESC LIMIT 10;
```

### Network Debugging

```bash
# Test Databricks connection
curl -v -H "Authorization: Bearer $DATABRICKS_TOKEN" \
     "$DATABRICKS_HOST/api/2.0/clusters/list"

# Test backend API
curl -v http://localhost:8000/api/health

# Test chat endpoint
curl -v -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?", "session_id": "test-session"}'
```

---

## Getting More Help

If you're still stuck:

1. **Check logs:**
   - Backend: `logs/backend.log`
   - Frontend: `logs/frontend.log`
   - Browser console (F12)

2. **Run tests:**
   ```bash
   source .venv/bin/activate
   pytest -v
   ```

3. **Verify installation:**
   ```bash
   # Check all services
   ./start_app.sh
   curl http://localhost:8000/api/health
   curl http://localhost:3000
   ```

4. **Review documentation:**
   - [README.md](../README.md)
   - [CLAUDE.md](../CLAUDE.md)

5. **Open an issue** on GitHub with:
   - Error messages
   - Relevant logs
   - Steps to reproduce
   - Environment details (OS, Python version, etc.)
