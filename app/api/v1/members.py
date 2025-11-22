"""
Member API endpoints
Team member management API
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

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
    """
    # [FIX] joinedload를 사용하여 user 관계를 미리 로드 (N+1 문제 및 로딩 오류 방지)
    base_query = select(TeamMember).options(joinedload(TeamMember.user))
    builder = QueryBuilder(base_query, TeamMember)

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
    # [FIX] joinedload 사용
    base_query = select(TeamMember).options(joinedload(TeamMember.user))
    builder = QueryBuilder(base_query, TeamMember).filter(
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
    # [FIX] 명시적 쿼리로 변경하여 joinedload 적용
    member = db.scalar(
        select(TeamMember)
        .options(joinedload(TeamMember.user))
        .where(TeamMember.id == member_id)
    )
    
    if not member:
        raise NotFoundError(f"Member {member_id} not found")

    return member