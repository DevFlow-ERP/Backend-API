"""
Sprint Pydantic schemas
스프린트 관련 스키마를 정의합니다.
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.sprint import SprintStatus
from app.schemas.common import TimestampSchema
from app.schemas.project import ProjectListResponse


class SprintBase(BaseModel):
    """
    Sprint 기본 스키마
    공통 필드를 정의합니다.
    """
    name: str = Field(min_length=2, max_length=200, description="스프린트 이름")
    goal: Optional[str] = Field(default=None, description="스프린트 목표")


class SprintCreate(SprintBase):
    """
    Sprint 생성 스키마
    스프린트 생성 시 필요한 필드를 정의합니다.
    """
    project_id: int = Field(description="프로젝트 ID")
    start_date: Optional[date] = Field(default=None, description="시작일")
    end_date: Optional[date] = Field(default=None, description="종료일")
    status: SprintStatus = Field(default=SprintStatus.PLANNED, description="스프린트 상태")

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: Optional[date], info) -> Optional[date]:
        """종료일은 시작일보다 이후여야 합니다."""
        if v is not None and info.data.get("start_date") is not None:
            if v < info.data["start_date"]:
                raise ValueError("종료일은 시작일보다 이후여야 합니다")
        return v


class SprintUpdate(BaseModel):
    """
    Sprint 수정 스키마
    스프린트 정보 수정 시 필요한 필드를 정의합니다.
    """
    name: Optional[str] = Field(default=None, min_length=2, max_length=200, description="스프린트 이름")
    goal: Optional[str] = Field(default=None, description="스프린트 목표")
    start_date: Optional[date] = Field(default=None, description="시작일")
    end_date: Optional[date] = Field(default=None, description="종료일")
    status: Optional[SprintStatus] = Field(default=None, description="스프린트 상태")


class SprintResponse(SprintBase, TimestampSchema):
    """
    Sprint 응답 스키마
    API 응답으로 반환되는 스프린트 정보입니다.
    """
    id: int = Field(description="스프린트 ID")
    project_id: int = Field(description="프로젝트 ID")
    start_date: Optional[str] = Field(default=None, description="시작일 (ISO 8601)")
    end_date: Optional[str] = Field(default=None, description="종료일 (ISO 8601)")
    status: SprintStatus = Field(description="스프린트 상태")
    project: Optional[ProjectListResponse] = Field(default=None, description="프로젝트 정보")
    issue_count: Optional[int] = Field(default=None, description="이슈 개수")

    model_config = ConfigDict(from_attributes=True)


class SprintListResponse(BaseModel):
    """
    Sprint 목록 조회 응답 스키마
    간소화된 스프린트 정보 목록입니다.
    """
    id: int = Field(description="스프린트 ID")
    name: str = Field(description="스프린트 이름")
    status: SprintStatus = Field(description="스프린트 상태")
    start_date: Optional[str] = Field(default=None, description="시작일 (ISO 8601)")
    end_date: Optional[str] = Field(default=None, description="종료일 (ISO 8601)")
    issue_count: Optional[int] = Field(default=None, description="이슈 개수")

    model_config = ConfigDict(from_attributes=True)
