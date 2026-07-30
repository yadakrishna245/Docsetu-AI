"""
DocSetu AI - Integration Test Configuration
Sets up in-memory SQLite test database, test client, and shared fixtures.
"""

import sys
import os
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override settings BEFORE importing the app
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["UPLOAD_DIR"] = "./test_uploads"
os.environ["LOG_FILE"] = "./test_logs/test.log"
os.environ["CHROMA_PERSIST_DIR"] = "./test_chroma"
os.environ["APP_ENV"] = "testing"
os.environ["DEBUG"] = "false"

from db import Base, get_db
from main import app


# --- In-Memory Test Database Setup ---

SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Provide a test database session."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the get_db dependency globally
app.dependency_overrides[get_db] = override_get_db


# --- Minimal PDF bytes for upload tests ---

MINIMAL_PDF_BYTES = (
    b"%PDF-1.0\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
    b"xref\n0 4\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n210\n%%EOF\n"
)


# --- Fixtures ---


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them after."""
    # Import models so they register with Base
    from models.database import User, Document, Analysis, ComplianceReport  # noqa: F401

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest_asyncio.fixture
async def test_client():
    """Create an async test client using httpx with ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def test_user(test_client: AsyncClient):
    """Register a test user and return their auth token and user info."""
    user_data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "organization": "Test Org",
    }

    # Register user
    register_response = await test_client.post("/api/auth/register", json=user_data)
    assert register_response.status_code == 201, f"Registration failed: {register_response.text}"

    # Login to get token
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"],
    }
    login_response = await test_client.post("/api/auth/login", json=login_data)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"

    token_data = login_response.json()

    return {
        "token": token_data["access_token"],
        "email": user_data["email"],
        "username": user_data["username"],
        "password": user_data["password"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
    }


@pytest_asyncio.fixture
async def test_document(test_client: AsyncClient, test_user: dict):
    """Upload a dummy PDF document and return its info."""
    # Mock the OCR service to avoid external dependencies
    mock_ocr_result = {
        "text": "This is a test document with GST number 27AAPFU0939F1ZV and PAN AAPFU0939F.",
        "language_detected": "en",
        "page_count": 1,
        "method": "test",
        "is_scanned": False,
        "confidence": 0.99,
    }

    with patch("routers.documents.OCRService") as mock_ocr_class:
        mock_ocr_instance = mock_ocr_class.return_value
        mock_ocr_instance.extract_text = AsyncMock(return_value=mock_ocr_result)

        response = await test_client.post(
            "/api/documents/upload",
            files={"file": ("test_document.pdf", MINIMAL_PDF_BYTES, "application/pdf")},
            headers=test_user["headers"],
        )

    assert response.status_code == 201, f"Document upload failed: {response.text}"
    doc_data = response.json()

    return {
        "id": doc_data["id"],
        "filename": doc_data["filename"],
        "status": doc_data["status"],
        "headers": test_user["headers"],
    }
