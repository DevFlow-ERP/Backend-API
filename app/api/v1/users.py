"""
User API endpoints
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy import select

from app.crud import crud_user
from app.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserListResponse
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

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: CurrentUser,
):
    """
    Get current user
    """
    return current_user

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