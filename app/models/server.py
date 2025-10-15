from typing import List, Optional
from sqlalchemy import String, Text, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base, TimestampMixin


class ServerType(str, enum.Enum):
    """서버 타입"""
    PHYSICAL = "physical"
    VIRTUAL = "virtual"
    CLOUD = "cloud"
    CONTAINER = "container"


class ServerStatus(str, enum.Enum):
    """서버 상태"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"


class Server(Base, TimestampMixin):
    """
    서버 모델
    물리 서버, 가상 서버, 클라우드 인스턴스 등의 정보를 저장합니다.
    """
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(primary_key=True, comment="서버 ID")

    # 기본 정보
    name: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        index=True,
        comment="서버 이름"
    )
    hostname: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        comment="호스트명"
    )
    ip_address: Mapped[str] = mapped_column(
        String(45),
        comment="IP 주소 (IPv4/IPv6)"
    )

    # 분류
    type: Mapped[ServerType] = mapped_column(
        SQLEnum(ServerType, native_enum=False, length=20),
        default=ServerType.VIRTUAL,
        index=True,
        comment="서버 타입"
    )
    status: Mapped[ServerStatus] = mapped_column(
        SQLEnum(ServerStatus, native_enum=False, length=20),
        default=ServerStatus.ACTIVE,
        index=True,
        comment="서버 상태"
    )

    # 환경
    environment: Mapped[str] = mapped_column(
        String(50),
        index=True,
        comment="환경 (dev, staging, production)"
    )

    # 사양
    cpu_cores: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="CPU 코어 수"
    )
    memory_gb: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="메모리 (GB)"
    )
    disk_gb: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="디스크 용량 (GB)"
    )

    # 운영체제
    os_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="운영체제 이름"
    )
    os_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="운영체제 버전"
    )

    # 클라우드 정보
    provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="클라우드 제공자 (AWS, GCP, Azure 등)"
    )
    region: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="리전"
    )
    instance_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="인스턴스 ID"
    )

    # 접근 정보
    ssh_port: Mapped[int] = mapped_column(
        Integer,
        default=22,
        comment="SSH 포트"
    )
    ssh_user: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="SSH 사용자명"
    )

    # 모니터링
    monitoring_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="모니터링 활성화 여부"
    )
    monitoring_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="모니터링 대시보드 URL"
    )

    # 메모
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="서버 설명"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="비고"
    )

    # Relationships
    services: Mapped[List["Service"]] = relationship(
        back_populates="server",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Server(id={self.id!r}, name={self.name!r}, hostname={self.hostname!r}, status={self.status!r})"
