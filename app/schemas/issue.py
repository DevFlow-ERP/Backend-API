"""
Issue Pydantic schemas
이슈 관련 스키마를 정의합니다.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from app.models.issue import IssueType, IssuePriority, IssueStatus
from app.schemas.common import TimestampSchema
from app.schemas.user import UserListResponse
from app.schemas.project import ProjectListResponse
from app.schemas.sprint import SprintListResponse


class IssueBase(BaseModel):
    """
    Issue 기본 스키마
    공통 필드를 정의합니다.
    """
    title: str = Field(min_length=1, max_length=500, description="이슈 제목")
    description: Optional[str] = Field(default=None, description="이슈 설명")
    type: IssueType = Field(default=IssueType.TASK, description="이슈 타입")
    priority: IssuePriority = Field(default=IssuePriority.MEDIUM, description="우선순위")


class IssueCreate(IssueBase):
    """
    Issue 생성 스키마
    이슈 생성 시 필요한 필드를 정의합니다.
    """
    project_id: int = Field(description="프로젝트 ID")
    sprint_id: Optional[int] = Field(default=None, description="스프린트 ID (백로그는 NULL)")
    assignee_id: Optional[int] = Field(default=None, description="담당자 ID")
    status: IssueStatus = Field(default=IssueStatus.TODO, description="이슈 상태")
    estimate_hours: Optional[int] = Field(default=None, ge=0, description="예상 소요 시간 (시간)")


class IssueUpdate(BaseModel):
    """
    Issue 수정 스키마
    이슈 정보 수정 시 필요한 필드를 정의합니다.
    """
    title: Optional[str] = Field(default=None, min_length=1, max_length=500, description="이슈 제목")
    description: Optional[str] = Field(default=None, description="이슈 설명")
    type: Optional[IssueType] = Field(default=None, description="이슈 타입")
    priority: Optional[IssuePriority] = Field(default=None, description="우선순위")
    status: Optional[IssueStatus] = Field(default=None, description="이슈 상태")
    sprint_id: Optional[int] = Field(default=None, description="스프린트 ID")
    assignee_id: Optional[int] = Field(default=None, description="담당자 ID")
    estimate_hours: Optional[int] = Field(default=None, ge=0, description="예상 소요 시간 (시간)")
    actual_hours: Optional[int] = Field(default=None, ge=0, description="실제 소요 시간 (시간)")
    order: Optional[int] = Field(default=None, description="정렬 순서")


class IssueResponse(IssueBase, TimestampSchema):
    """
    Issue 응답 스키마
    API 응답으로 반환되는 이슈 정보입니다.
    """
    id: int = Field(description="이슈 ID")
    key: str = Field(description="이슈 키 (예: PROJ-123)")
    project_id: int = Field(description="프로젝트 ID")
    sprint_id: Optional[int] = Field(default=None, description="스프린트 ID")
    assignee_id: Optional[int] = Field(default=None, description="담당자 ID")
    creator_id: int = Field(description="생성자 ID")
    status: IssueStatus = Field(description="이슈 상태")
    estimate_hours: Optional[int] = Field(default=None, description="예상 소요 시간 (시간)")
    actual_hours: Optional[int] = Field(default=None, description="실제 소요 시간 (시간)")
    order: int = Field(description="정렬 순서")

    # Nested objects
    project: Optional[ProjectListResponse] = Field(default=None, description="프로젝트 정보")
    sprint: Optional[SprintListResponse] = Field(default=None, description="스프린트 정보")
    assignee: Optional[UserListResponse] = Field(default=None, description="담당자 정보")
    creator: Optional[UserListResponse] = Field(default=None, description="생성자 정보")

    model_config = ConfigDict(from_attributes=True)


class IssueListResponse(BaseModel):
    """
    Issue 목록 조회 응답 스키마
    간소화된 이슈 정보 목록입니다.
    """
    id: int = Field(description="이슈 ID")
    key: str = Field(description="이슈 키")
    title: str = Field(description="이슈 제목")
    type: IssueType = Field(description="이슈 타입")
    priority: IssuePriority = Field(description="우선순위")
    status: IssueStatus = Field(description="이슈 상태")
    assignee: Optional[UserListResponse] = Field(default=None, description="담당자 정보")

    model_config = ConfigDict(from_attributes=True)
