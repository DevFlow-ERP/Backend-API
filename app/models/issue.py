from typing import Optional
from sqlalchemy import String, ForeignKey, Text, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base, TimestampMixin


class IssueType(str, enum.Enum):
    """이슈 타입"""
    TASK = "task"
    BUG = "bug"
    FEATURE = "feature"
    IMPROVEMENT = "improvement"
    EPIC = "epic"


class IssuePriority(str, enum.Enum):
    """이슈 우선순위"""
    LOWEST = "lowest"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HIGHEST = "highest"


class IssueStatus(str, enum.Enum):
    """이슈 상태"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    TESTING = "testing"
    DONE = "done"
    CLOSED = "closed"


class Issue(Base, TimestampMixin):
    """
    이슈 모델
    프로젝트의 작업, 버그, 기능 요청 등을 추적합니다.
    """
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True, comment="이슈 ID")

    # Foreign Keys
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        comment="프로젝트 ID"
    )
    sprint_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sprints.id", ondelete="SET NULL"),
        comment="스프린트 ID"
    )
    assignee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="담당자 ID"
    )
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        comment="생성자 ID"
    )

    # 기본 정보
    key: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        comment="이슈 키 (예: PROJ-123)"
    )
    title: Mapped[str] = mapped_column(
        String(500),
        comment="이슈 제목"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="이슈 설명"
    )

    # 분류
    type: Mapped[IssueType] = mapped_column(
        SQLEnum(IssueType, native_enum=False, length=20),
        default=IssueType.TASK,
        index=True,
        comment="이슈 타입"
    )
    priority: Mapped[IssuePriority] = mapped_column(
        SQLEnum(IssuePriority, native_enum=False, length=20),
        default=IssuePriority.MEDIUM,
        index=True,
        comment="우선순위"
    )
    status: Mapped[IssueStatus] = mapped_column(
        SQLEnum(IssueStatus, native_enum=False, length=20),
        default=IssueStatus.TODO,
        index=True,
        comment="상태"
    )

    # 추정 및 실제 시간
    estimate_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="예상 소요 시간 (시간)"
    )
    actual_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="실제 소요 시간 (시간)"
    )

    # 순서 (스프린트 내 우선순위)
    order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="정렬 순서"
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="issues")
    sprint: Mapped[Optional["Sprint"]] = relationship(back_populates="issues")
    assignee: Mapped[Optional["User"]] = relationship(
        foreign_keys=[assignee_id],
        back_populates="assigned_issues"
    )
    creator: Mapped["User"] = relationship(
        foreign_keys=[creator_id],
        back_populates="created_issues"
    )

    def __repr__(self) -> str:
        return f"Issue(id={self.id!r}, key={self.key!r}, title={self.title!r}, status={self.status!r})"
