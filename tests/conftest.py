import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.test_db import get_test_db, init_test_db, drop_test_db

@pytest.fixture(scope="session")
def db():
    init_test_db()
    yield next(get_test_db())
    drop_test_db()

@pytest.fixture(scope="module")
def client(db: Session):
    app.dependency_overrides[get_test_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear() 