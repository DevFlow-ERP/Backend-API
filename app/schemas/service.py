"""
Service Pydantic schemas
서비스 관련 스키마를 정의합니다.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.service import ServiceType, ServiceStatus
from app.schemas.common import TimestampSchema
from app.schemas.server import ServerListResponse


class ServiceBase(BaseModel):
    """
    Service 기본 스키마
    공통 필드를 정의합니다.
    """
    name: str = Field(min_length=1, max_length=200, description="서비스 이름")
    type: ServiceType = Field(default=ServiceType.WEB, description="서비스 타입")


class ServiceCreate(ServiceBase):
    """
    Service 생성 스키마
    서비스 등록 시 필요한 필드를 정의합니다.
    """
    server_id: int = Field(description="서버 ID")
    status: ServiceStatus = Field(default=ServiceStatus.STOPPED, description="서비스 상태")
    version: Optional[str] = Field(default=None, max_length=50, description="서비스 버전")
    port: Optional[int] = Field(default=None, ge=1, le=65535, description="서비스 포트")
    url: Optional[str] = Field(default=None, max_length=500, description="서비스 URL")
    process_name: Optional[str] = Field(default=None, max_length=200, description="프로세스 이름")
    pid: Optional[int] = Field(default=None, ge=1, description="프로세스 ID")
    container_id: Optional[str] = Field(default=None, max_length=100, description="컨테이너 ID")
    image_name: Optional[str] = Field(default=None, max_length=200, description="컨테이너 이미지 이름")
    cpu_limit: Optional[int] = Field(default=None, ge=0, le=100, description="CPU 제한 (%)")
    memory_limit_mb: Optional[int] = Field(default=None, ge=0, description="메모리 제한 (MB)")
    health_check_url: Optional[str] = Field(default=None, max_length=500, description="헬스체크 URL")
    health_check_enabled: bool = Field(default=False, description="헬스체크 활성화 여부")
    environment_variables: Optional[dict] = Field(default=None, description="환경 변수 (JSON)")
    config_path: Optional[str] = Field(default=None, max_length=500, description="설정 파일 경로")
    log_path: Optional[str] = Field(default=None, max_length=500, description="로그 파일 경로")
    auto_start: bool = Field(default=False, description="자동 시작 여부")
    description: Optional[str] = Field(default=None, description="서비스 설명")
    notes: Optional[str] = Field(default=None, description="비고")


class ServiceUpdate(BaseModel):
    """
    Service 수정 스키마
    서비스 정보 수정 시 필요한 필드를 정의합니다.
    """
    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="서비스 이름")
    type: Optional[ServiceType] = Field(default=None, description="서비스 타입")
    status: Optional[ServiceStatus] = Field(default=None, description="서비스 상태")
    version: Optional[str] = Field(default=None, max_length=50, description="서비스 버전")
    port: Optional[int] = Field(default=None, ge=1, le=65535, description="서비스 포트")
    url: Optional[str] = Field(default=None, max_length=500, description="서비스 URL")
    process_name: Optional[str] = Field(default=None, max_length=200, description="프로세스 이름")
    pid: Optional[int] = Field(default=None, ge=1, description="프로세스 ID")
    container_id: Optional[str] = Field(default=None, max_length=100, description="컨테이너 ID")
    image_name: Optional[str] = Field(default=None, max_length=200, description="이미지 이름")
    cpu_limit: Optional[int] = Field(default=None, ge=0, le=100, description="CPU 제한 (%)")
    memory_limit_mb: Optional[int] = Field(default=None, ge=0, description="메모리 제한 (MB)")
    health_check_url: Optional[str] = Field(default=None, max_length=500, description="헬스체크 URL")
    health_check_enabled: Optional[bool] = Field(default=None, description="헬스체크 활성화 여부")
    environment_variables: Optional[dict] = Field(default=None, description="환경 변수 (JSON)")
    config_path: Optional[str] = Field(default=None, max_length=500, description="설정 파일 경로")
    log_path: Optional[str] = Field(default=None, max_length=500, description="로그 파일 경로")
    auto_start: Optional[bool] = Field(default=None, description="자동 시작 여부")
    description: Optional[str] = Field(default=None, description="서비스 설명")
    notes: Optional[str] = Field(default=None, description="비고")


class ServiceResponse(ServiceBase, TimestampSchema):
    """
    Service 응답 스키마
    API 응답으로 반환되는 서비스 정보입니다.
    """
    id: int = Field(description="서비스 ID")
    server_id: int = Field(description="서버 ID")
    status: ServiceStatus = Field(description="서비스 상태")
    version: Optional[str] = Field(default=None, description="서비스 버전")
    port: Optional[int] = Field(default=None, description="서비스 포트")
    url: Optional[str] = Field(default=None, description="서비스 URL")
    process_name: Optional[str] = Field(default=None, description="프로세스 이름")
    pid: Optional[int] = Field(default=None, description="프로세스 ID")
    container_id: Optional[str] = Field(default=None, description="컨테이너 ID")
    image_name: Optional[str] = Field(default=None, description="이미지 이름")
    cpu_limit: Optional[int] = Field(default=None, description="CPU 제한 (%)")
    memory_limit_mb: Optional[int] = Field(default=None, description="메모리 제한 (MB)")
    health_check_url: Optional[str] = Field(default=None, description="헬스체크 URL")
    health_check_enabled: bool = Field(description="헬스체크 활성화 여부")
    environment_variables: Optional[dict] = Field(default=None, description="환경 변수")
    config_path: Optional[str] = Field(default=None, description="설정 파일 경로")
    log_path: Optional[str] = Field(default=None, description="로그 파일 경로")
    auto_start: bool = Field(description="자동 시작 여부")
    description: Optional[str] = Field(default=None, description="서비스 설명")
    notes: Optional[str] = Field(default=None, description="비고")
    server: Optional[ServerListResponse] = Field(default=None, description="서버 정보")
    deployment_count: Optional[int] = Field(default=None, description="배포 이력 개수")

    model_config = ConfigDict(from_attributes=True)


class ServiceListResponse(BaseModel):
    """
    Service 목록 조회 응답 스키마
    간소화된 서비스 정보 목록입니다.
    """
    id: int = Field(description="서비스 ID")
    server_id: int = Field(description="서버 ID")
    name: str = Field(description="서비스 이름")
    type: ServiceType = Field(description="서비스 타입")
    status: ServiceStatus = Field(description="서비스 상태")
    version: Optional[str] = Field(default=None, description="서비스 버전")
    url: Optional[str] = Field(default=None, description="서비스 URL")

    model_config = ConfigDict(from_attributes=True)
