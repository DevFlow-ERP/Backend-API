"""
Team Pydantic schemas
팀 및 팀 멤버 관련 스키마를 정의합니다.
"""

from typing import Optional,List
from pydantic import BaseModel, Field, ConfigDict

from app.models.team import TeamRole
from app.schemas.common import TimestampSchema
from app.schemas.user import UserListResponse


class TeamBase(BaseModel):
    """
    Team 기본 스키마
    공통 필드를 정의합니다.
    """
    name: str = Field(min_length=2, max_length=100, description="팀 이름")
    description: Optional[str] = Field(default=None, max_length=500, description="팀 설명")
    slug: Optional[str] = Field(default=None, description="팀 슬러그 (URL용, 미입력 시 자동 생성)")


class TeamCreate(TeamBase):
    """
    Team 생성 스키마
    팀 생성 시 필요한 필드를 정의합니다.
    """
    avatar_url: Optional[str] = Field(default=None, max_length=500, description="팀 로고 이미지 URL")
    member_ids: List[int] = Field(default=[], description="초기 추가할 팀원 ID 목록")

class TeamUpdate(BaseModel):
    """
    Team 수정 스키마
    팀 정보 수정 시 필요한 필드를 정의합니다.
    """
    name: Optional[str] = Field(default=None, min_length=2, max_length=100, description="팀 이름")
    description: Optional[str] = Field(default=None, max_length=500, description="팀 설명")
    avatar_url: Optional[str] = Field(default=None, max_length=500, description="팀 로고 이미지 URL")


class TeamResponse(TeamBase, TimestampSchema):
    """
    Team 응답 스키마
    API 응답으로 반환되는 팀 정보입니다.
    """
    id: int = Field(description="팀 ID")
    slug: str = Field(description="팀 슬러그")
    avatar_url: Optional[str] = Field(default=None, description="팀 로고 이미지 URL")
    member_count: Optional[int] = Field(default=None, description="팀 멤버 수")

    model_config = ConfigDict(from_attributes=True)


class TeamListResponse(BaseModel):
    """
    Team 목록 조회 응답 스키마
    간소화된 팀 정보 목록입니다.
    """
    id: int = Field(description="팀 ID")
    name: str = Field(description="팀 이름")
    slug: str = Field(description="팀 슬러그")
    avatar_url: Optional[str] = Field(default=None, description="팀 로고 이미지 URL")
    member_count: Optional[int] = Field(default=None, description="팀 멤버 수")

    model_config = ConfigDict(from_attributes=True)


# TeamMember Schemas

class TeamMemberBase(BaseModel):
    """
    TeamMember 기본 스키마
    """
    role: TeamRole = Field(default=TeamRole.MEMBER, description="팀 내 역할")


class TeamMemberCreate(TeamMemberBase):
    """
    TeamMember 생성 스키마
    팀 멤버 추가 시 필요한 필드를 정의합니다.
    """
    user_id: int = Field(description="사용자 ID")


class TeamMemberUpdate(BaseModel):
    """
    TeamMember 수정 스키마
    팀 멤버 역할 변경 시 사용합니다.
    """
    role: TeamRole = Field(description="팀 내 역할")


class TeamMemberResponse(TeamMemberBase, TimestampSchema):
    """
    TeamMember 응답 스키마
    API 응답으로 반환되는 팀 멤버 정보입니다.
    """
    id: int = Field(description="팀 멤버 ID")
    team_id: int = Field(description="팀 ID")
    user_id: int = Field(description="사용자 ID")
    user: Optional[UserListResponse] = Field(default=None, description="사용자 정보")

    model_config = ConfigDict(from_attributes=True)


class TeamDetailResponse(TeamResponse):
    """
    Team 상세 조회 응답 스키마
    팀 정보와 함께 멤버 목록을 포함합니다.
    """
    members: list[TeamMemberResponse] = Field(default_factory=list, description="팀 멤버 목록")

    model_config = ConfigDict(from_attributes=True)

# Backend-API/app/schemas/team.py 파일 하단에 추가

class TeamStatsResponse(BaseModel):
    """
    팀 통계 조회 응답 스키마
    """
    member_count: int = Field(description="총 팀 멤버 수")
    project_count: int = Field(description="팀에 속한 총 프로젝트 수")
    active_sprint_count: int = Field(description="현재 활성화된 스프린트 수")
    total_issues: int = Field(description="팀에 할당된 총 이슈 수 (전체)")

    model_config = ConfigDict(from_attributes=True)