from typing import List, Optional
from sqlalchemy import String, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base, TimestampMixin


class ProjectStatus(str, enum.Enum):
    """프로젝트 상태"""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Project(Base, TimestampMixin):
    """
    프로젝트 모델
    개발 프로젝트 정보를 저장합니다.
    """
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, comment="프로젝트 ID")

    # Foreign Keys
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        comment="팀 ID"
    )

    # 기본 정보
    name: Mapped[str] = mapped_column(
        String(200),
        index=True,
        comment="프로젝트 이름"
    )
    key: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        index=True,
        comment="프로젝트 키 (예: PROJ, DEV)"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="프로젝트 설명"
    )

    # 상태
    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(ProjectStatus, native_enum=False, length=20),
        default=ProjectStatus.PLANNING,
        index=True,
        comment="프로젝트 상태"
    )

    # 리포지토리 정보
    repository_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="Git 리포지토리 URL"
    )
    documentation_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="문서 URL"
    )

    # 메타데이터
    icon_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="프로젝트 아이콘 URL"
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(7),
        comment="프로젝트 색상 (HEX)"
    )

    # Relationships
    team: Mapped["Team"] = relationship(back_populates="projects")
    sprints: Mapped[List["Sprint"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )
    issues: Mapped[List["Issue"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Project(id={self.id!r}, key={self.key!r}, name={self.name!r}, status={self.status!r})"
