"""
Server Pydantic schemas
서버 관련 스키마를 정의합니다.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.server import ServerType, ServerStatus
from app.schemas.common import TimestampSchema


class ServerBase(BaseModel):
    """
    Server 기본 스키마
    공통 필드를 정의합니다.
    """
    name: str = Field(min_length=1, max_length=200, description="서버 이름")
    hostname: str = Field(min_length=1, max_length=255, description="호스트명")
    ip_address: str = Field(
        pattern=r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$",
        description="IP 주소 (IPv4 또는 IPv6)"
    )
    environment: str = Field(
        min_length=1,
        max_length=50,
        pattern=r"^(dev|development|staging|production|test)$",
        description="환경 (dev, staging, production 등)"
    )


class ServerCreate(ServerBase):
    """
    Server 생성 스키마
    서버 등록 시 필요한 필드를 정의합니다.
    """
    type: ServerType = Field(default=ServerType.VIRTUAL, description="서버 타입")
    status: ServerStatus = Field(default=ServerStatus.ACTIVE, description="서버 상태")
    cpu_cores: Optional[int] = Field(default=None, ge=1, description="CPU 코어 수")
    memory_gb: Optional[int] = Field(default=None, ge=1, description="메모리 (GB)")
    disk_gb: Optional[int] = Field(default=None, ge=1, description="디스크 용량 (GB)")
    os_name: Optional[str] = Field(default=None, max_length=100, description="운영체제 이름")
    os_version: Optional[str] = Field(default=None, max_length=50, description="운영체제 버전")
    provider: Optional[str] = Field(default=None, max_length=50, description="클라우드 제공자")
    region: Optional[str] = Field(default=None, max_length=50, description="리전")
    instance_id: Optional[str] = Field(default=None, max_length=100, description="인스턴스 ID")
    ssh_port: int = Field(default=22, ge=1, le=65535, description="SSH 포트")
    ssh_user: Optional[str] = Field(default=None, max_length=50, description="SSH 사용자명")
    monitoring_enabled: bool = Field(default=False, description="모니터링 활성화 여부")
    monitoring_url: Optional[str] = Field(default=None, max_length=500, description="모니터링 대시보드 URL")
    description: Optional[str] = Field(default=None, description="서버 설명")
    notes: Optional[str] = Field(default=None, description="비고")


class ServerUpdate(BaseModel):
    """
    Server 수정 스키마
    서버 정보 수정 시 필요한 필드를 정의합니다.
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="서버 이름")
    hostname: Optional[str] = Field(default=None, min_length=1, max_length=255, description="호스트명")
    ip_address: Optional[str] = Field(default=None, description="IP 주소")
    type: Optional[ServerType] = Field(default=None, description="서버 타입")
    status: Optional[ServerStatus] = Field(default=None, description="서버 상태")
    environment: Optional[str] = Field(default=None, description="환경")
    cpu_cores: Optional[int] = Field(default=None, ge=1, description="CPU 코어 수")
    memory_gb: Optional[int] = Field(default=None, ge=1, description="메모리 (GB)")
    disk_gb: Optional[int] = Field(default=None, ge=1, description="디스크 용량 (GB)")
    os_name: Optional[str] = Field(default=None, max_length=100, description="운영체제 이름")
    os_version: Optional[str] = Field(default=None, max_length=50, description="운영체제 버전")
    provider: Optional[str] = Field(default=None, max_length=50, description="클라우드 제공자")
    region: Optional[str] = Field(default=None, max_length=50, description="리전")
    instance_id: Optional[str] = Field(default=None, max_length=100, description="인스턴스 ID")
    ssh_port: Optional[int] = Field(default=None, ge=1, le=65535, description="SSH 포트")
    ssh_user: Optional[str] = Field(default=None, max_length=50, description="SSH 사용자명")
    monitoring_enabled: Optional[bool] = Field(default=None, description="모니터링 활성화 여부")
    monitoring_url: Optional[str] = Field(default=None, max_length=500, description="모니터링 URL")
    description: Optional[str] = Field(default=None, description="서버 설명")
    notes: Optional[str] = Field(default=None, description="비고")


class ServerResponse(ServerBase, TimestampSchema):
    """
    Server 응답 스키마
    API 응답으로 반환되는 서버 정보입니다.
    """
    id: int = Field(description="서버 ID")
    type: ServerType = Field(description="서버 타입")
    status: ServerStatus = Field(description="서버 상태")
    cpu_cores: Optional[int] = Field(default=None, description="CPU 코어 수")
    memory_gb: Optional[int] = Field(default=None, description="메모리 (GB)")
    disk_gb: Optional[int] = Field(default=None, description="디스크 용량 (GB)")
    os_name: Optional[str] = Field(default=None, description="운영체제 이름")
    os_version: Optional[str] = Field(default=None, description="운영체제 버전")
    provider: Optional[str] = Field(default=None, description="클라우드 제공자")
    region: Optional[str] = Field(default=None, description="리전")
    instance_id: Optional[str] = Field(default=None, description="인스턴스 ID")
    ssh_port: int = Field(description="SSH 포트")
    ssh_user: Optional[str] = Field(default=None, description="SSH 사용자명")
    monitoring_enabled: bool = Field(description="모니터링 활성화 여부")
    monitoring_url: Optional[str] = Field(default=None, description="모니터링 URL")
    description: Optional[str] = Field(default=None, description="서버 설명")
    notes: Optional[str] = Field(default=None, description="비고")
    service_count: Optional[int] = Field(default=None, description="서비스 개수")

    model_config = ConfigDict(from_attributes=True)


class ServerListResponse(BaseModel):
    """
    Server 목록 조회 응답 스키마
    간소화된 서버 정보 목록입니다.
    """
    id: int = Field(description="서버 ID")
    name: str = Field(description="서버 이름")
    hostname: str = Field(description="호스트명")
    ip_address: str = Field(description="IP 주소")
    type: ServerType = Field(description="서버 타입")
    status: ServerStatus = Field(description="서버 상태")
    environment: str = Field(description="환경")
    service_count: Optional[int] = Field(default=None, description="서비스 개수")

    model_config = ConfigDict(from_attributes=True)
