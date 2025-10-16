"""
Deployment CRUD tests
"""

import pytest
from sqlalchemy.orm import Session

from app.crud import crud_deployment
from app.models.deployment import Deployment, DeploymentStatus, DeploymentType
from app.models.service import Service, ServiceType, ServiceStatus
from app.models.server import Server, ServerType, ServerStatus
from app.models.user import User


class TestDeploymentCRUD:
    """Test deployment CRUD operations"""

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

    def test_create_deployment(self, db_session: Session):
        """Test creating a deployment"""
        deployment_data = {
            "service_id": self.service.id,
            "deployed_by": self.test_user.id,
            "version": "1.0.0",
            "environment": "production",
            "type": DeploymentType.MANUAL,
            "status": DeploymentStatus.PENDING,
        }

        deployment = crud_deployment.create(db_session, obj_in=deployment_data)

        assert deployment.id is not None
        assert deployment.service_id == self.service.id
        assert deployment.version == "1.0.0"

    def test_get_deployment(self, db_session: Session):
        """Test getting a deployment by ID"""
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

        fetched_deployment = crud_deployment.get(db_session, id=deployment.id)

        assert fetched_deployment is not None
        assert fetched_deployment.id == deployment.id

    def test_get_by_service(self, db_session: Session):
        """Test getting deployments by service"""
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

        deployments = crud_deployment.get_by_service(db_session, service_id=self.service.id)

        assert len(deployments) == 2
        assert all(d.service_id == self.service.id for d in deployments)

    def test_get_by_environment(self, db_session: Session):
        """Test getting deployments by environment"""
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

        deployments = crud_deployment.get_by_environment(db_session, environment="production")

        assert len(deployments) == 1
        assert deployments[0].environment == "production"

    def test_get_successful_deployments(self, db_session: Session):
        """Test getting successful deployments"""
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

        deployments = crud_deployment.get_successful_deployments(
            db_session, service_id=self.service.id
        )

        assert len(deployments) == 1
        assert deployments[0].status == DeploymentStatus.SUCCESS

    def test_update_status(self, db_session: Session):
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

        updated = crud_deployment.update_status(
            db_session,
            deployment_id=deployment.id,
            status=DeploymentStatus.SUCCESS,
        )

        assert updated.status == DeploymentStatus.SUCCESS

    def test_get_latest_by_service(self, db_session: Session):
        """Test getting latest deployment for a service"""
        deployment1 = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="1.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.SUCCESS,
        )
        db_session.add(deployment1)
        db_session.commit()

        # Add newer deployment
        deployment2 = Deployment(
            service_id=self.service.id,
            deployed_by=self.test_user.id,
            version="2.0.0",
            environment="production",
            type=DeploymentType.MANUAL,
            status=DeploymentStatus.SUCCESS,
        )
        db_session.add(deployment2)
        db_session.commit()

        latest = crud_deployment.get_latest_by_service(db_session, service_id=self.service.id)

        assert latest is not None
        assert latest.version == "2.0.0"

    def test_delete_deployment(self, db_session: Session):
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

        crud_deployment.delete(db_session, id=deployment.id)

        deleted = crud_deployment.get(db_session, id=deployment.id)
        assert deleted is None
