import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch, MagicMock

from app.main import app
from app.db.test_db import get_test_db, init_test_db, drop_test_db, TestingSessionLocal, engine
from app.db.session import get_db

@pytest.fixture(autouse=True)
def setup_test_db():
    """Fixture to set up and tear down the test database for each test."""
    os.environ["TESTING"] = "1"
    init_test_db()  # Initialize fresh test database
    yield
    drop_test_db()  # Clean up after test

@pytest.fixture
def db():
    """Fixture to get a test database session."""
    init_test_db()
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
        drop_test_db()

@pytest.fixture
def client(db):
    """Fixture to get a test client with a test database session."""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
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