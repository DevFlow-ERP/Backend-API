"""
Profile Pydantic schemas
사용자 프로필 관련 스키마를 정의합니다.
"""

from typing import List
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.user import UserResponse
from app.schemas.team import TeamListResponse
from app.schemas.project import ProjectListResponse


class UserProfileResponse(BaseModel):
    """
    사용자 프로필 응답 스키마
    사용자 기본 정보, 소속 팀, 진행 중인 프로젝트 정보를 포함합니다.
    """
    user: UserResponse = Field(description="사용자 기본 정보")
    teams: List[TeamListResponse] = Field(description="소속 팀 목록")
    projects: List[ProjectListResponse] = Field(description="진행 중인 프로젝트 목록")

    model_config = ConfigDict(from_attributes=True)
