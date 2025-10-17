from typing import List, Optional
from sqlalchemy import String, ForeignKey, Text, Integer, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base, TimestampMixin


class ServiceType(str, enum.Enum):
    """서비스 타입"""
    WEB = "web"
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    WORKER = "worker"
    CRON = "cron"
    OTHER = "other"


class ServiceStatus(str, enum.Enum):
    """서비스 상태"""
    RUNNING = "running"
    STOPPED = "stopped"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    FAILED = "failed"


class Service(Base, TimestampMixin):
    """
    서비스 모델
    서버에서 실행되는 애플리케이션 서비스를 관리합니다.
    """
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, comment="서비스 ID")

    # Foreign Keys
    server_id: Mapped[int] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"),
        comment="서버 ID"
    )

    # 기본 정보
    name: Mapped[str] = mapped_column(
        String(200),
        index=True,
        comment="서비스 이름"
    )
    type: Mapped[ServiceType] = mapped_column(
        SQLEnum(ServiceType, native_enum=True, name='servicetype', values_callable=lambda x: [e.value for e in x]),
        default=ServiceType.WEB,
        index=True,
        comment="서비스 타입"
    )
    status: Mapped[ServiceStatus] = mapped_column(
        SQLEnum(ServiceStatus, native_enum=True, name='servicestatus', values_callable=lambda x: [e.value for e in x]),
        default=ServiceStatus.STOPPED,
        index=True,
        comment="서비스 상태"
    )

    # 버전 정보
    version: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="서비스 버전"
    )

    # 네트워크
    port: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="서비스 포트"
    )
    url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="서비스 URL"
    )

    # 프로세스 정보
    process_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="프로세스 이름"
    )
    pid: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="프로세스 ID"
    )

    # 컨테이너 정보
    container_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="컨테이너 ID (Docker 등)"
    )
    image_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="컨테이너 이미지 이름"
    )

    # 리소스
    cpu_limit: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="CPU 제한 (%)"
    )
    memory_limit_mb: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="메모리 제한 (MB)"
    )

    # 헬스체크
    health_check_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="헬스체크 URL"
    )
    health_check_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="헬스체크 활성화 여부"
    )

    # 환경 변수
    environment_variables: Mapped[Optional[dict]] = mapped_column(
        JSON,
        comment="환경 변수 (JSON)"
    )

    # 설정
    config_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="설정 파일 경로"
    )
    log_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        comment="로그 파일 경로"
    )

    # 자동 시작
    auto_start: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="서버 부팅 시 자동 시작 여부"
    )

    # 메모
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="서비스 설명"
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="비고"
    )

    # Relationships
    server: Mapped["Server"] = relationship(back_populates="services")
    deployments: Mapped[List["Deployment"]] = relationship(
        back_populates="service",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Service(id={self.id!r}, name={self.name!r}, type={self.type!r}, status={self.status!r})"
