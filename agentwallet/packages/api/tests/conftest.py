"""Test configuration -- use in-memory SQLite for tests."""

import os

# Override database URL before importing anything
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["ENCRYPTION_KEY"] = ""
