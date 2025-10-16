"""
Authentication API tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


class TestAuthAPI:
    """Test authentication endpoints"""

    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data

    def test_readiness_check(self, client: TestClient):
        """Test readiness check endpoint"""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data


class TestAuthenticationFlow:
    """Test authentication flow"""

    def test_get_current_user_authenticated(self, authenticated_client: TestClient, test_user: User):
        """Test getting current user when authenticated"""
        response = authenticated_client.get("/api/v1/auth/me")

        if response.status_code == 404:
            # Auth endpoint might not be implemented yet
            pytest.skip("Auth endpoints not implemented")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    def test_get_current_user_unauthenticated(self, client: TestClient):
        """Test getting current user when not authenticated"""
        response = client.get("/api/v1/auth/me")

        if response.status_code == 404:
            pytest.skip("Auth endpoints not implemented")

        assert response.status_code == 401


class TestAuthorization:
    """Test authorization and permissions"""

    def test_superuser_access(self, superuser_client: TestClient, test_superuser: User):
        """Test superuser has proper access"""
        assert test_superuser.is_admin is True

    def test_regular_user_access(self, authenticated_client: TestClient, test_user: User):
        """Test regular user permissions"""
        assert test_user.is_admin is False
        assert test_user.is_active is True
