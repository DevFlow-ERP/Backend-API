"""
Service API endpoint tests
서비스 API 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.server import Server, ServerType, ServerStatus
from app.models.service import Service, ServiceType, ServiceStatus


class TestServiceAPI:
    """Test service CRUD operations"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session):
        """Setup test data"""
        server = Server(
            name="test-server",
            hostname="test.example.com",
            ip_address="192.168.1.100",
            environment="dev",
            type=ServerType.VIRTUAL,
            status=ServerStatus.ACTIVE,
        )
        db_session.add(server)
        db_session.commit()
        db_session.refresh(server)

        self.server = server

    def test_create_service(self, authenticated_client: TestClient, db_session: Session):
        """Test creating a new service"""
        service_data = {
            "server_id": self.server.id,
            "name": "web-app",
            "type": "web",
            "status": "running",
            "version": "1.0.0",
            "port": 8080,
        }

        response = authenticated_client.post("/api/v1/services", json=service_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "web-app"
        assert data["server_id"] == self.server.id

    def test_list_services(self, authenticated_client: TestClient, db_session: Session):
        """Test listing services"""
        service = Service(
            server_id=self.server.id,
            name="web-app",
            type=ServiceType.WEB,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
        )
        db_session.add(service)
        db_session.commit()

        response = authenticated_client.get("/api/v1/services")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_get_service(self, authenticated_client: TestClient, db_session: Session):
        """Test getting a service by ID"""
        service = Service(
            server_id=self.server.id,
            name="web-app",
            type=ServiceType.WEB,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
        )
        db_session.add(service)
        db_session.commit()
        db_session.refresh(service)

        response = authenticated_client.get(f"/api/v1/services/{service.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == service.id
        assert data["name"] == "web-app"

    def test_update_service(self, authenticated_client: TestClient, db_session: Session):
        """Test updating a service"""
        service = Service(
            server_id=self.server.id,
            name="web-app",
            type=ServiceType.WEB,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
        )
        db_session.add(service)
        db_session.commit()
        db_session.refresh(service)

        update_data = {
            "name": "updated-app",
            "version": "2.0.0",
        }

        response = authenticated_client.put(f"/api/v1/services/{service.id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "updated-app"

    def test_delete_service(self, authenticated_client: TestClient, db_session: Session):
        """Test deleting a service"""
        service = Service(
            server_id=self.server.id,
            name="web-app",
            type=ServiceType.WEB,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
        )
        db_session.add(service)
        db_session.commit()
        db_session.refresh(service)

        response = authenticated_client.delete(f"/api/v1/services/{service.id}")
        assert response.status_code == 200

        # Verify service is deleted
        get_response = authenticated_client.get(f"/api/v1/services/{service.id}")
        assert get_response.status_code == 404

    def test_update_service_status(self, authenticated_client: TestClient, db_session: Session):
        """Test updating service status"""
        service = Service(
            server_id=self.server.id,
            name="web-app",
            type=ServiceType.WEB,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
        )
        db_session.add(service)
        db_session.commit()
        db_session.refresh(service)

        response = authenticated_client.patch(
            f"/api/v1/services/{service.id}/status?status=stopped"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "stopped"


class TestServiceFiltering:
    """Test service filtering operations"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session):
        """Setup test data"""
        server = Server(
            name="test-server",
            hostname="test.example.com",
            ip_address="192.168.1.100",
            environment="dev",
            type=ServerType.VIRTUAL,
            status=ServerStatus.ACTIVE,
        )
        db_session.add(server)
        db_session.commit()
        db_session.refresh(server)

        self.server = server

    def test_filter_by_server(self, authenticated_client: TestClient, db_session: Session):
        """Test filtering services by server"""
        service = Service(
            server_id=self.server.id,
            name="web-app",
            type=ServiceType.WEB,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
        )
        db_session.add(service)
        db_session.commit()

        response = authenticated_client.get(f"/api/v1/services/server/{self.server.id}")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["server_id"] == self.server.id

    def test_filter_by_type(self, authenticated_client: TestClient, db_session: Session):
        """Test filtering services by type"""
        service1 = Service(
            server_id=self.server.id,
            name="web-app",
            type=ServiceType.WEB,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
        )
        service2 = Service(
            server_id=self.server.id,
            name="db-service",
            type=ServiceType.DATABASE,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
        )
        db_session.add_all([service1, service2])
        db_session.commit()

        response = authenticated_client.get("/api/v1/services/type/web")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["type"] == "web"

    def test_filter_running_services(self, authenticated_client: TestClient, db_session: Session):
        """Test filtering running services"""
        service1 = Service(
            server_id=self.server.id,
            name="running-app",
            type=ServiceType.WEB,
            status=ServiceStatus.RUNNING,
            version="1.0.0",
        )
        service2 = Service(
            server_id=self.server.id,
            name="stopped-app",
            type=ServiceType.WEB,
            status=ServiceStatus.STOPPED,
            version="1.0.0",
        )
        db_session.add_all([service1, service2])
        db_session.commit()

        response = authenticated_client.get("/api/v1/services/status/running")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "running"
