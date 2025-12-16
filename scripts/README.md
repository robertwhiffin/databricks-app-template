# Scripts

Utility scripts for the Databricks Chat Template.

## `init_database.py`

Initialize the PostgreSQL database with seed profiles from YAML.

```bash
source .venv/bin/activate
python scripts/init_database.py
```

**What it does:**
1. Creates database tables (if they don't exist)
2. Loads profiles from `config/seed_profiles.yaml`
3. Creates config records (AI settings, MLflow, prompts)

**Prerequisites:**
- PostgreSQL running with `chat_template` database created
- `.env` file with `DATABASE_URL` configured
- `config/seed_profiles.yaml` exists

**Idempotent:** Safe to run multiple times - skips if profiles already exist.

---

## Seed Profiles

Profiles are defined in `config/seed_profiles.yaml`:

```yaml
profiles:
  - name: "Default"
    description: "Default configuration"
    is_default: true
    ai_infra:
      llm_endpoint: "databricks-claude-sonnet-4-5"
      llm_temperature: 0.7
      llm_max_tokens: 4096
    mlflow:
      experiment_name: "/Users/{username}/chat-template"
    prompts:
      system_prompt: "..."
      user_prompt_template: "..."
```

The `{username}` placeholder is replaced with the current Databricks user.
