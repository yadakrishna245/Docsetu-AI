"""
DocSetu AI - Authentication Integration Tests
Tests for user registration, login, and JWT-protected endpoints.
"""

import pytest
from httpx import AsyncClient


class TestUserRegistration:
    """Tests for POST /api/auth/register."""

    async def test_register_success(self, test_client: AsyncClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePass123!",
            "full_name": "New User",
            "organization": "New Org",
        }

        response = await test_client.post("/api/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["full_name"] == user_data["full_name"]
        assert data["organization"] == user_data["organization"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        # Password should not be in the response
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email_fails(self, test_client: AsyncClient):
        """Test that registering with an existing email returns 409."""
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "SecurePass123!",
        }

        # First registration should succeed
        response1 = await test_client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 201

        # Second registration with same email should fail
        user_data_duplicate = {
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "SecurePass123!",
        }
        response2 = await test_client.post("/api/auth/register", json=user_data_duplicate)

        assert response2.status_code == 409
        assert "already registered" in response2.json()["detail"].lower()

    async def test_register_duplicate_username_fails(self, test_client: AsyncClient):
        """Test that registering with an existing username returns 409."""
        user_data = {
            "email": "first@example.com",
            "username": "sameusername",
            "password": "SecurePass123!",
        }

        response1 = await test_client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 201

        user_data_duplicate = {
            "email": "second@example.com",
            "username": "sameusername",
            "password": "SecurePass123!",
        }
        response2 = await test_client.post("/api/auth/register", json=user_data_duplicate)

        assert response2.status_code == 409
        assert "username" in response2.json()["detail"].lower()

    async def test_register_invalid_email_fails(self, test_client: AsyncClient):
        """Test that registration with invalid email fails validation."""
        user_data = {
            "email": "not-an-email",
            "username": "validuser",
            "password": "SecurePass123!",
        }

        response = await test_client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422

    async def test_register_short_password_fails(self, test_client: AsyncClient):
        """Test that registration with too-short password fails validation."""
        user_data = {
            "email": "valid@example.com",
            "username": "validuser",
            "password": "short",
        }

        response = await test_client.post("/api/auth/register", json=user_data)
        assert response.status_code == 422


class TestUserLogin:
    """Tests for POST /api/auth/login."""

    async def test_login_success(self, test_client: AsyncClient):
        """Test successful login returns a valid token."""
        # First register a user
        user_data = {
            "email": "logintest@example.com",
            "username": "logintest",
            "password": "SecurePass123!",
        }
        await test_client.post("/api/auth/register", json=user_data)

        # Login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"],
        }
        response = await test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["expires_in"] > 0

    async def test_login_wrong_password_fails(self, test_client: AsyncClient):
        """Test login with wrong password returns 401."""
        # Register a user
        user_data = {
            "email": "wrongpass@example.com",
            "username": "wrongpass",
            "password": "CorrectPassword123!",
        }
        await test_client.post("/api/auth/register", json=user_data)

        # Login with wrong password
        login_data = {
            "email": user_data["email"],
            "password": "WrongPassword456!",
        }
        response = await test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_login_nonexistent_user_fails(self, test_client: AsyncClient):
        """Test login with non-existent email returns 401."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        }
        response = await test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401


class TestGetMe:
    """Tests for GET /api/auth/me."""

    async def test_get_me_with_valid_token(self, test_client: AsyncClient, test_user: dict):
        """Test that /me returns current user data with valid token."""
        response = await test_client.get("/api/auth/me", headers=test_user["headers"])

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["username"] == test_user["username"]
        assert data["is_active"] is True
        assert "id" in data

    async def test_get_me_without_token_returns_401(self, test_client: AsyncClient):
        """Test that /me without token returns 401 Unauthorized."""
        response = await test_client.get("/api/auth/me")

        assert response.status_code == 401

    async def test_get_me_with_invalid_token_returns_401(self, test_client: AsyncClient):
        """Test that /me with invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid-token-value"}
        response = await test_client.get("/api/auth/me", headers=headers)

        assert response.status_code == 401
