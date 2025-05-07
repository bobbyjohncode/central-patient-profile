import pytest
import pytest_asyncio
import asyncio
import os
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch, MagicMock

from app.main import app
from app.db.test_db import get_db, init_test_db, drop_test_db

@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Set up test database before each test."""
    os.environ["TESTING"] = "1"
    await init_test_db()
    yield
    await drop_test_db()

@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for testing."""
    async for session in get_db():
        yield session

@pytest.fixture
def client(db: AsyncSession) -> Generator:
    """Create a test client with a test database session."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def error_db():
    """Fixture that provides a database session that raises IntegrityError on commit."""
    mock_session = MagicMock()
    mock_session.commit.side_effect = IntegrityError("", "", "")
    mock_session.query.return_value.all.return_value = []
    yield mock_session

@pytest.fixture
def error_client(error_db):
    """Client fixture that uses a database session that raises IntegrityError."""
    def override_get_db():
        yield error_db
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear() 