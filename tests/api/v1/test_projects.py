"""
Project API tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User


class TestProjectAPI:
    """Test project endpoints"""

    def test_create_project(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        test_user: User,
    ):
        """Test creating a new project"""
        project_data = {
            "key": "TEST",
            "name": "Test Project",
            "description": "A test project",
            "owner_id": test_user.id,
        }

        response = authenticated_client.post("/api/v1/projects", json=project_data)
        assert response.status_code == 201

        data = response.json()
        assert data["key"] == "TEST"
        assert data["name"] == "Test Project"
        assert data["owner_id"] == test_user.id

    def test_list_projects(self, authenticated_client: TestClient, db_session: Session, test_user: User):
        """Test listing projects"""
        # Create test projects
        project1 = Project(
            key="TEST1",
            name="Project 1",
            owner_id=test_user.id,
        )
        project2 = Project(
            key="TEST2",
            name="Project 2",
            owner_id=test_user.id,
        )
        db_session.add_all([project1, project2])
        db_session.commit()

        response = authenticated_client.get("/api/v1/projects")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) == 2

    def test_get_project(self, authenticated_client: TestClient, db_session: Session, test_user: User):
        """Test getting a single project"""
        project = Project(
            key="TEST",
            name="Test Project",
            owner_id=test_user.id,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        response = authenticated_client.get(f"/api/v1/projects/{project.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == project.id
        assert data["key"] == "TEST"
        assert data["name"] == "Test Project"

    def test_update_project(self, authenticated_client: TestClient, db_session: Session, test_user: User):
        """Test updating a project"""
        project = Project(
            key="TEST",
            name="Test Project",
            owner_id=test_user.id,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        update_data = {
            "name": "Updated Project",
            "description": "Updated description",
        }

        response = authenticated_client.put(f"/api/v1/projects/{project.id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Project"
        assert data["description"] == "Updated description"

    def test_delete_project(self, authenticated_client: TestClient, db_session: Session, test_user: User):
        """Test deleting a project"""
        project = Project(
            key="TEST",
            name="Test Project",
            owner_id=test_user.id,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        response = authenticated_client.delete(f"/api/v1/projects/{project.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Verify project is deleted
        db_project = db_session.get(Project, project.id)
        assert db_project is None

    def test_get_nonexistent_project(self, authenticated_client: TestClient):
        """Test getting a project that doesn't exist"""
        response = authenticated_client.get("/api/v1/projects/99999")
        assert response.status_code == 404

    def test_create_project_duplicate_key(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        test_user: User,
    ):
        """Test creating a project with duplicate key"""
        project = Project(
            key="TEST",
            name="Test Project",
            owner_id=test_user.id,
        )
        db_session.add(project)
        db_session.commit()

        # Try to create another project with same key
        project_data = {
            "key": "TEST",
            "name": "Another Project",
            "owner_id": test_user.id,
        }

        response = authenticated_client.post("/api/v1/projects", json=project_data)
        assert response.status_code == 400


class TestProjectFiltering:
    """Test project filtering and search"""

    def test_filter_projects_by_owner(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        test_user: User,
        test_superuser: User,
    ):
        """Test filtering projects by owner"""
        project1 = Project(key="TEST1", name="User Project", owner_id=test_user.id)
        project2 = Project(key="TEST2", name="Admin Project", owner_id=test_superuser.id)
        db_session.add_all([project1, project2])
        db_session.commit()

        response = authenticated_client.get(f"/api/v1/projects?owner_id={test_user.id}")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["owner_id"] == test_user.id

    def test_search_projects(self, authenticated_client: TestClient, db_session: Session, test_user: User):
        """Test searching projects"""
        project1 = Project(key="TEST1", name="Backend Project", owner_id=test_user.id)
        project2 = Project(key="TEST2", name="Frontend Project", owner_id=test_user.id)
        db_session.add_all([project1, project2])
        db_session.commit()

        response = authenticated_client.get("/api/v1/projects?search=Backend")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 1
        assert "Backend" in data["data"][0]["name"]

    def test_pagination(self, authenticated_client: TestClient, db_session: Session, test_user: User):
        """Test project pagination"""
        # Create 25 projects
        projects = [
            Project(key=f"TEST{i}", name=f"Project {i}", owner_id=test_user.id)
            for i in range(25)
        ]
        db_session.add_all(projects)
        db_session.commit()

        # Get first page
        response = authenticated_client.get("/api/v1/projects?page=1&page_size=10")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 10
        assert data["meta"]["page"] == 1
        assert data["meta"]["total"] == 25
        assert data["meta"]["has_next"] is True

        # Get second page
        response = authenticated_client.get("/api/v1/projects?page=2&page_size=10")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 10
        assert data["meta"]["page"] == 2
