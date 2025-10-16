"""
Issue CRUD operations
이슈 관련 CRUD 작업
"""

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.issue import Issue, IssueStatus, IssueType, IssuePriority
from app.schemas.issue import IssueCreate, IssueUpdate


class CRUDIssue(CRUDBase[Issue, IssueCreate, IssueUpdate]):
    """Issue 모델에 대한 CRUD 작업"""

    def get_by_key(self, db: Session, *, key: str) -> Issue | None:
        """
        이슈 키로 조회 (예: PROJ-123)

        Args:
            db: 데이터베이스 세션
            key: 이슈 키

        Returns:
            Issue | None: 조회된 이슈 또는 None
        """
        return db.query(Issue).filter(Issue.key == key.upper()).first()

    def get_by_project(
        self,
        db: Session,
        *,
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Issue]:
        """
        프로젝트의 이슈 목록 조회

        Args:
            db: 데이터베이스 세션
            project_id: 프로젝트 ID
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Issue]: 이슈 목록
        """
        return (
            db.query(Issue)
            .filter(Issue.project_id == project_id)
            .order_by(Issue.order)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_sprint(
        self,
        db: Session,
        *,
        sprint_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Issue]:
        """
        스프린트의 이슈 목록 조회

        Args:
            db: 데이터베이스 세션
            sprint_id: 스프린트 ID
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Issue]: 이슈 목록
        """
        return (
            db.query(Issue)
            .filter(Issue.sprint_id == sprint_id)
            .order_by(Issue.order)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_backlog(
        self,
        db: Session,
        *,
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Issue]:
        """
        프로젝트 백로그 조회 (스프린트 미할당 이슈)

        Args:
            db: 데이터베이스 세션
            project_id: 프로젝트 ID
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Issue]: 백로그 이슈 목록
        """
        return (
            db.query(Issue)
            .filter(
                Issue.project_id == project_id,
                Issue.sprint_id.is_(None)
            )
            .order_by(Issue.order)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_assignee(
        self,
        db: Session,
        *,
        assignee_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[Issue]:
        """
        담당자의 이슈 목록 조회

        Args:
            db: 데이터베이스 세션
            assignee_id: 담당자 ID
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Issue]: 이슈 목록
        """
        return (
            db.query(Issue)
            .filter(Issue.assignee_id == assignee_id)
            .order_by(Issue.order)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_status(
        self,
        db: Session,
        *,
        status: IssueStatus,
        skip: int = 0,
        limit: int = 100
    ) -> list[Issue]:
        """
        상태별 이슈 목록 조회

        Args:
            db: 데이터베이스 세션
            status: 이슈 상태
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Issue]: 이슈 목록
        """
        return (
            db.query(Issue)
            .filter(Issue.status == status)
            .order_by(Issue.order)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_type(
        self,
        db: Session,
        *,
        issue_type: IssueType,
        skip: int = 0,
        limit: int = 100
    ) -> list[Issue]:
        """
        타입별 이슈 목록 조회

        Args:
            db: 데이터베이스 세션
            issue_type: 이슈 타입
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Issue]: 이슈 목록
        """
        return (
            db.query(Issue)
            .filter(Issue.type == issue_type)
            .order_by(Issue.order)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_priority(
        self,
        db: Session,
        *,
        priority: IssuePriority,
        skip: int = 0,
        limit: int = 100
    ) -> list[Issue]:
        """
        우선순위별 이슈 목록 조회

        Args:
            db: 데이터베이스 세션
            priority: 우선순위
            skip: 건너뛸 레코드 수
            limit: 조회할 최대 레코드 수

        Returns:
            list[Issue]: 이슈 목록
        """
        return (
            db.query(Issue)
            .filter(Issue.priority == priority)
            .order_by(Issue.order)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_status(
        self,
        db: Session,
        *,
        issue_id: int,
        status: IssueStatus
    ) -> Issue | None:
        """
        이슈 상태 변경

        Args:
            db: 데이터베이스 세션
            issue_id: 이슈 ID
            status: 새로운 상태

        Returns:
            Issue | None: 업데이트된 이슈 또는 None
        """
        issue = self.get(db, id=issue_id)
        if issue:
            issue.status = status
            db.add(issue)
            db.commit()
            db.refresh(issue)
        return issue

    def assign_to_sprint(
        self,
        db: Session,
        *,
        issue_id: int,
        sprint_id: int | None
    ) -> Issue | None:
        """
        이슈를 스프린트에 할당 (None이면 백로그로 이동)

        Args:
            db: 데이터베이스 세션
            issue_id: 이슈 ID
            sprint_id: 스프린트 ID (None이면 백로그)

        Returns:
            Issue | None: 업데이트된 이슈 또는 None
        """
        issue = self.get(db, id=issue_id)
        if issue:
            issue.sprint_id = sprint_id
            db.add(issue)
            db.commit()
            db.refresh(issue)
        return issue


# CRUD 인스턴스 생성
crud_issue = CRUDIssue(Issue)
