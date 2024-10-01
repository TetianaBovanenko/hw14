import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.connect_db import Base, get_db
from services.auth import auth_services
from db.models import User
from main import app

# Define the test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create the test database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the database tables before running the tests
Base.metadata.create_all(bind=engine)

# Override the default database dependency with the testing session
def override_get_db():
    db = SessionTesting()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Mocking the current user
async def mock_get_current_user():
    return User(id=1, email="testuser@example.com", username="testuser")

app.dependency_overrides[auth_services.get_current_user] = mock_get_current_user

# Pytest fixture to handle setup and teardown of database session
@pytest.fixture(scope="function", autouse=True)
def setup_db():
    # Create tables before each test
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after each test
    Base.metadata.drop_all(bind=engine)

# The actual test for creating a contact
@pytest.mark.asyncio
async def test_create_contact():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Contact payload
        contact_data = {
            "first_name": "Alice",
            "second_name": "Smith",
            "email": "alice.smith@example.com",
            "phone": "9876543210",
            "birthdate": "1992-06-15",
            "additional_data": "Work colleague"
        }

        # Make the POST request to create a contact
        response = await client.post("/api/contacts/", json=contact_data)

        # Assert that the status code is 201 Created
        assert response.status_code == status.HTTP_201_CREATED

        # Assert that the response contains the correct contact details
        response_data = response.json()
        assert response_data["first_name"] == "Alice"
        assert response_data["second_name"] == "Smith"
        assert response_data["email"] == "alice.smith@example.com"
        assert response_data["phone"] == "9876543210"
        assert response_data["birthdate"] == "1992-06-15"
        assert response_data["additional_data"] == "Work colleague"

# Additional test to check validation (for example, missing fields)
@pytest.mark.asyncio
async def test_create_contact_validation_error():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Contact payload with missing fields
        contact_data = {
            "first_name": "Bob",
            "second_name": "Johnson",
            "email": "bob.johnson@example.com",
            "phone": "9876543210",
            # Missing birthdate and additional_data
        }

        # Make the POST request to create a contact
        response = await client.post("/api/contacts/", json=contact_data)

        # Assert that the status code is 422 Unprocessable Entity
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Assert that the error message contains details about the missing fields
        response_data = response.json()
        assert "detail" in response_data
