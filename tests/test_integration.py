"""
Integration tests
Test complete workflows across multiple modules
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.issue import Issue
from app.models.server import Server
from app.models.service import Service
from app.models.deployment import Deployment


class TestProjectWorkflow:
    """Test complete project workflow"""

    def test_project_sprint_issue_workflow(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        test_user: User,
        test_team,
    ):
        """
        Test full workflow: Create project → Create sprint → Create issue → Assign to sprint
        """
        # 1. Create project
        project_data = {
            "key": "TEST",
            "name": "Test Project",
            "description": "Integration test project",
            "team_id": test_team.id,
        }
        project_response = authenticated_client.post("/api/v1/projects", json=project_data)
        assert project_response.status_code == 201
        project = project_response.json()
        project_id = project["id"]

        # 2. Create sprint
        sprint_data = {
            "name": "Sprint 1",
            "project_id": project_id,
            "start_date": "2024-01-15",
            "end_date": "2024-01-29",
            "goal": "Complete integration tests",
        }
        sprint_response = authenticated_client.post("/api/v1/sprints", json=sprint_data)
        assert sprint_response.status_code == 201
        sprint = sprint_response.json()
        sprint_id = sprint["id"]

        # 3. Create issue
        issue_data = {
            "project_id": project_id,
            "title": "Integration Test Issue",
            "description": "Test issue for integration testing",
            "type": "task",
            "priority": "high",
            "creator_id": test_user.id,
        }
        issue_response = authenticated_client.post("/api/v1/issues", json=issue_data)
        assert issue_response.status_code == 201
        issue = issue_response.json()
        issue_id = issue["id"]
        assert issue["key"].startswith("TEST-")

        # 4. Assign issue to sprint
        assign_response = authenticated_client.patch(
            f"/api/v1/issues/{issue_id}/sprint?sprint_id={sprint_id}"
        )
        assert assign_response.status_code == 200
        updated_issue = assign_response.json()
        assert updated_issue["sprint_id"] == sprint_id

        # 5. Verify sprint contains issue
        sprint_issues_response = authenticated_client.get(f"/api/v1/issues/sprint/{sprint_id}")
        assert sprint_issues_response.status_code == 200
        sprint_issues = sprint_issues_response.json()
        assert len(sprint_issues["items"]) == 1
        assert sprint_issues["items"][0]["id"] == issue_id

        # 6. Start sprint
        start_response = authenticated_client.post(f"/api/v1/sprints/{sprint_id}/start")
        assert start_response.status_code == 200
        started_sprint = start_response.json()
        assert started_sprint["status"] == "active"

        # 7. Update issue status
        status_response = authenticated_client.patch(
            f"/api/v1/issues/{issue_id}/status?status=in_progress"
        )
        assert status_response.status_code == 200

        # 8. Complete sprint
        complete_response = authenticated_client.post(f"/api/v1/sprints/{sprint_id}/complete")
        assert complete_response.status_code == 200
        completed_sprint = complete_response.json()
        assert completed_sprint["status"] == "completed"


class TestDeploymentWorkflow:
    """Test complete deployment workflow"""

    def test_infrastructure_deployment_rollback_workflow(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        test_user: User,
    ):
        """
        Test full workflow: Create server → Create service → Deploy → Rollback
        """
        # 1. Create server
        server_data = {
            "name": "prod-server-01",
            "hostname": "prod01.example.com",
            "ip_address": "192.168.1.10",
            "environment": "production",
            "type": "virtual",
            "status": "active",
            "cpu_cores": 8,
            "memory_gb": 32,
        }
        server_response = authenticated_client.post("/api/v1/servers", json=server_data)
        assert server_response.status_code == 201
        server = server_response.json()
        server_id = server["id"]

        # 2. Create service on server
        service_data = {
            "server_id": server_id,
            "name": "web-app",
            "type": "web",
            "status": "running",
            "version": "1.0.0",
            "port": 8080,
        }
        service_response = authenticated_client.post("/api/v1/services", json=service_data)
        assert service_response.status_code == 201
        service = service_response.json()
        service_id = service["id"]

        # 3. Deploy version 1.0.0
        deployment1_data = {
            "service_id": service_id,
            "version": "1.0.0",
            "environment": "production",
            "type": "manual",
            "status": "pending",
            "commit_hash": "abc123def456789abc123def456789abc1234567",
            "branch": "main",
        }
        deployment1_response = authenticated_client.post("/api/v1/deployments", json=deployment1_data)
        assert deployment1_response.status_code == 201
        deployment1 = deployment1_response.json()
        deployment1_id = deployment1["id"]

        # 4. Mark deployment as successful
        success_response = authenticated_client.patch(
            f"/api/v1/deployments/{deployment1_id}/status?status=success"
        )
        assert success_response.status_code == 200

        # 5. Deploy version 2.0.0
        deployment2_data = {
            "service_id": service_id,
            "version": "2.0.0",
            "environment": "production",
            "type": "manual",
            "status": "pending",
            "commit_hash": "def456abc789def456abc789def456abc7890123",
            "branch": "main",
        }
        deployment2_response = authenticated_client.post("/api/v1/deployments", json=deployment2_data)
        assert deployment2_response.status_code == 201
        deployment2 = deployment2_response.json()
        deployment2_id = deployment2["id"]

        # 6. Mark deployment as failed
        failed_response = authenticated_client.patch(
            f"/api/v1/deployments/{deployment2_id}/status?status=failed&error_message=Database+migration+failed"
        )
        assert failed_response.status_code == 200

        # 7. Rollback to version 1.0.0
        rollback_response = authenticated_client.post(
            f"/api/v1/deployments/{deployment1_id}/rollback?notes=Rolling+back+due+to+failed+deployment"
        )
        assert rollback_response.status_code == 201
        rollback_deployment = rollback_response.json()
        assert rollback_deployment["type"] == "rollback"
        assert rollback_deployment["version"] == "1.0.0"
        assert rollback_deployment["rollback_from_id"] == deployment1_id

        # 8. Verify deployment history
        history_response = authenticated_client.get(f"/api/v1/deployments/service/{service_id}")
        assert history_response.status_code == 200
        history = history_response.json()
        assert len(history["items"]) == 3  # Three deployments total

        # 9. Mark rollback as successful
        rollback_success = authenticated_client.patch(
            f"/api/v1/deployments/{rollback_deployment['id']}/status?status=success"
        )
        assert rollback_success.status_code == 200

        # 10. Verify only successful deployments
        success_list = authenticated_client.get("/api/v1/deployments/status/success")
        assert success_list.status_code == 200
        successful = success_list.json()
        assert len(successful["items"]) == 2  # Original and rollback


class TestTeamCollaboration:
    """Test team collaboration workflow"""

    def test_team_project_assignment_workflow(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        test_user: User,
        test_superuser: User,
    ):
        """
        Test workflow: Create team → Add members → Create project → Assign issues
        """
        # 1. Create team
        team_data = {
            "name": "Backend Team",
            "slug": "backend-team",
            "description": "Backend development team",
        }
        team_response = authenticated_client.post("/api/v1/teams", json=team_data)
        assert team_response.status_code == 201
        team = team_response.json()
        team_id = team["id"]

        # 2. Add member to team
        member_data = {
            "user_id": test_superuser.id,
            "role": "member",
        }
        member_response = authenticated_client.post(
            f"/api/v1/teams/{team_id}/members", json=member_data
        )
        assert member_response.status_code == 201

        # 3. Get team members
        members_response = authenticated_client.get(f"/api/v1/teams/{team_id}/members")
        assert members_response.status_code == 200
        members = members_response.json()
        assert len(members["items"]) == 2  # Owner + added member

        # 4. Create project
        project_data = {
            "key": "BACK",
            "name": "Backend Project",
            "team_id": team_id,
        }
        project_response = authenticated_client.post("/api/v1/projects", json=project_data)
        assert project_response.status_code == 201
        project = project_response.json()
        project_id = project["id"]

        # 5. Create and assign issues to team members
        issue1_data = {
            "project_id": project_id,
            "title": "Setup database",
            "type": "task",
            "priority": "high",
            "creator_id": test_user.id,
            "assignee_id": test_user.id,
        }
        issue1_response = authenticated_client.post("/api/v1/issues", json=issue1_data)
        assert issue1_response.status_code == 201

        issue2_data = {
            "project_id": project_id,
            "title": "Implement API",
            "type": "task",
            "priority": "high",
            "creator_id": test_user.id,
            "assignee_id": test_superuser.id,
        }
        issue2_response = authenticated_client.post("/api/v1/issues", json=issue2_data)
        assert issue2_response.status_code == 201

        # 6. Verify my assigned issues
        my_issues_response = authenticated_client.get("/api/v1/issues/my")
        assert my_issues_response.status_code == 200
        my_issues = my_issues_response.json()
        assert len(my_issues["items"]) >= 1


class TestCascadeDeletes:
    """Test cascade deletion behavior"""

    def test_project_cascade_delete(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        test_user: User,
        test_team,
    ):
        """
        Test that deleting a project cascades to sprints and issues
        """
        # Create project
        project = Project(key="TEST", name="Test Project", team_id=test_team.id)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        # Create sprint
        sprint = Sprint(
            name="Sprint 1",
            project_id=project.id,
            status="planned",
        )
        db_session.add(sprint)
        db_session.commit()

        # Create issues
        issue1 = Issue(
            project_id=project.id,
            title="Issue 1",
            type="task",
            priority="medium",
            status="todo",
            creator_id=test_user.id,
            key="TEST-1",
        )
        issue2 = Issue(
            project_id=project.id,
            sprint_id=sprint.id,
            title="Issue 2",
            type="task",
            priority="medium",
            status="todo",
            creator_id=test_user.id,
            key="TEST-2",
        )
        db_session.add_all([issue1, issue2])
        db_session.commit()

        # Delete project
        response = authenticated_client.delete(f"/api/v1/projects/{project.id}")
        assert response.status_code == 200

        # Verify cascaded deletes
        assert db_session.get(Project, project.id) is None
        assert db_session.get(Sprint, sprint.id) is None
        assert db_session.get(Issue, issue1.id) is None
        assert db_session.get(Issue, issue2.id) is None

    def test_server_cascade_delete(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        test_user: User,
    ):
        """
        Test that deleting a server cascades to services and deployments
        """
        # Create server
        server_data = {
            "name": "test-server",
            "hostname": "test.example.com",
            "ip_address": "192.168.1.100",
            "environment": "dev",
            "type": "virtual",
        }
        server_response = authenticated_client.post("/api/v1/servers", json=server_data)
        assert server_response.status_code == 201
        server = server_response.json()
        server_id = server["id"]

        # Create service
        service_data = {
            "server_id": server_id,
            "name": "test-service",
            "type": "web",
        }
        service_response = authenticated_client.post("/api/v1/services", json=service_data)
        assert service_response.status_code == 201
        service = service_response.json()
        service_id = service["id"]

        # Create deployment
        deployment_data = {
            "service_id": service_id,
            "version": "1.0.0",
            "environment": "dev",
        }
        deployment_response = authenticated_client.post("/api/v1/deployments", json=deployment_data)
        assert deployment_response.status_code == 201
        deployment = deployment_response.json()

        # Delete server
        delete_response = authenticated_client.delete(f"/api/v1/servers/{server_id}")
        assert delete_response.status_code == 200

        # Verify service is deleted (cascade)
        service_get = authenticated_client.get(f"/api/v1/services/{service_id}")
        assert service_get.status_code == 404

        # Verify deployment is deleted (cascade through service)
        deployment_get = authenticated_client.get(f"/api/v1/deployments/{deployment['id']}")
        assert deployment_get.status_code == 404
