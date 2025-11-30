"""
User API endpoints
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy import select

from app.crud import crud_user
from app.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserListResponse, UserCreate
from app.schemas.profile import UserProfileResponse
from app.schemas.common import PaginatedResponse
from app.utils import (
    paginate,
    create_paginated_response,
    QueryBuilder,
    SortOrder,
)

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=PaginatedResponse[UserListResponse])
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get user list
    """
    builder = QueryBuilder(select(User), User)
    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)
    return create_paginated_response(items, meta)

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Create new user
    """
    # Check if user with same email exists
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise ValueError("The user with this email already exists in the system.")
        
    # Check if user with same username exists
    user = crud_user.get_by_username(db, username=user_in.username)
    if user:
        raise ValueError("The user with this username already exists in the system.")

    user = crud_user.create(db, obj_in=user_in)
    return user

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: CurrentUser,
):
    """
    Get current user
    """
    return current_user

@router.get("/me/profile", response_model=UserProfileResponse)
def read_user_profile(
    current_user: CurrentUser,
):
    """
    Get current user profile with teams and projects
    내 프로필 조회 (팀, 프로젝트 포함)
    """
    teams = []
    projects = []
    
    # 사용자가 속한 팀과 해당 팀의 프로젝트 조회
    for membership in current_user.team_memberships:
        team = membership.team
        teams.append(team)
        
        # 팀의 프로젝트 중 진행 중인 것만 필터링? 
        # 요구사항: "진행중인 프로젝트" -> 일단 모든 프로젝트 반환하고 FE에서 필터링하거나, 여기서 필터링
        # 여기서는 모든 프로젝트를 반환하도록 함 (FE에서 상태별로 보여줄 수 있으므로)
        for project in team.projects:
            projects.append(project)
            
    return {
        "user": current_user,
        "teams": teams,
        "projects": projects
    }

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: Annotated[int, Path(description="User ID")],
    user_in: UserUpdate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Update user information
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")
        
    updated_user = crud_user.update(db, db_obj=user, obj_in=user_in)
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: Annotated[int, Path(description="User ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Delete user
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")
        
    crud_user.remove(db, id=user_id)