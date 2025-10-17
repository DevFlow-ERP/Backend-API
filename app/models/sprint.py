from typing import List, Optional
from datetime import date
from sqlalchemy import String, ForeignKey, Text, Date, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base, TimestampMixin


class SprintStatus(str, enum.Enum):
    """스프린트 상태"""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Sprint(Base, TimestampMixin):
    """
    스프린트 모델
    애자일 스프린트 정보를 저장합니다.
    """
    __tablename__ = "sprints"

    id: Mapped[int] = mapped_column(primary_key=True, comment="스프린트 ID")

    # Foreign Keys
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        comment="프로젝트 ID"
    )

    # 기본 정보
    name: Mapped[str] = mapped_column(
        String(200),
        comment="스프린트 이름"
    )
    goal: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="스프린트 목표"
    )

    # 기간
    start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="시작일"
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        comment="종료일"
    )

    # 상태
    status: Mapped[SprintStatus] = mapped_column(
        SQLEnum(SprintStatus, native_enum=True, name='sprint_status', values_callable=lambda x: [e.value for e in x]),
        default=SprintStatus.PLANNED,
        index=True,
        comment="스프린트 상태"
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="sprints")
    issues: Mapped[List["Issue"]] = relationship(
        back_populates="sprint",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Sprint(id={self.id!r}, name={self.name!r}, status={self.status!r})"
