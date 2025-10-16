"""
Deployment CRUD operations
배포 관련 CRUD 작업
"""

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.deployment import Deployment, DeploymentStatus, DeploymentType
from app.schemas.deployment import DeploymentCreate, DeploymentUpdate


class CRUDDeployment(CRUDBase[Deployment, DeploymentCreate, DeploymentUpdate]):
    """Deployment 모델에 대한 CRUD 작업"""

    def get_by_service(
        self,
        db: Session,
        *,
        service_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Deployment]:
        """
        서비스의 배포 이력 조회

        Args:
            db: 데이터베이스 세션
            service_id: 서비스 ID
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Deployment]: 배포 이력 목록
        """
        return (
            db.query(Deployment)
            .filter(Deployment.service_id == service_id)
            .order_by(Deployment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_environment(
        self,
        db: Session,
        *,
        environment: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[Deployment]:
        """
        환경별 배포 이력 조회

        Args:
            db: 데이터베이스 세션
            environment: 배포 환경 (dev, staging, production 등)
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Deployment]: 배포 이력 목록
        """
        return (
            db.query(Deployment)
            .filter(Deployment.environment == environment)
            .order_by(Deployment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self,
        db: Session,
        *,
        status: DeploymentStatus,
        skip: int = 0,
        limit: int = 100
    ) -> list[Deployment]:
        """
        상태별 배포 이력 조회

        Args:
            db: 데이터베이스 세션
            status: 배포 상태
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Deployment]: 배포 이력 목록
        """
        return (
            db.query(Deployment)
            .filter(Deployment.status == status)
            .order_by(Deployment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_type(
        self,
        db: Session,
        *,
        deployment_type: DeploymentType,
        skip: int = 0,
        limit: int = 100
    ) -> list[Deployment]:
        """
        타입별 배포 이력 조회

        Args:
            db: 데이터베이스 세션
            deployment_type: 배포 타입
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Deployment]: 배포 이력 목록
        """
        return (
            db.query(Deployment)
            .filter(Deployment.type == deployment_type)
            .order_by(Deployment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_user(
        self,
        db: Session,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Deployment]:
        """
        사용자의 배포 이력 조회

        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID (배포자)
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Deployment]: 배포 이력 목록
        """
        return (
            db.query(Deployment)
            .filter(Deployment.deployed_by == user_id)
            .order_by(Deployment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_latest_by_service(
        self,
        db: Session,
        *,
        service_id: int
    ) -> Deployment | None:
        """
        서비스의 최신 배포 조회

        Args:
            db: 데이터베이스 세션
            service_id: 서비스 ID

        Returns:
            Deployment | None: 최신 배포 또는 None
        """
        return (
            db.query(Deployment)
            .filter(Deployment.service_id == service_id)
            .order_by(Deployment.created_at.desc())
            .first()
        )

    def get_successful_deployments(
        self,
        db: Session,
        *,
        service_id: int | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[Deployment]:
        """
        성공한 배포 이력 조회

        Args:
            db: 데이터베이스 세션
            service_id: 서비스 ID (선택사항)
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Deployment]: 성공한 배포 이력 목록
        """
        query = db.query(Deployment).filter(
            Deployment.status == DeploymentStatus.SUCCESS
        )

        if service_id:
            query = query.filter(Deployment.service_id == service_id)

        return (
            query
            .order_by(Deployment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_rollback_deployments(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> list[Deployment]:
        """
        롤백 배포 이력 조회

        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Deployment]: 롤백 배포 이력 목록
        """
        return (
            db.query(Deployment)
            .filter(Deployment.rollback_from_id.isnot(None))
            .order_by(Deployment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_status(
        self,
        db: Session,
        *,
        deployment_id: int,
        status: DeploymentStatus
    ) -> Deployment | None:
        """
        배포 상태 변경

        Args:
            db: 데이터베이스 세션
            deployment_id: 배포 ID
            status: 새로운 상태

        Returns:
            Deployment | None: 업데이트된 배포 또는 None
        """
        deployment = self.get(db, id=deployment_id)
        if deployment:
            deployment.status = status
            db.add(deployment)
            db.commit()
            db.refresh(deployment)
        return deployment


# CRUD 인스턴스 생성
crud_deployment = CRUDDeployment(Deployment)
