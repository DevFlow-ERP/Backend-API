"""
Issue API endpoint tests
이슈 API 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.issue import Issue
from app.models.sprint import Sprint


class TestIssueAPI:
    """Test issue CRUD operations"""

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
        self.test_user = test_user

    def test_create_issue(self, authenticated_client: TestClient, db_session: Session):
        """Test creating a new issue"""
        issue_data = {
            "project_id": self.project.id,
            "title": "Test Issue",
            "description": "Test description",
            "type": "task",
            "priority": "medium",
        }

        response = authenticated_client.post("/api/v1/issues", json=issue_data)
        assert response.status_code == 201

        data = response.json()
        assert data["title"] == "Test Issue"
        assert data["key"].startswith("TEST-")

    def test_list_issues(self, authenticated_client: TestClient, db_session: Session):
        """Test listing issues"""
        issue = Issue(
            project_id=self.project.id,
            creator_id=self.test_user.id,
            title="Test Issue",
            type="task",
            priority="medium",
            status="todo",
            key="TEST-1",
        )
        db_session.add(issue)
        db_session.commit()

        response = authenticated_client.get("/api/v1/issues")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_get_issue(self, authenticated_client: TestClient, db_session: Session):
        """Test getting an issue by ID"""
        issue = Issue(
            project_id=self.project.id,
            creator_id=self.test_user.id,
            title="Test Issue",
            type="task",
            priority="medium",
            status="todo",
            key="TEST-1",
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        response = authenticated_client.get(f"/api/v1/issues/{issue.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == issue.id
        assert data["title"] == "Test Issue"

    def test_update_issue(self, authenticated_client: TestClient, db_session: Session):
        """Test updating an issue"""
        issue = Issue(
            project_id=self.project.id,
            creator_id=self.test_user.id,
            title="Test Issue",
            type="task",
            priority="medium",
            status="todo",
            key="TEST-1",
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        update_data = {
            "title": "Updated Issue",
            "priority": "high",
        }

        response = authenticated_client.put(f"/api/v1/issues/{issue.id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Updated Issue"
        assert data["priority"] == "high"

    def test_delete_issue(self, authenticated_client: TestClient, db_session: Session):
        """Test deleting an issue"""
        issue = Issue(
            project_id=self.project.id,
            creator_id=self.test_user.id,
            title="Test Issue",
            type="task",
            priority="medium",
            status="todo",
            key="TEST-1",
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        response = authenticated_client.delete(f"/api/v1/issues/{issue.id}")
        assert response.status_code == 200

        # Verify issue is deleted
        get_response = authenticated_client.get(f"/api/v1/issues/{issue.id}")
        assert get_response.status_code == 404

    def test_update_issue_status(self, authenticated_client: TestClient, db_session: Session):
        """Test updating issue status"""
        issue = Issue(
            project_id=self.project.id,
            creator_id=self.test_user.id,
            title="Test Issue",
            type="task",
            priority="medium",
            status="todo",
            key="TEST-1",
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        response = authenticated_client.patch(
            f"/api/v1/issues/{issue.id}/status?status=in_progress"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "in_progress"

    def test_assign_issue(self, authenticated_client: TestClient, db_session: Session):
        """Test assigning an issue"""
        issue = Issue(
            project_id=self.project.id,
            creator_id=self.test_user.id,
            title="Test Issue",
            type="task",
            priority="medium",
            status="todo",
            key="TEST-1",
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        response = authenticated_client.patch(
            f"/api/v1/issues/{issue.id}/assign",
            json={"assignee_id": self.test_user.id}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["assignee_id"] == self.test_user.id

    def test_move_issue_to_sprint(self, authenticated_client: TestClient, db_session: Session):
        """Test moving an issue to a sprint"""
        sprint = Sprint(
            name="Sprint 1",
            project_id=self.project.id,
            status="planned",
        )
        db_session.add(sprint)
        db_session.commit()
        db_session.refresh(sprint)

        issue = Issue(
            project_id=self.project.id,
            creator_id=self.test_user.id,
            title="Test Issue",
            type="task",
            priority="medium",
            status="todo",
            key="TEST-1",
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)

        response = authenticated_client.patch(
            f"/api/v1/issues/{issue.id}/sprint",
            json={"sprint_id": sprint.id}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["sprint_id"] == sprint.id


class TestIssueFiltering:
    """Test issue filtering operations"""

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

        sprint = Sprint(
            name="Sprint 1",
            project_id=project.id,
            status="planned",
        )
        db_session.add(sprint)
        db_session.commit()
        db_session.refresh(sprint)

        self.project = project
        self.sprint = sprint
        self.test_user = test_user

    def test_get_my_issues(self, authenticated_client: TestClient, db_session: Session):
        """Test getting my assigned issues"""
        issue = Issue(
            project_id=self.project.id,
            creator_id=self.test_user.id,
            assignee_id=self.test_user.id,
            title="My Issue",
            type="task",
            priority="medium",
            status="todo",
            key="TEST-1",
        )
        db_session.add(issue)
        db_session.commit()

        response = authenticated_client.get("/api/v1/issues/my")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) >= 1

    def test_get_project_backlog(self, authenticated_client: TestClient, db_session: Session):
        """Test getting project backlog"""
        issue = Issue(
            project_id=self.project.id,
            creator_id=self.test_user.id,
            title="Backlog Issue",
            type="task",
            priority="medium",
            status="todo",
            key="TEST-1",
        )
        db_session.add(issue)
        db_session.commit()

        response = authenticated_client.get(
            f"/api/v1/issues/project/{self.project.id}/backlog"
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) >= 1

    def test_get_sprint_issues(self, authenticated_client: TestClient, db_session: Session):
        """Test getting sprint issues"""
        issue = Issue(
            project_id=self.project.id,
            creator_id=self.test_user.id,
            sprint_id=self.sprint.id,
            title="Sprint Issue",
            type="task",
            priority="medium",
            status="todo",
            key="TEST-1",
        )
        db_session.add(issue)
        db_session.commit()

        response = authenticated_client.get(f"/api/v1/issues/sprint/{self.sprint.id}")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) >= 1
