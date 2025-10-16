"""
Service CRUD operations
서비스 관련 CRUD 작업
"""

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.service import Service, ServiceStatus, ServiceType
from app.schemas.service import ServiceCreate, ServiceUpdate


class CRUDService(CRUDBase[Service, ServiceCreate, ServiceUpdate]):
    """Service 모델에 대한 CRUD 작업"""

    def get_by_name(self, db: Session, *, name: str) -> Service | None:
        """
        서비스 이름으로 조회

        Args:
            db: 데이터베이스 세션
            name: 서비스 이름

        Returns:
            Service | None: 조회된 서비스 또는 None
        """
        return db.query(Service).filter(Service.name == name).first()

    def get_by_server(
        self,
        db: Session,
        *,
        server_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Service]:
        """
        서버의 서비스 목록 조회

        Args:
            db: 데이터베이스 세션
            server_id: 서버 ID
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Service]: 서비스 목록
        """
        return (
            db.query(Service)
            .filter(Service.server_id == server_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_type(
        self,
        db: Session,
        *,
        service_type: ServiceType,
        skip: int = 0,
        limit: int = 100
    ) -> list[Service]:
        """
        타입별 서비스 목록 조회

        Args:
            db: 데이터베이스 세션
            service_type: 서비스 타입
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Service]: 서비스 목록
        """
        return (
            db.query(Service)
            .filter(Service.type == service_type)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self,
        db: Session,
        *,
        status: ServiceStatus,
        skip: int = 0,
        limit: int = 100
    ) -> list[Service]:
        """
        상태별 서비스 목록 조회

        Args:
            db: 데이터베이스 세션
            status: 서비스 상태
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Service]: 서비스 목록
        """
        return (
            db.query(Service)
            .filter(Service.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_running_services(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> list[Service]:
        """
        실행 중인 서비스 목록 조회

        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Service]: 실행 중인 서비스 목록
        """
        return self.get_by_status(
            db,
            status=ServiceStatus.RUNNING,
            skip=skip,
            limit=limit
        )

    def get_by_port(self, db: Session, *, port: int) -> Service | None:
        """
        포트 번호로 서비스 조회

        Args:
            db: 데이터베이스 세션
            port: 포트 번호

        Returns:
            Service | None: 조회된 서비스 또는 None
        """
        return db.query(Service).filter(Service.port == port).first()

    def get_by_container_id(
        self,
        db: Session,
        *,
        container_id: str
    ) -> Service | None:
        """
        컨테이너 ID로 서비스 조회

        Args:
            db: 데이터베이스 세션
            container_id: 컨테이너 ID

        Returns:
            Service | None: 조회된 서비스 또는 None
        """
        return (
            db.query(Service)
            .filter(Service.container_id == container_id)
            .first()
        )

    def update_status(
        self,
        db: Session,
        *,
        service_id: int,
        status: ServiceStatus
    ) -> Service | None:
        """
        서비스 상태 변경

        Args:
            db: 데이터베이스 세션
            service_id: 서비스 ID
            status: 새로운 상태

        Returns:
            Service | None: 업데이트된 서비스 또는 None
        """
        service = self.get(db, id=service_id)
        if service:
            service.status = status
            db.add(service)
            db.commit()
            db.refresh(service)
        return service


# CRUD 인스턴스 생성
crud_service = CRUDService(Service)
