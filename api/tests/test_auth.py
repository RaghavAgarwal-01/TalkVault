import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

from app.main import app
from app.db.dbmongo import db  # original db client

MONGO_TEST_DB = "talkvault_test"

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def override_get_db():
    # Connect to test DB
    test_client = AsyncIOMotorClient("mongodb://localhost:27017")
    test_db = test_client[MONGO_TEST_DB]

    # Override dependency with test DB
    app.dependency_overrides[db] = lambda: test_db

    yield

    # Cleanup after tests: drop test DB
    asyncio.get_event_loop().run_until_complete(test_client.drop_database(MONGO_TEST_DB))

def test_signup():
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"

# Add more tests similarly...
