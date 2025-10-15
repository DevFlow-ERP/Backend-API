from typing import Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base, TimestampMixin


class DeploymentStatus(str, enum.Enum):
    """배포 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeploymentType(str, enum.Enum):
    """배포 타입"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    ROLLBACK = "rollback"


class Deployment(Base, TimestampMixin):
    """
    배포 모델
    서비스의 배포 이력을 추적합니다.
    """
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(primary_key=True, comment="배포 ID")

    # Foreign Keys
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"),
        comment="서비스 ID"
    )
    deployed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        comment="배포 실행자 ID"
    )

    # 배포 정보
    version: Mapped[str] = mapped_column(
        String(50),
        comment="배포 버전"
    )
    commit_hash: Mapped[Optional[str]] = mapped_column(
        String(40),
        comment="Git 커밋 해시"
    )
    branch: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Git 브랜치"
    )
    tag: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Git 태그"
    )

    # 배포 타입 및 상태
    type: Mapped[DeploymentType] = mapped_column(
        SQLEnum(DeploymentType, native_enum=False, length=20),
        default=DeploymentType.MANUAL,
        comment="배포 타입"
    )
    status: Mapped[DeploymentStatus] = mapped_column(
        SQLEnum(DeploymentStatus, native_enum=False, length=20),
        default=DeploymentStatus.PENDING,
        index=True,
        comment="배포 상태"
    )

    # 시간 정보
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="배포 시작 시간"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="배포 완료 시간"
    )

    # 환경
    environment: Mapped[str] = mapped_column(
        String(50),
        index=True,
        comment="배포 환경 (dev, staging, production)"
    )

    # 롤백 정보
    rollback_from_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("deployments.id", ondelete="SET NULL"),
        comment="롤백 대상 배포 ID"
    )

    # 메모
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="배포 메모"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="에러 메시지 (실패 시)"
    )

    # 배포 로그
    log_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="배포 로그 URL"
    )

    # Relationships
    service: Mapped["Service"] = relationship(back_populates="deployments")
    deployed_by_user: Mapped["User"] = relationship(back_populates="deployments")
    rollback_from: Mapped[Optional["Deployment"]] = relationship(
        remote_side=[id],
        foreign_keys=[rollback_from_id]
    )

    def __repr__(self) -> str:
        return f"Deployment(id={self.id!r}, version={self.version!r}, status={self.status!r}, environment={self.environment!r})"
