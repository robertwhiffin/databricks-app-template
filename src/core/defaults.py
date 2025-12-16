"""Default configuration values for initial setup.

These are used when creating new profiles if no source profile is specified.
"""

DEFAULT_CONFIG = {
    "llm": {
        "endpoint": "databricks-claude-sonnet-4-5",
        "temperature": 0.7,
        "max_tokens": 2048,
    },
    "mlflow": {
        "experiment_name": "/Workspace/Users/{username}/chat-template-experiments",
    },
    "prompts": {
        "system_prompt": """You are a helpful AI assistant powered by Databricks. You provide clear, accurate, and concise responses to user questions.

Format your responses using markdown for better readability:
- Use **bold** for emphasis
- Use bullet points for lists
- Use code blocks with syntax highlighting for code snippets
- Use headings to organize longer responses

Be friendly, professional, and helpful. If you don't know something, admit it rather than making up information.""",
        "user_prompt_template": "{question}",
    },
}
