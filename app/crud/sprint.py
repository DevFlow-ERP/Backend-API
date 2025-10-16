"""
Sprint CRUD operations
스프린트 관련 CRUD 작업
"""

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.sprint import Sprint, SprintStatus
from app.schemas.sprint import SprintCreate, SprintUpdate


class CRUDSprint(CRUDBase[Sprint, SprintCreate, SprintUpdate]):
    """Sprint 모델에 대한 CRUD 작업"""

    def get_by_project(
        self,
        db: Session,
        *,
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Sprint]:
        """
        프로젝트의 스프린트 목록 조회

        Args:
            db: 데이터베이스 세션
            project_id: 프로젝트 ID
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Sprint]: 스프린트 목록
        """
        return (
            db.query(Sprint)
            .filter(Sprint.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self,
        db: Session,
        *,
        status: SprintStatus,
        skip: int = 0,
        limit: int = 100
    ) -> list[Sprint]:
        """
        상태별 스프린트 목록 조회

        Args:
            db: 데이터베이스 세션
            status: 스프린트 상태
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Sprint]: 스프린트 목록
        """
        return (
            db.query(Sprint)
            .filter(Sprint.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_sprint(
        self,
        db: Session,
        *,
        project_id: int
    ) -> Sprint | None:
        """
        프로젝트의 활성 스프린트 조회

        Args:
            db: 데이터베이스 세션
            project_id: 프로젝트 ID

        Returns:
            Sprint | None: 활성 스프린트 또는 None
        """
        return (
            db.query(Sprint)
            .filter(
                Sprint.project_id == project_id,
                Sprint.status == SprintStatus.ACTIVE
            )
            .first()
        )

    def get_by_project_and_status(
        self,
        db: Session,
        *,
        project_id: int,
        status: SprintStatus,
        skip: int = 0,
        limit: int = 100
    ) -> list[Sprint]:
        """
        프로젝트와 상태로 스프린트 목록 조회

        Args:
            db: 데이터베이스 세션
            project_id: 프로젝트 ID
            status: 스프린트 상태
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Sprint]: 스프린트 목록
        """
        return (
            db.query(Sprint)
            .filter(
                Sprint.project_id == project_id,
                Sprint.status == status
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def start_sprint(
        self,
        db: Session,
        *,
        sprint_id: int
    ) -> Sprint | None:
        """
        스프린트 시작

        Args:
            db: 데이터베이스 세션
            sprint_id: 스프린트 ID

        Returns:
            Sprint | None: 시작된 스프린트 또는 None
        """
        sprint = self.get(db, id=sprint_id)
        if sprint:
            sprint.status = SprintStatus.ACTIVE
            db.add(sprint)
            db.commit()
            db.refresh(sprint)
        return sprint

    def complete_sprint(
        self,
        db: Session,
        *,
        sprint_id: int
    ) -> Sprint | None:
        """
        스프린트 완료

        Args:
            db: 데이터베이스 세션
            sprint_id: 스프린트 ID

        Returns:
            Sprint | None: 완료된 스프린트 또는 None
        """
        sprint = self.get(db, id=sprint_id)
        if sprint:
            sprint.status = SprintStatus.COMPLETED
            db.add(sprint)
            db.commit()
            db.refresh(sprint)
        return sprint


# CRUD 인스턴스 생성
crud_sprint = CRUDSprint(Sprint)
