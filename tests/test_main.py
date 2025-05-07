import os
import pytest
from fastapi.testclient import TestClient
from app.main import app, lifespan

def test_read_root():
    """Test the root endpoint."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Central Patient Profile Service is running"}

@pytest.mark.asyncio
async def test_lifespan():
    """Test the application lifespan."""
    # Test with TESTING=1
    os.environ["TESTING"] = "1"
    async with lifespan(app) as _:
        pass  # Should not initialize the database
    
    # Test without TESTING
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    async with lifespan(app) as _:
        pass  # Should initialize the database 