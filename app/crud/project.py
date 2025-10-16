"""
Project CRUD operations
프로젝트 관련 CRUD 작업
"""

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    """Project 모델에 대한 CRUD 작업"""

    def get_by_key(self, db: Session, *, key: str) -> Project | None:
        """
        프로젝트 키로 조회

        Args:
            db: 데이터베이스 세션
            key: 프로젝트 키 (예: PROJ)

        Returns:
            Project | None: 조회된 프로젝트 또는 None
        """
        return db.query(Project).filter(Project.key == key.upper()).first()

    def get_by_team(
        self,
        db: Session,
        *,
        team_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Project]:
        """
        팀의 프로젝트 목록 조회

        Args:
            db: 데이터베이스 세션
            team_id: 팀 ID
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Project]: 프로젝트 목록
        """
        return (
            db.query(Project)
            .filter(Project.team_id == team_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self,
        db: Session,
        *,
        status: ProjectStatus,
        skip: int = 0,
        limit: int = 100
    ) -> list[Project]:
        """
        상태별 프로젝트 목록 조회

        Args:
            db: 데이터베이스 세션
            status: 프로젝트 상태
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Project]: 프로젝트 목록
        """
        return (
            db.query(Project)
            .filter(Project.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_projects(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> list[Project]:
        """
        활성 프로젝트 목록 조회 (ACTIVE 상태)

        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Project]: 활성 프로젝트 목록
        """
        return self.get_by_status(
            db,
            status=ProjectStatus.ACTIVE,
            skip=skip,
            limit=limit
        )

    def get_by_team_and_status(
        self,
        db: Session,
        *,
        team_id: int,
        status: ProjectStatus,
        skip: int = 0,
        limit: int = 100
    ) -> list[Project]:
        """
        팀과 상태로 프로젝트 목록 조회

        Args:
            db: 데이터베이스 세션
            team_id: 팀 ID
            status: 프로젝트 상태
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Project]: 프로젝트 목록
        """
        return (
            db.query(Project)
            .filter(
                Project.team_id == team_id,
                Project.status == status
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_status(
        self,
        db: Session,
        *,
        project_id: int,
        status: ProjectStatus
    ) -> Project | None:
        """
        프로젝트 상태 변경

        Args:
            db: 데이터베이스 세션
            project_id: 프로젝트 ID
            status: 새로운 상태

        Returns:
            Project | None: 업데이트된 프로젝트 또는 None
        """
        project = self.get(db, id=project_id)
        if project:
            project.status = status
            db.add(project)
            db.commit()
            db.refresh(project)
        return project


# CRUD 인스턴스 생성
crud_project = CRUDProject(Project)
