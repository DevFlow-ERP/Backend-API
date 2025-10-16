"""
Deployment API tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.deployment import Deployment, DeploymentStatus, DeploymentType
from app.models.service import Service, ServiceType, ServiceStatus
from app.models.server import Server, ServerType, ServerStatus
from app.models.user import User


class TestDeploymentAPI:
    """Test deployment endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session, test_user: User):
        """Setup test data"""
        # Create server
        server = Server(
            name="test-server",
            hostname="test.example.com",
            ip_address="192.168.1.100",
            environment="production",
            type=ServerType.VIRTUAL,
            status=ServerStatus.ACTIVE,
        )
        db_session.add(server)
        db_session.commit()
        db_session.refresh(server)

        # Create service
        service = Service(
            server_id=server.id,
            name="test-service",
            type=ServiceType.WEB,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
        )
        db_session.add(service)
        db_session.commit()
        db_session.refresh(service)

        self.server = server
        self.service = service
        self.test_user = test_user

    def test_create_deployment(self, authenticated_client: TestClient, db_session: Session):
        """Test creating a new deployment"""
        deployment_data = {
            "service_id": self.service.id,
            "version": "2.0.0",
            "environment": "production",
            "type": "manual",
            "status": "pending",
            "commit_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
            "branch": "main",
            "notes": "Test deployment",
        }

        response = authenticated_client.post("/api/v1/deployments", json=deployment_data)
        assert response.status_code == 201

        data = response.json()
        assert data["service_id"] == self.service.id
        assert data["version"] == "2.0.0"
        assert data["deployed_by"] == self.test_user.id

    def test_list_deployments(self, authenticated_client: TestClient, db_session: Session):
        """Test listing deployments"""
        # Create test deployments
        deployment1 = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.SUCCESS,
        )
        deployment2 = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.1.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.SUCCESS,
        )
        db_session.add_all([deployment1, deployment2])
        db_session.commit()

        response = authenticated_client.get("/api/v1/deployments")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) == 2

    def test_get_deployment(self, authenticated_client: TestClient, db_session: Session):
        """Test getting a single deployment"""
        deployment = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.SUCCESS,
        )
        db_session.add(deployment)
        db_session.commit()
        db_session.refresh(deployment)

        response = authenticated_client.get(f"/api/v1/deployments/{deployment.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == deployment.id
        assert data["version"] == "1.0.0"

    def test_update_deployment_status(self, authenticated_client: TestClient, db_session: Session):
        """Test updating deployment status"""
        deployment = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.PENDING,
        )
        db_session.add(deployment)
        db_session.commit()
        db_session.refresh(deployment)

        response = authenticated_client.patch(
            f"/api/v1/deployments/{deployment.id}/status?status=success"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["completed_at"] is not None

    def test_rollback_deployment(self, authenticated_client: TestClient, db_session: Session):
        """Test rollback to previous deployment"""
        # Create successful deployment to rollback to
        target_deployment = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.SUCCESS,
            commit_hash="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
            branch="main",
        )
        db_session.add(target_deployment)
        db_session.commit()
        db_session.refresh(target_deployment)

        # Perform rollback
        response = authenticated_client.post(
            f"/api/v1/deployments/{target_deployment.id}/rollback?notes=Critical+bug+found"
        )
        assert response.status_code == 201

        data = response.json()
        assert data["type"] == "rollback"
        assert data["version"] == "1.0.0"
        assert data["rollback_from_id"] == target_deployment.id
        assert "Critical bug found" in data["notes"]

    def test_rollback_to_failed_deployment(self, authenticated_client: TestClient, db_session: Session):
        """Test rollback to failed deployment should fail"""
        failed_deployment = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.FAILED,
        )
        db_session.add(failed_deployment)
        db_session.commit()
        db_session.refresh(failed_deployment)

        response = authenticated_client.post(f"/api/v1/deployments/{failed_deployment.id}/rollback")
        assert response.status_code == 400

    def test_delete_deployment(self, authenticated_client: TestClient, db_session: Session):
        """Test deleting a deployment"""
        deployment = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.SUCCESS,
        )
        db_session.add(deployment)
        db_session.commit()
        db_session.refresh(deployment)

        response = authenticated_client.delete(f"/api/v1/deployments/{deployment.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Verify deployment is deleted
        db_deployment = db_session.get(Deployment, deployment.id)
        assert db_deployment is None


class TestDeploymentFiltering:
    """Test deployment filtering"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session, test_user: User):
        """Setup test data"""
        server = Server(
            name="test-server",
            hostname="test.example.com",
            ip_address="192.168.1.100",
            environment="production",
            type=ServerType.VIRTUAL,
            status=ServerStatus.ACTIVE,
        )
        db_session.add(server)
        db_session.commit()

        service = Service(
            server_id=server.id,
            name="test-service",
            type=ServiceType.WEB,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
        )
        db_session.add(service)
        db_session.commit()

        self.service = service
        self.test_user = test_user

    def test_filter_by_service(self, authenticated_client: TestClient, db_session: Session):
        """Test filtering deployments by service"""
        deployment = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.SUCCESS,
        )
        db_session.add(deployment)
        db_session.commit()

        response = authenticated_client.get(f"/api/v1/deployments/service/{self.service.id}")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["service_id"] == self.service.id

    def test_filter_by_environment(self, authenticated_client: TestClient, db_session: Session):
        """Test filtering deployments by environment"""
        deployment1 = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.SUCCESS,
        )
        deployment2 = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="staging",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.SUCCESS,
        )
        db_session.add_all([deployment1, deployment2])
        db_session.commit()

        response = authenticated_client.get("/api/v1/deployments/environment/production")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["environment"] == "production"

    def test_list_successful_deployments(self, authenticated_client: TestClient, db_session: Session):
        """Test listing successful deployments"""
        deployment1 = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.SUCCESS,
        )
        deployment2 = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="2.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.FAILED,
        )
        db_session.add_all([deployment1, deployment2])
        db_session.commit()

        response = authenticated_client.get("/api/v1/deployments/status/success")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "success"

    def test_list_rollback_deployments(self, authenticated_client: TestClient, db_session: Session):
        """Test listing rollback deployments"""
        target = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.SUCCESS,
        )
        db_session.add(target)
        db_session.commit()

        rollback = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="production",
            type=DeploymentType.ROLLBACK,
            status=DeploymentStatus.SUCCESS,
            rollback_from_id=target.id,
        )
        db_session.add(rollback)
        db_session.commit()

        response = authenticated_client.get("/api/v1/deployments/type/rollback")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["type"] == "rollback"
