# Template Customization Guide

This guide helps you adapt the Databricks Chat App Template for your specific use case.

## Quick Customization Checklist

- [ ] Update app name in `config/deployment.yaml`
- [ ] Configure your model serving endpoint in `config/seed_profiles.yaml`
- [ ] Customize system prompt in `config/prompts.yaml`
- [ ] Update frontend branding in `frontend/src/components/`
- [ ] Add your business logic in `src/services/chat_model.py`
- [ ] Test locally with `./start_app.sh`
- [ ] Deploy to Databricks with `./deploy.sh`

---

## Example Use Cases

### 1. Customer Support Chatbot

**Customize the prompt:**
```yaml
# config/prompts.yaml
system_prompt: |
  You are a customer support agent for Acme Corp. You help customers with:
  - Product questions
  - Order tracking
  - Returns and refunds

  Always be polite, empathetic, and solution-oriented.
```

**Add knowledge retrieval:**
```python
# src/services/chat_model.py
async def generate(self, messages, ...):
    # Search knowledge base
    user_question = messages[-1]["content"]
    kb_results = await self.search_knowledge_base(user_question)

    # Add to context
    if kb_results:
        messages.insert(1, {
            "role": "system",
            "content": f"Relevant docs:\n{kb_results}"
        })

    return await super().generate(messages, ...)
```

### 2. Data Analysis Assistant

**Customize for SQL generation:**
```yaml
# config/prompts.yaml
system_prompt: |
  You are a data analysis assistant. You help users write SQL queries
  and interpret results. You have access to the following tables:
  - customers (id, name, email, created_at)
  - orders (id, customer_id, total, status, order_date)

  Generate valid SQL and explain the results clearly.
```

**Add function calling:**
```python
# src/services/chat_model.py
async def generate_with_sql(self, messages):
    # Generate SQL
    sql_query = await self.generate(messages + [{
        "role": "system",
        "content": "Generate SQL only, no explanation"
    }])

    # Execute query
    results = await self.execute_sql(sql_query)

    # Get explanation
    explanation_messages = messages + [
        {"role": "assistant", "content": f"SQL: {sql_query}"},
        {"role": "system", "content": f"Results: {results}"},
        {"role": "system", "content": "Explain these results"}
    ]

    return await self.generate(explanation_messages)
```

### 3. Code Review Assistant

**Customize for code review:**
```yaml
# config/prompts.yaml
system_prompt: |
  You are a senior software engineer performing code reviews. Focus on:
  - Code quality and best practices
  - Security vulnerabilities
  - Performance issues
  - Readability and maintainability

  Provide specific, actionable feedback with code examples.
```

**Add context from repository:**
```python
# src/services/chat_model.py
async def review_code(self, code, file_path):
    # Get related files for context
    context_files = await self.get_related_files(file_path)

    messages = [
        self.format_system_prompt(),
        {"role": "user", "content": f"Review this code:\n\n```python\n{code}\n```"},
        {"role": "system", "content": f"Related files:\n{context_files}"}
    ]

    return await self.generate(messages)
```

---

## Advanced Features

### Adding RAG (Retrieval-Augmented Generation)

1. **Install vector search library:**
```bash
pip install databricks-vectorsearch
```

2. **Add retrieval method:**
```python
# src/services/chat_model.py
from databricks.vector_search.client import VectorSearchClient

class ChatModel:
    def __init__(self):
        super().__init__()
        self.vs_client = VectorSearchClient()

    async def _retrieve_context(self, query):
        results = self.vs_client.get_index(
            endpoint_name="my_endpoint",
            index_name="my_index"
        ).similarity_search(
            query_text=query,
            columns=["content"],
            num_results=5
        )
        return "\n".join([r["content"] for r in results["result"]["data_array"]])
```

3. **Use in generation:**
```python
async def generate(self, messages, use_rag=True):
    if use_rag:
        query = messages[-1]["content"]
        context = await self._retrieve_context(query)
        messages.insert(1, {
            "role": "system",
            "content": f"Context:\n{context}"
        })

    return await super().generate(messages)
```

### Adding Streaming

The template includes streaming support ready to use:

```python
# Backend already has this
async for chunk in chat_model.generate_stream(messages):
    yield f"data: {chunk}\n\n"
```

Frontend updates needed:
```typescript
// frontend/src/services/api.ts
const eventSource = new EventSource('/api/chat/stream');
eventSource.onmessage = (event) => {
    const chunk = event.data;
    // Update UI with chunk
};
```

### Adding Authentication

1. **Add auth middleware:**
```python
# src/api/main.py
from fastapi import Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/api/chat")
async def chat(token: str = Security(security)):
    # Verify token with Databricks or your auth provider
    user = verify_token(token)
    ...
```

2. **Update frontend:**
```typescript
// frontend/src/services/api.ts
const token = await getAuthToken();
headers: {
    'Authorization': `Bearer ${token}`
}
```

---

## Deployment Best Practices

### Development → Staging → Production

1. **Development**: Test changes locally and in dev environment
```bash
./deploy.sh update --env development --profile dev
```

2. **Staging**: Test with realistic data and load
```bash
./deploy.sh update --env staging --profile staging
```

3. **Production**: Deploy to users
```bash
./deploy.sh update --env production --profile prod
```

### Monitoring

- **MLflow**: Check traces in Databricks MLflow UI
- **Logs**: View in Databricks Apps logs tab
- **Metrics**: Add custom metrics to MLflow spans

```python
import mlflow
with mlflow.start_span(name="chat_generation") as span:
    response = await chat_model.generate(messages)
    span.set_attribute("response_length", len(response))
```

### Performance Tuning

- **Database connection pool**: Adjust in `src/core/database.py`
- **Model parameters**: Tune temperature, max_tokens in profiles
- **Caching**: Add caching layer for common queries

---

## Common Questions

**Q: Can I use a different database?**
A: Yes! Modify `src/core/database.py` to support your database. The template uses SQLAlchemy, so most SQL databases work.

**Q: Can I deploy outside Databricks?**
A: Yes, but you'll lose Lakebase integration. Deploy to any platform that supports Docker or Python apps. You'll need to handle authentication differently.

**Q: How do I add file uploads?**
A: Add multipart form handling in FastAPI:
```python
from fastapi import UploadFile

@router.post("/upload")
async def upload_file(file: UploadFile):
    content = await file.read()
    # Process file
```

**Q: Can I use a different frontend framework?**
A: Yes! The backend API is framework-agnostic. Replace the React frontend with Vue, Angular, or any framework.

**Q: How do I handle rate limiting?**
A: Add rate limiting middleware:
```python
from slowapi import Limiter
limiter = Limiter(key_func=lambda: "global")

@router.post("/chat")
@limiter.limit("10/minute")
async def chat(...):
    ...
```

---

## Support

- **Issues**: Check troubleshooting in README.md
- **Customization**: This guide and CLAUDE.md
- **Databricks Docs**: https://docs.databricks.com/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

---

## Contributing

This is a template - customize it for your needs! If you build something cool, consider sharing your modifications with the community.
