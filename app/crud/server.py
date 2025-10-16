"""
Server CRUD operations
서버 관련 CRUD 작업
"""

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.server import Server, ServerStatus, ServerType
from app.schemas.server import ServerCreate, ServerUpdate


class CRUDServer(CRUDBase[Server, ServerCreate, ServerUpdate]):
    """Server 모델에 대한 CRUD 작업"""

    def get_by_hostname(self, db: Session, *, hostname: str) -> Server | None:
        """
        호스트명으로 서버 조회

        Args:
            db: 데이터베이스 세션
            hostname: 호스트명

        Returns:
            Server | None: 조회된 서버 또는 None
        """
        return db.query(Server).filter(Server.hostname == hostname).first()

    def get_by_ip_address(self, db: Session, *, ip_address: str) -> Server | None:
        """
        IP 주소로 서버 조회

        Args:
            db: 데이터베이스 세션
            ip_address: IP 주소

        Returns:
            Server | None: 조회된 서버 또는 None
        """
        return db.query(Server).filter(Server.ip_address == ip_address).first()

    def get_by_environment(
        self,
        db: Session,
        *,
        environment: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[Server]:
        """
        환경별 서버 목록 조회

        Args:
            db: 데이터베이스 세션
            environment: 환경 (dev, staging, production 등)
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Server]: 서버 목록
        """
        return (
            db.query(Server)
            .filter(Server.environment == environment)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_type(
        self,
        db: Session,
        *,
        server_type: ServerType,
        skip: int = 0,
        limit: int = 100
    ) -> list[Server]:
        """
        타입별 서버 목록 조회

        Args:
            db: 데이터베이스 세션
            server_type: 서버 타입
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Server]: 서버 목록
        """
        return (
            db.query(Server)
            .filter(Server.type == server_type)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self,
        db: Session,
        *,
        status: ServerStatus,
        skip: int = 0,
        limit: int = 100
    ) -> list[Server]:
        """
        상태별 서버 목록 조회

        Args:
            db: 데이터베이스 세션
            status: 서버 상태
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Server]: 서버 목록
        """
        return (
            db.query(Server)
            .filter(Server.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_servers(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> list[Server]:
        """
        활성 서버 목록 조회

        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Server]: 활성 서버 목록
        """
        return self.get_by_status(
            db,
            status=ServerStatus.ACTIVE,
            skip=skip,
            limit=limit
        )

    def update_status(
        self,
        db: Session,
        *,
        server_id: int,
        status: ServerStatus
    ) -> Server | None:
        """
        서버 상태 변경

        Args:
            db: 데이터베이스 세션
            server_id: 서버 ID
            status: 새로운 상태

        Returns:
            Server | None: 업데이트된 서버 또는 None
        """
        server = self.get(db, id=server_id)
        if server:
            server.status = status
            db.add(server)
            db.commit()
            db.refresh(server)
        return server


# CRUD 인스턴스 생성
crud_server = CRUDServer(Server)
