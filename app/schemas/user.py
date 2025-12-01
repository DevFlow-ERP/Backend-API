"""
User Pydantic schemas
사용자 관련 스키마를 정의합니다.
"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from app.schemas.common import TimestampSchema


class UserBase(BaseModel):
    """
    User 기본 스키마
    공통 필드를 정의합니다.
    """
    email: EmailStr = Field(description="이메일 주소")
    username: str = Field(min_length=3, max_length=100, description="사용자명")
    full_name: Optional[str] = Field(default=None, max_length=200, description="전체 이름")
    phone: Optional[str] = Field(default=None, max_length=20, pattern=r"^\+?[0-9\-\s()]+$", description="전화번호")


class UserCreate(UserBase):
    """
    User 생성 스키마
    사용자 생성 시 필요한 필드를 정의합니다.
    """
    full_name: str = Field(max_length=200, description="전체 이름")
    phone: str = Field(max_length=20, pattern=r"^\+?[0-9\-\s()]+$", description="전화번호")
    is_admin: bool = Field(default=False, description="관리자 여부")
    authentik_id: Optional[str] = Field(default=None, max_length=255, description="Authentik SSO ID")
    avatar_url: Optional[str] = Field(default=None, max_length=500, description="프로필 이미지 URL")


class UserUpdate(BaseModel):
    """
    User 수정 스키마
    사용자 정보 수정 시 필요한 필드를 정의합니다.
    모든 필드는 Optional입니다.
    """
    email: Optional[EmailStr] = Field(default=None, description="이메일 주소")
    username: Optional[str] = Field(default=None, min_length=3, max_length=100, description="사용자명")
    full_name: Optional[str] = Field(default=None, max_length=200, description="전체 이름")
    phone: Optional[str] = Field(default=None, max_length=20, pattern=r"^\+?[0-9\-\s()]+$", description="전화번호")
    avatar_url: Optional[str] = Field(default=None, max_length=500, description="프로필 이미지 URL")
    is_active: Optional[bool] = Field(default=None, description="활성 상태")


class UserResponse(UserBase, TimestampSchema):
    """
    User 응답 스키마
    API 응답으로 반환되는 사용자 정보입니다.
    """
    id: int = Field(description="사용자 ID")
    authentik_id: str = Field(description="Authentik SSO ID")
    avatar_url: Optional[str] = Field(default=None, description="프로필 이미지 URL")
    is_active: bool = Field(description="활성 상태")
    is_admin: bool = Field(description="관리자 여부")

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """
    User 목록 조회 응답 스키마
    간소화된 사용자 정보 목록입니다.
    """
    id: int = Field(description="사용자 ID")
    email: EmailStr = Field(description="이메일 주소")
    username: str = Field(description="사용자명")
    full_name: Optional[str] = Field(default=None, description="전체 이름")
    avatar_url: Optional[str] = Field(default=None, description="프로필 이미지 URL")
    is_active: bool = Field(description="활성 상태")

    model_config = ConfigDict(from_attributes=True)


class CurrentUserResponse(UserResponse):
    """
    현재 로그인한 사용자 정보 응답 스키마
    추가 정보를 포함할 수 있습니다.
    """
    pass
