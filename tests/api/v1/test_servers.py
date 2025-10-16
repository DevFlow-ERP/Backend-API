"""
Server API endpoint tests
서버 API 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.server import Server, ServerType, ServerStatus


class TestServerAPI:
    """Test server CRUD operations"""

    def test_create_server(self, authenticated_client: TestClient, db_session: Session):
        """Test creating a new server"""
        server_data = {
            "name": "test-server",
            "hostname": "test.example.com",
            "ip_address": "192.168.1.100",
            "environment": "dev",
            "type": "virtual",
            "status": "active",
            "cpu_cores": 4,
            "memory_gb": 16,
        }

        response = authenticated_client.post("/api/v1/servers", json=server_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "test-server"
        assert data["ip_address"] == "192.168.1.100"

    def test_list_servers(self, authenticated_client: TestClient, db_session: Session):
        """Test listing servers"""
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

        response = authenticated_client.get("/api/v1/servers")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

    def test_get_server(self, authenticated_client: TestClient, db_session: Session):
        """Test getting a server by ID"""
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

        response = authenticated_client.get(f"/api/v1/servers/{server.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == server.id
        assert data["name"] == "test-server"

    def test_update_server(self, authenticated_client: TestClient, db_session: Session):
        """Test updating a server"""
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

        update_data = {
            "name": "updated-server",
            "cpu_cores": 8,
            "memory_gb": 32,
        }

        response = authenticated_client.put(f"/api/v1/servers/{server.id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "updated-server"

    def test_delete_server(self, authenticated_client: TestClient, db_session: Session):
        """Test deleting a server"""
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

        response = authenticated_client.delete(f"/api/v1/servers/{server.id}")
        assert response.status_code == 200

        # Verify server is deleted
        get_response = authenticated_client.get(f"/api/v1/servers/{server.id}")
        assert get_response.status_code == 404

    def test_update_server_status(self, authenticated_client: TestClient, db_session: Session):
        """Test updating server status"""
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

        response = authenticated_client.patch(
            f"/api/v1/servers/{server.id}/status?status=maintenance"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "maintenance"


class TestServerFiltering:
    """Test server filtering operations"""

    def test_filter_by_environment(self, authenticated_client: TestClient, db_session: Session):
        """Test filtering servers by environment"""
        server1 = Server(
            name="prod-server",
            hostname="prod.example.com",
            ip_address="192.168.1.10",
            environment="production",
            type=ServerType.PHYSICAL,
            status=ServerStatus.ACTIVE,
        )
        server2 = Server(
            name="dev-server",
            hostname="dev.example.com",
            ip_address="192.168.1.100",
            environment="dev",
            type=ServerType.VIRTUAL,
            status=ServerStatus.ACTIVE,
        )
        db_session.add_all([server1, server2])
        db_session.commit()

        response = authenticated_client.get("/api/v1/servers/environment/production")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["environment"] == "production"

    def test_filter_by_type(self, authenticated_client: TestClient, db_session: Session):
        """Test filtering servers by type"""
        server1 = Server(
            name="physical-server",
            hostname="physical.example.com",
            ip_address="192.168.1.10",
            environment="production",
            type=ServerType.PHYSICAL,
            status=ServerStatus.ACTIVE,
        )
        server2 = Server(
            name="virtual-server",
            hostname="virtual.example.com",
            ip_address="192.168.1.100",
            environment="dev",
            type=ServerType.VIRTUAL,
            status=ServerStatus.ACTIVE,
        )
        db_session.add_all([server1, server2])
        db_session.commit()

        response = authenticated_client.get("/api/v1/servers/type/virtual")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["type"] == "virtual"
