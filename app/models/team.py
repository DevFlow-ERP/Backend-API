from typing import List, Optional
from sqlalchemy import String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base, TimestampMixin


class TeamRole(str, enum.Enum):
    """팀 내 역할"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Team(Base, TimestampMixin):
    """
    팀 모델
    프로젝트를 관리하는 팀 정보를 저장합니다.
    """
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, comment="팀 ID")

    # 기본 정보
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        comment="팀 이름"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="팀 설명"
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        comment="팀 슬러그 (URL용)"
    )

    # 메타데이터
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="팀 로고 이미지 URL"
    )

    # Relationships
    members: Mapped[List["TeamMember"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan"
    )
    projects: Mapped[List["Project"]] = relationship(
        back_populates="team",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Team(id={self.id!r}, name={self.name!r}, slug={self.slug!r})"


class TeamMember(Base, TimestampMixin):
    """
    팀 멤버 모델
    팀과 사용자의 다대다 관계를 나타내며, 팀 내 역할 정보를 포함합니다.
    """
    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(primary_key=True, comment="팀 멤버 ID")

    # Foreign Keys
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        comment="팀 ID"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        comment="사용자 ID"
    )

    # 역할
    # [FIX] values_callable 추가: DB의 값('owner')을 Enum 값으로 올바르게 매핑하도록 설정
    role: Mapped[TeamRole] = mapped_column(
        SQLEnum(
            TeamRole, 
            native_enum=False, 
            length=20, 
            values_callable=lambda x: [e.value for e in x]
        ),
        default=TeamRole.MEMBER,
        comment="팀 내 역할"
    )

    # Relationships
    team: Mapped["Team"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="team_memberships")

    def __repr__(self) -> str:
        return f"TeamMember(id={self.id!r}, team_id={self.team_id!r}, user_id={self.user_id!r}, role={self.role!r})"