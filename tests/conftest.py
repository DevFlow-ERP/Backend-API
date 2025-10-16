"""
Pytest configuration and fixtures
Test infrastructure setup
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.core.security import create_access_token


# Test database URL (SQLite in-memory for testing)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with in-memory SQLite
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database session override
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """
    Create a test user
    """
    user = User(
        authentik_id="test-user-123",
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_superuser(db_session: Session) -> User:
    """
    Create a test superuser
    """
    user = User(
        authentik_id="admin-user-456",
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_token(test_user: User) -> str:
    """
    Create an access token for the test user
    """
    return create_access_token(subject=test_user.id)


@pytest.fixture(scope="function")
def superuser_token(test_superuser: User) -> str:
    """
    Create an access token for the test superuser
    """
    return create_access_token(subject=test_superuser.id)


@pytest.fixture(scope="function")
def auth_headers(test_token: str) -> dict:
    """
    Create authorization headers with test token
    """
    return {"Authorization": f"Bearer {test_token}"}


@pytest.fixture(scope="function")
def superuser_auth_headers(superuser_token: str) -> dict:
    """
    Create authorization headers with superuser token
    """
    return {"Authorization": f"Bearer {superuser_token}"}


@pytest.fixture(scope="function")
def authenticated_client(client: TestClient, test_user: User) -> TestClient:
    """
    Create a test client with authenticated user
    """
    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    return client


@pytest.fixture(scope="function")
def superuser_client(client: TestClient, test_superuser: User) -> TestClient:
    """
    Create a test client with authenticated superuser
    """
    def override_get_current_user():
        return test_superuser

    app.dependency_overrides[get_current_user] = override_get_current_user

    return client


# Test data fixtures

@pytest.fixture(scope="function")
def sample_project_data() -> dict:
    """
    Sample project data for testing
    """
    return {
        "key": "TEST",
        "name": "Test Project",
        "description": "A test project",
        "owner_id": 1,
    }


@pytest.fixture(scope="function")
def sample_sprint_data() -> dict:
    """
    Sample sprint data for testing
    """
    return {
        "name": "Sprint 1",
        "project_id": 1,
        "start_date": "2024-01-15",
        "end_date": "2024-01-29",
        "goal": "Complete core features",
    }


@pytest.fixture(scope="function")
def sample_issue_data() -> dict:
    """
    Sample issue data for testing
    """
    return {
        "project_id": 1,
        "title": "Test Issue",
        "description": "Test issue description",
        "type": "task",
        "priority": "medium",
        "reporter_id": 1,
    }


@pytest.fixture(scope="function")
def sample_team_data() -> dict:
    """
    Sample team data for testing
    """
    return {
        "name": "Test Team",
        "description": "A test team",
    }


@pytest.fixture(scope="function")
def sample_server_data() -> dict:
    """
    Sample server data for testing
    """
    return {
        "name": "test-server",
        "hostname": "test.example.com",
        "ip_address": "192.168.1.100",
        "environment": "dev",
        "type": "virtual",
        "status": "active",
    }


@pytest.fixture(scope="function")
def sample_service_data() -> dict:
    """
    Sample service data for testing
    """
    return {
        "server_id": 1,
        "name": "test-service",
        "type": "web",
        "status": "running",
        "version": "1.0.0",
    }


@pytest.fixture(scope="function")
def sample_deployment_data() -> dict:
    """
    Sample deployment data for testing
    """
    return {
        "service_id": 1,
        "version": "1.0.0",
        "environment": "production",
        "type": "manual",
        "status": "pending",
        "commit_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
        "branch": "main",
    }
