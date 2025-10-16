"""
Sprint API endpoint tests
스프린트 API 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.sprint import Sprint


class TestSprintAPI:
    """Test sprint CRUD operations"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session, test_user, test_team):
        """Setup test data"""
        from app.models.project import Project

        project = Project(
            key="TEST",
            name="Test Project",
            team_id=test_team.id,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        self.project = project

    def test_create_sprint(self, authenticated_client: TestClient, db_session: Session):
        """Test creating a new sprint"""
        sprint_data = {
            "name": "Sprint 1",
            "project_id": self.project.id,
            "start_date": "2024-01-15",
            "end_date": "2024-01-29",
            "goal": "Complete core features",
        }

        response = authenticated_client.post("/api/v1/sprints", json=sprint_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Sprint 1"
        assert data["project_id"] == self.project.id

    def test_list_sprints(self, authenticated_client: TestClient, db_session: Session):
        """Test listing sprints"""
        # Create a sprint first
        sprint = Sprint(
            name="Sprint 1",
            project_id=self.project.id,
            status="planned",
        )
        db_session.add(sprint)
        db_session.commit()

        response = authenticated_client.get("/api/v1/sprints")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "meta" in data
        assert len(data["items"]) >= 1

    def test_get_sprint(self, authenticated_client: TestClient, db_session: Session):
        """Test getting a sprint by ID"""
        sprint = Sprint(
            name="Sprint 1",
            project_id=self.project.id,
            status="planned",
        )
        db_session.add(sprint)
        db_session.commit()
        db_session.refresh(sprint)

        response = authenticated_client.get(f"/api/v1/sprints/{sprint.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == sprint.id
        assert data["name"] == "Sprint 1"

    def test_update_sprint(self, authenticated_client: TestClient, db_session: Session):
        """Test updating a sprint"""
        sprint = Sprint(
            name="Sprint 1",
            project_id=self.project.id,
            status="planned",
        )
        db_session.add(sprint)
        db_session.commit()
        db_session.refresh(sprint)

        update_data = {
            "name": "Updated Sprint",
            "goal": "Updated goal",
        }

        response = authenticated_client.put(f"/api/v1/sprints/{sprint.id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Sprint"
        assert data["goal"] == "Updated goal"

    def test_delete_sprint(self, authenticated_client: TestClient, db_session: Session):
        """Test deleting a sprint"""
        sprint = Sprint(
            name="Sprint 1",
            project_id=self.project.id,
            status="planned",
        )
        db_session.add(sprint)
        db_session.commit()
        db_session.refresh(sprint)

        response = authenticated_client.delete(f"/api/v1/sprints/{sprint.id}")
        assert response.status_code == 200

        # Verify sprint is deleted
        get_response = authenticated_client.get(f"/api/v1/sprints/{sprint.id}")
        assert get_response.status_code == 404

    def test_start_sprint(self, authenticated_client: TestClient, db_session: Session):
        """Test starting a sprint"""
        sprint = Sprint(
            name="Sprint 1",
            project_id=self.project.id,
            status="planned",
        )
        db_session.add(sprint)
        db_session.commit()
        db_session.refresh(sprint)

        response = authenticated_client.post(f"/api/v1/sprints/{sprint.id}/start")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "active"

    def test_complete_sprint(self, authenticated_client: TestClient, db_session: Session):
        """Test completing a sprint"""
        sprint = Sprint(
            name="Sprint 1",
            project_id=self.project.id,
            status="active",
        )
        db_session.add(sprint)
        db_session.commit()
        db_session.refresh(sprint)

        response = authenticated_client.post(f"/api/v1/sprints/{sprint.id}/complete")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "completed"

    def test_update_sprint_status(self, authenticated_client: TestClient, db_session: Session):
        """Test updating sprint status"""
        sprint = Sprint(
            name="Sprint 1",
            project_id=self.project.id,
            status="planned",
        )
        db_session.add(sprint)
        db_session.commit()
        db_session.refresh(sprint)

        response = authenticated_client.patch(
            f"/api/v1/sprints/{sprint.id}/status?status=active"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "active"


class TestSprintFiltering:
    """Test sprint filtering operations"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session, test_user, test_team):
        """Setup test data"""
        from app.models.project import Project

        project = Project(
            key="TEST",
            name="Test Project",
            team_id=test_team.id,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        self.project = project

    def test_get_project_sprints(self, authenticated_client: TestClient, db_session: Session):
        """Test getting sprints by project"""
        sprint1 = Sprint(
            name="Sprint 1",
            project_id=self.project.id,
            status="planned",
        )
        sprint2 = Sprint(
            name="Sprint 2",
            project_id=self.project.id,
            status="active",
        )
        db_session.add_all([sprint1, sprint2])
        db_session.commit()

        response = authenticated_client.get(f"/api/v1/sprints/project/{self.project.id}")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 2

    def test_get_active_sprint(self, authenticated_client: TestClient, db_session: Session):
        """Test getting active sprint for a project"""
        sprint = Sprint(
            name="Sprint 1",
            project_id=self.project.id,
            status="active",
        )
        db_session.add(sprint)
        db_session.commit()

        response = authenticated_client.get(f"/api/v1/sprints/project/{self.project.id}/active")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "active"
