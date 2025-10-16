"""
Team API endpoint tests
팀 API 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.team import Team


class TestTeamAPI:
    """Test team CRUD operations"""

    def test_create_team(self, authenticated_client: TestClient, db_session: Session):
        """Test creating a new team"""
        team_data = {
            "name": "Dev Team",
            "slug": "dev-team",
            "description": "Development team",
        }

        response = authenticated_client.post("/api/v1/teams", json=team_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Dev Team"
        assert data["slug"] == "dev-team"

    def test_list_teams(self, authenticated_client: TestClient, db_session: Session, test_team):
        """Test listing teams"""
        response = authenticated_client.get("/api/v1/teams")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "meta" in data
        assert len(data["items"]) >= 1

    def test_get_my_teams(self, authenticated_client: TestClient, db_session: Session, test_team):
        """Test getting my teams"""
        response = authenticated_client.get("/api/v1/teams/my")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data

    def test_get_team(self, authenticated_client: TestClient, db_session: Session, test_team):
        """Test getting a team by ID"""
        response = authenticated_client.get(f"/api/v1/teams/{test_team.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == test_team.id
        assert data["name"] == test_team.name

    def test_update_team(self, authenticated_client: TestClient, db_session: Session, test_team):
        """Test updating a team"""
        update_data = {
            "name": "Updated Team Name",
            "description": "Updated description",
        }

        response = authenticated_client.put(f"/api/v1/teams/{test_team.id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Team Name"
        assert data["description"] == "Updated description"

    def test_delete_team(self, authenticated_client: TestClient, db_session: Session, test_team):
        """Test deleting a team"""
        response = authenticated_client.delete(f"/api/v1/teams/{test_team.id}")
        assert response.status_code == 200

        # Verify team is deleted
        get_response = authenticated_client.get(f"/api/v1/teams/{test_team.id}")
        assert get_response.status_code == 404

    def test_get_nonexistent_team(self, authenticated_client: TestClient):
        """Test getting a nonexistent team"""
        response = authenticated_client.get("/api/v1/teams/99999")
        assert response.status_code == 404


class TestTeamMemberAPI:
    """Test team member operations"""

    def test_get_team_members(self, authenticated_client: TestClient, db_session: Session, test_team):
        """Test getting team members"""
        response = authenticated_client.get(f"/api/v1/teams/{test_team.id}/members")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data

    def test_add_team_member(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        test_team,
        test_superuser: User
    ):
        """Test adding a member to team"""
        member_data = {
            "user_id": test_superuser.id,
            "role": "member",
        }

        response = authenticated_client.post(
            f"/api/v1/teams/{test_team.id}/members",
            json=member_data
        )
        assert response.status_code == 201

        data = response.json()
        assert data["user_id"] == test_superuser.id
        assert data["role"] == "member"

    def test_update_member_role(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        test_team,
        test_superuser: User
    ):
        """Test updating member role"""
        # First add member
        member_data = {"user_id": test_superuser.id, "role": "member"}
        authenticated_client.post(f"/api/v1/teams/{test_team.id}/members", json=member_data)

        # Update role
        response = authenticated_client.patch(
            f"/api/v1/teams/{test_team.id}/members/{test_superuser.id}/role",
            json={"role": "admin"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["role"] == "admin"

    def test_remove_team_member(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        test_team,
        test_superuser: User
    ):
        """Test removing a member from team"""
        # First add member
        member_data = {"user_id": test_superuser.id, "role": "member"}
        authenticated_client.post(f"/api/v1/teams/{test_team.id}/members", json=member_data)

        # Remove member
        response = authenticated_client.delete(
            f"/api/v1/teams/{test_team.id}/members/{test_superuser.id}"
        )
        assert response.status_code == 200
