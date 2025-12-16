"""Initialize database tables for the chat template.

This script creates the necessary database tables for multi-user session management.
Run this once during local development setup.

Usage:
    python scripts/init_database.py
"""
import os
import sys

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.database import init_db


def initialize_database():
    """Initialize database tables."""
    
    print("Initializing database tables...")
    print("")
    
    try:
        init_db()
        print("✓ Database tables created successfully")
        print("")
        print("Tables created:")
        print("  - user_sessions: Multi-user session tracking")
        print("  - session_messages: Chat message history per session")
        print("  - chat_requests: Async request tracking")
        print("")
        print("Ready to start the app!")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        raise


if __name__ == "__main__":
    try:
        initialize_database()
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
