import asyncio
import os

# Must be set before any app imports
os.environ["OPENAI_API_KEY"] = "test"
os.environ["KIE_API_KEY"] = "test"
os.environ["MOCK_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_db.sqlite3"

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.database import Base

TEST_DB_URL = "sqlite+aiosqlite:///./test_db.sqlite3"


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    async def _create():
        engine = create_async_engine(TEST_DB_URL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.get_event_loop().run_until_complete(_create())
    yield

    # cleanup
    if os.path.exists("./test_db.sqlite3"):
        os.remove("./test_db.sqlite3")
