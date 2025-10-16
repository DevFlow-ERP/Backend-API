"""
Deployment Pydantic schemas
배포 관련 스키마를 정의합니다.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_serializer

from app.models.deployment import DeploymentType, DeploymentStatus
from app.schemas.common import TimestampSchema
from app.schemas.user import UserListResponse
from app.schemas.service import ServiceListResponse


class DeploymentBase(BaseModel):
    """
    Deployment 기본 스키마
    공통 필드를 정의합니다.
    """
    version: str = Field(min_length=1, max_length=50, description="배포 버전")
    environment: str = Field(
        min_length=1,
        max_length=50,
        pattern=r"^(dev|development|staging|production|test)$",
        description="배포 환경 (dev, staging, production 등)"
    )


class DeploymentCreate(DeploymentBase):
    """
    Deployment 생성 스키마
    배포 기록 생성 시 필요한 필드를 정의합니다.
    """
    service_id: int = Field(description="서비스 ID")
    commit_hash: Optional[str] = Field(default=None, max_length=40, pattern=r"^[a-f0-9]{40}$", description="Git 커밋 해시 (40자)")
    branch: Optional[str] = Field(default=None, max_length=100, description="Git 브랜치")
    tag: Optional[str] = Field(default=None, max_length=100, description="Git 태그")
    type: DeploymentType = Field(default=DeploymentType.MANUAL, description="배포 타입")
    status: DeploymentStatus = Field(default=DeploymentStatus.PENDING, description="배포 상태")
    notes: Optional[str] = Field(default=None, description="배포 메모")


class DeploymentUpdate(BaseModel):
    """
    Deployment 수정 스키마
    배포 상태 및 정보 업데이트 시 사용합니다.
    """
    status: Optional[DeploymentStatus] = Field(default=None, description="배포 상태")
    started_at: Optional[datetime] = Field(default=None, description="배포 시작 시간")
    completed_at: Optional[datetime] = Field(default=None, description="배포 완료 시간")
    notes: Optional[str] = Field(default=None, description="배포 메모")
    error_message: Optional[str] = Field(default=None, description="에러 메시지")
    log_url: Optional[str] = Field(default=None, max_length=500, description="배포 로그 URL")


class DeploymentResponse(DeploymentBase, TimestampSchema):
    """
    Deployment 응답 스키마
    API 응답으로 반환되는 배포 정보입니다.
    """
    id: int = Field(description="배포 ID")
    service_id: int = Field(description="서비스 ID")
    deployed_by: int = Field(description="배포자 ID")
    commit_hash: Optional[str] = Field(default=None, description="Git 커밋 해시")
    branch: Optional[str] = Field(default=None, description="Git 브랜치")
    tag: Optional[str] = Field(default=None, description="Git 태그")
    type: DeploymentType = Field(description="배포 타입")
    status: DeploymentStatus = Field(description="배포 상태")
    started_at: Optional[datetime] = Field(default=None, description="배포 시작 시간 (ISO 8601)")
    completed_at: Optional[datetime] = Field(default=None, description="배포 완료 시간 (ISO 8601)")
    rollback_from_id: Optional[int] = Field(default=None, description="롤백 대상 배포 ID")
    notes: Optional[str] = Field(default=None, description="배포 메모")
    error_message: Optional[str] = Field(default=None, description="에러 메시지")
    log_url: Optional[str] = Field(default=None, description="배포 로그 URL")

    # Nested objects
    service: Optional[ServiceListResponse] = Field(default=None, description="서비스 정보")
    deployed_by_user: Optional[UserListResponse] = Field(default=None, description="배포자 정보")

    @field_serializer('started_at', 'completed_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Convert datetime to ISO 8601 string"""
        return value.isoformat() if value else None

    model_config = ConfigDict(from_attributes=True)


class DeploymentListResponse(BaseModel):
    """
    Deployment 목록 조회 응답 스키마
    간소화된 배포 정보 목록입니다.
    """
    id: int = Field(description="배포 ID")
    service_id: int = Field(description="서비스 ID")
    version: str = Field(description="배포 버전")
    environment: str = Field(description="배포 환경")
    type: DeploymentType = Field(description="배포 타입")
    status: DeploymentStatus = Field(description="배포 상태")
    deployed_at: datetime = Field(alias="created_at", description="배포일시 (created_at)")
    deployed_by_user: Optional[UserListResponse] = Field(default=None, description="배포자 정보")

    @field_serializer('deployed_at')
    def serialize_deployed_at(self, value: datetime) -> str:
        """Convert datetime to ISO 8601 string"""
        return value.isoformat()

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DeploymentRollbackRequest(BaseModel):
    """
    Deployment 롤백 요청 스키마
    특정 배포로 롤백할 때 사용합니다.
    """
    target_deployment_id: int = Field(description="롤백할 배포 ID")
    notes: Optional[str] = Field(default=None, description="롤백 사유")
