"""
Member API endpoints
Team member management API
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import crud_team_member
from app.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError
from app.models.team import TeamMember, TeamRole
from app.schemas.team import TeamMemberResponse
from app.schemas.common import PaginatedResponse
from app.utils import (
    paginate,
    create_paginated_response,
    QueryBuilder,
    SortOrder,
)

router = APIRouter(prefix="/members", tags=["Members"])


@router.get("", response_model=PaginatedResponse[TeamMemberResponse])
def list_members(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    team_id: int | None = Query(default=None, description="Filter by team ID"),
    user_id: int | None = Query(default=None, description="Filter by user ID"),
    role: TeamRole | None = Query(default=None, description="Filter by role"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    order: SortOrder = Query(default=SortOrder.DESC, description="Sort order"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get team member list

    Returns a list of team members with various filters.

    - **page**: Page number (starting from 1)
    - **page_size**: Page size (max 100)
    - **team_id**: Filter by team ID
    - **user_id**: Filter by user ID
    - **role**: Filter by role
    - **sort_by**: Sort field
    - **order**: Sort order (asc or desc)
    """
    builder = QueryBuilder(select(TeamMember), TeamMember)

    # Filters
    if team_id:
        builder.filter(team_id=team_id)
    if user_id:
        builder.filter(user_id=user_id)
    if role:
        builder.filter(role=role)

    # Sort
    builder.sort(sort_by, order)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/my", response_model=PaginatedResponse[TeamMemberResponse])
def list_my_memberships(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get my team memberships

    Returns a list of team memberships for the current user.
    """
    builder = QueryBuilder(select(TeamMember), TeamMember).filter(
        user_id=current_user.id
    )
    builder.sort("created_at", SortOrder.DESC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/{member_id}", response_model=TeamMemberResponse)
def get_member(
    member_id: Annotated[int, Path(description="Member ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get team member details

    Returns detailed information about a specific team member.
    """
    member = crud_team_member.get(db, id=member_id)
    if not member:
        raise NotFoundError(f"Member {member_id} not found")

    return member
