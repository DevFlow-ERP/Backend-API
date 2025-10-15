from typing import List, Optional
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    사용자 모델
    Authentik과 연동되는 사용자 정보를 저장합니다.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, comment="사용자 ID")

    # Authentik 연동 필드
    authentik_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        comment="Authentik 사용자 ID"
    )

    # 기본 정보
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        comment="이메일"
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        comment="사용자명"
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="전체 이름"
    )

    # 프로필 정보
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="프로필 이미지 URL"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="전화번호"
    )

    # 상태
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="활성 상태"
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="관리자 여부"
    )

    # Relationships
    team_memberships: Mapped[List["TeamMember"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    assigned_issues: Mapped[List["Issue"]] = relationship(
        foreign_keys="Issue.assignee_id",
        back_populates="assignee"
    )
    created_issues: Mapped[List["Issue"]] = relationship(
        foreign_keys="Issue.creator_id",
        back_populates="creator"
    )
    deployments: Mapped[List["Deployment"]] = relationship(
        back_populates="deployed_by_user"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, email={self.email!r})"
