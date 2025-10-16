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
        test_team,
    ):
        """Test creating a new project"""
        project_data = {
            "key": "TEST",
            "name": "Test Project",
            "description": "A test project",
            "team_id": test_team.id,
        }

        response = authenticated_client.post("/api/v1/projects", json=project_data)
        assert response.status_code == 201

        data = response.json()
        assert data["key"] == "TEST"
        assert data["name"] == "Test Project"
        assert data["team_id"] == test_team.id

    def test_list_projects(self, authenticated_client: TestClient, db_session: Session, test_team):
        """Test listing projects"""
        # Create test projects
        project1 = Project(
            key="TEST1",
            name="Project 1",
            team_id=test_team.id,
        )
        project2 = Project(
            key="TEST2",
            name="Project 2",
            team_id=test_team.id,
        )
        db_session.add_all([project1, project2])
        db_session.commit()

        response = authenticated_client.get("/api/v1/projects")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "meta" in data
        assert len(data["items"]) == 2

    def test_get_project(self, authenticated_client: TestClient, db_session: Session, test_team):
        """Test getting a single project"""
        project = Project(
            key="TEST",
            name="Test Project",
            team_id=test_team.id,
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

    def test_update_project(self, authenticated_client: TestClient, db_session: Session, test_team):
        """Test updating a project"""
        project = Project(
            key="TEST",
            name="Test Project",
            team_id=test_team.id,
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

    def test_delete_project(self, authenticated_client: TestClient, db_session: Session, test_team):
        """Test deleting a project"""
        project = Project(
            key="TEST",
            name="Test Project",
            team_id=test_team.id,
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
        test_team,
    ):
        """Test creating a project with duplicate key"""
        project = Project(
            key="TEST",
            name="Test Project",
            team_id=test_team.id,
        )
        db_session.add(project)
        db_session.commit()

        # Try to create another project with same key
        project_data = {
            "key": "TEST",
            "name": "Another Project",
            "team_id": test_team.id,
        }

        response = authenticated_client.post("/api/v1/projects", json=project_data)
        assert response.status_code == 400


class TestProjectFiltering:
    """Test project filtering and search"""

    def test_filter_projects_by_team(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        test_team,
    ):
        """Test filtering projects by team"""
        from app.models.team import Team
        team2 = Team(name="Team 2", slug="team-2")
        db_session.add(team2)
        db_session.commit()
        db_session.refresh(team2)

        project1 = Project(key="TEST1", name="Team 1 Project", team_id=test_team.id)
        project2 = Project(key="TEST2", name="Team 2 Project", team_id=team2.id)
        db_session.add_all([project1, project2])
        db_session.commit()

        response = authenticated_client.get(f"/api/v1/projects?team_id={test_team.id}")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["team_id"] == test_team.id

    def test_search_projects(self, authenticated_client: TestClient, db_session: Session, test_team):
        """Test searching projects"""
        project1 = Project(key="TEST1", name="Backend Project", team_id=test_team.id)
        project2 = Project(key="TEST2", name="Frontend Project", team_id=test_team.id)
        db_session.add_all([project1, project2])
        db_session.commit()

        response = authenticated_client.get("/api/v1/projects?search=Backend")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 1
        assert "Backend" in data["items"][0]["name"]

    def test_pagination(self, authenticated_client: TestClient, db_session: Session, test_team):
        """Test project pagination"""
        # Create 25 projects
        projects = [
            Project(key=f"TEST{i}", name=f"Project {i}", team_id=test_team.id)
            for i in range(25)
        ]
        db_session.add_all(projects)
        db_session.commit()

        # Get first page
        response = authenticated_client.get("/api/v1/projects?page=1&page_size=10")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 10
        assert data["meta"]["page"] == 1
        assert data["meta"]["total"] == 25
        assert data["meta"]["has_next"] is True

        # Get second page
        response = authenticated_client.get("/api/v1/projects?page=2&page_size=10")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 10
        assert data["meta"]["page"] == 2
