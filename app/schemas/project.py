"""
Project Pydantic schemas
프로젝트 관련 스키마를 정의합니다.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.project import ProjectStatus
from app.schemas.common import TimestampSchema
from app.schemas.team import TeamListResponse


class ProjectBase(BaseModel):
    """
    Project 기본 스키마
    공통 필드를 정의합니다.
    """
    name: str = Field(min_length=2, max_length=200, description="프로젝트 이름")
    key: str = Field(
        min_length=2,
        max_length=10,
        pattern=r"^[A-Z][A-Z0-9]*$",
        description="프로젝트 키 (대문자와 숫자만, 대문자로 시작)"
    )
    description: Optional[str] = Field(default=None, description="프로젝트 설명")

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        """프로젝트 키는 대문자로 변환합니다."""
        return v.upper()


class ProjectCreate(ProjectBase):
    """
    Project 생성 스키마
    프로젝트 생성 시 필요한 필드를 정의합니다.
    """
    team_id: int = Field(description="팀 ID")
    status: ProjectStatus = Field(default=ProjectStatus.PLANNING, description="프로젝트 상태")
    repository_url: Optional[str] = Field(default=None, max_length=500, description="Git 리포지토리 URL")
    documentation_url: Optional[str] = Field(default=None, max_length=500, description="문서 URL")
    icon_url: Optional[str] = Field(default=None, max_length=500, description="프로젝트 아이콘 URL")
    color: Optional[str] = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="프로젝트 색상 (HEX, 예: #FF5733)"
    )


class ProjectUpdate(BaseModel):
    """
    Project 수정 스키마
    프로젝트 정보 수정 시 필요한 필드를 정의합니다.
    """
    name: Optional[str] = Field(default=None, min_length=2, max_length=200, description="프로젝트 이름")
    description: Optional[str] = Field(default=None, description="프로젝트 설명")
    status: Optional[ProjectStatus] = Field(default=None, description="프로젝트 상태")
    repository_url: Optional[str] = Field(default=None, max_length=500, description="Git 리포지토리 URL")
    documentation_url: Optional[str] = Field(default=None, max_length=500, description="문서 URL")
    icon_url: Optional[str] = Field(default=None, max_length=500, description="프로젝트 아이콘 URL")
    color: Optional[str] = Field(
        default=None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="프로젝트 색상 (HEX, 예: #FF5733)"
    )


class ProjectResponse(ProjectBase, TimestampSchema):
    """
    Project 응답 스키마
    API 응답으로 반환되는 프로젝트 정보입니다.
    """
    id: int = Field(description="프로젝트 ID")
    team_id: int = Field(description="팀 ID")
    status: ProjectStatus = Field(description="프로젝트 상태")
    repository_url: Optional[str] = Field(default=None, description="Git 리포지토리 URL")
    documentation_url: Optional[str] = Field(default=None, description="문서 URL")
    icon_url: Optional[str] = Field(default=None, description="프로젝트 아이콘 URL")
    color: Optional[str] = Field(default=None, description="프로젝트 색상 (HEX)")
    team: Optional[TeamListResponse] = Field(default=None, description="팀 정보")

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """
    Project 목록 조회 응답 스키마
    간소화된 프로젝트 정보 목록입니다.
    """
    id: int = Field(description="프로젝트 ID")
    name: str = Field(description="프로젝트 이름")
    key: str = Field(description="프로젝트 키")
    status: ProjectStatus = Field(description="프로젝트 상태")
    icon_url: Optional[str] = Field(default=None, description="프로젝트 아이콘 URL")
    color: Optional[str] = Field(default=None, description="프로젝트 색상 (HEX)")

    model_config = ConfigDict(from_attributes=True)
