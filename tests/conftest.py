import os
import tempfile

# Configure the app for tests *before* any app module is imported: in-memory
# rate limiting/caching and a throwaway SQLite database instead of Postgres/Redis.
_DB_DIR = tempfile.mkdtemp(prefix="gateway-tests-")
_DB_FILE = os.path.join(_DB_DIR, "test.db").replace("\\", "/")
os.environ.update({
    "ENVIRONMENT": "testing",
    "USE_REDIS": "false",
    "DATABASE_URL": f"sqlite+aiosqlite:///{_DB_FILE}",
    "SECRET_KEY": "test-secret-key-that-is-long-enough-123",
    "ADMIN_EMAIL": "admin@example.com",
    "ADMIN_PASSWORD": "admin-password-1",
    "GATEWAY_RETRY_BASE_DELAY_SECONDS": "0",
})

import pytest
from sqlalchemy import create_engine

from app.infrastructure.database.models.base import Base
from app.infrastructure.database.models import api_key, provider, route, user  # noqa: F401  (register tables)


@pytest.fixture
def db_file():
    """Fresh schema for every test."""
    engine = create_engine(f"sqlite:///{_DB_FILE}")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    engine.dispose()
    return _DB_FILE
