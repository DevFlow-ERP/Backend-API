"""
Team API endpoints
Team management API
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.crud import crud_team, crud_user
from app.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.team import Team, TeamMember, TeamRole
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamListResponse,
    TeamDetailResponse,
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberResponse,
)
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.utils import (
    paginate,
    create_paginated_response,
    QueryBuilder,
    SortOrder,
)

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("", response_model=PaginatedResponse[TeamListResponse])
def list_teams(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    search: str | None = Query(default=None, description="Search in name"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    order: SortOrder = Query(default=SortOrder.DESC, description="Sort order"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get team list

    - **page**: Page number (starting from 1)
    - **page_size**: Page size (max 100)
    - **search**: Search in team name
    - **sort_by**: Sort field
    - **order**: Sort order (asc or desc)
    """
    builder = QueryBuilder(select(Team), Team)

    # Search
    if search:
        builder.search(["name"], search)

    # Sort
    builder.sort(sort_by, order)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    # Add member count to each team
    for team in items:
        team.member_count = db.query(func.count(TeamMember.id)).filter(
            TeamMember.team_id == team.id
        ).scalar() or 0

    return create_paginated_response(items, meta)


@router.post("", response_model=TeamResponse, status_code=201)
def create_team(
    team_in: TeamCreate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Create a new team

    Creates a new team and automatically adds the creator as owner.

    **Required fields**:
    - **name**: Team name
    - **slug**: Team slug (URL-friendly, lowercase with hyphens only)

    **Optional fields**:
    - **description**: Team description
    - **avatar_url**: Team logo image URL
    """
    # Check if team with same name exists
    existing_team = crud_team.get_by_name(db, name=team_in.name)
    if existing_team:
        raise BadRequestError(f"Team with name '{team_in.name}' already exists")

    # Create team
    team = crud_team.create(db, obj_in=team_in)

    # Add creator as owner
    crud_team.add_member(
        db,
        team_id=team.id,
        user_id=current_user.id,
        role=TeamRole.OWNER
    )

    # Add member count
    team.member_count = 1

    return team


@router.get("/my", response_model=PaginatedResponse[TeamListResponse])
def list_my_teams(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get teams I belong to

    Returns a list of teams that the current user is a member of.
    """
    # Get teams for current user
    teams = crud_team.get_user_teams(
        db,
        user_id=current_user.id,
        skip=(page - 1) * page_size,
        limit=page_size
    )

    # Count total teams
    total = db.query(func.count(Team.id)).join(TeamMember).filter(
        TeamMember.user_id == current_user.id
    ).scalar() or 0

    # Add member count to each team
    for team in teams:
        team.member_count = db.query(func.count(TeamMember.id)).filter(
            TeamMember.team_id == team.id
        ).scalar() or 0

    # Create pagination meta
    from math import ceil
    from app.schemas.common import PaginationMeta

    total_pages = ceil(total / page_size) if page_size > 0 else 0
    meta = PaginationMeta(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )

    return create_paginated_response(teams, meta)


@router.get("/{team_id}", response_model=TeamDetailResponse)
def get_team(
    team_id: Annotated[int, Path(description="Team ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get team details

    Returns detailed information about a specific team including member list.
    """
    team = crud_team.get(db, id=team_id)
    if not team:
        raise NotFoundError(f"Team {team_id} not found")

    # Add member count
    team.member_count = len(team.members)

    return team


@router.put("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: Annotated[int, Path(description="Team ID")],
    team_in: TeamUpdate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Update team information

    Updates team information. Only provided fields will be updated.

    **Updatable fields**:
    - **name**: Team name
    - **description**: Team description
    - **avatar_url**: Team logo image URL
    """
    # Check if team exists
    team = crud_team.get(db, id=team_id)
    if not team:
        raise NotFoundError(f"Team {team_id} not found")

    # Check if user is owner or admin
    if not crud_team.has_role(db, team_id=team_id, user_id=current_user.id, role=TeamRole.OWNER):
        if not crud_team.has_role(db, team_id=team_id, user_id=current_user.id, role=TeamRole.ADMIN):
            raise BadRequestError("Only team owners or admins can update team")

    # Update team
    updated_team = crud_team.update(db, db_obj=team, obj_in=team_in)

    # Add member count
    updated_team.member_count = db.query(func.count(TeamMember.id)).filter(
        TeamMember.team_id == team_id
    ).scalar() or 0

    return updated_team


@router.delete("/{team_id}", response_model=SuccessResponse)
def delete_team(
    team_id: Annotated[int, Path(description="Team ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Delete a team

    Deletes a team. Only team owners can delete teams.
    """
    # Check if team exists
    team = crud_team.get(db, id=team_id)
    if not team:
        raise NotFoundError(f"Team {team_id} not found")

    # Check if user is owner
    if not crud_team.has_role(db, team_id=team_id, user_id=current_user.id, role=TeamRole.OWNER):
        raise BadRequestError("Only team owners can delete team")

    # Delete team
    crud_team.delete(db, id=team_id)

    return SuccessResponse(
        success=True,
        message=f"Team '{team.name}' deleted successfully"
    )


# Team Member Management Endpoints

@router.get("/{team_id}/members", response_model=PaginatedResponse[TeamMemberResponse])
def list_team_members(
    team_id: Annotated[int, Path(description="Team ID")],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: TeamRole | None = Query(default=None, description="Filter by role"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get team member list

    Returns a list of members in the specified team.
    """
    # Check if team exists
    team = crud_team.get(db, id=team_id)
    if not team:
        raise NotFoundError(f"Team {team_id} not found")

    # Build query
    builder = QueryBuilder(select(TeamMember), TeamMember).filter(team_id=team_id)

    if role:
        builder.filter(role=role)

    builder.sort("created_at", SortOrder.ASC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=201)
def add_team_member(
    team_id: Annotated[int, Path(description="Team ID")],
    member_in: TeamMemberCreate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Add a member to the team

    Adds a new member to the team with the specified role.

    **Required fields**:
    - **user_id**: User ID to add

    **Optional fields**:
    - **role**: Team role (default: MEMBER)

    **Roles**:
    - **OWNER**: Team owner (full control)
    - **ADMIN**: Team admin (can manage members)
    - **MEMBER**: Regular member
    - **VIEWER**: Read-only access
    """
    # Check if team exists
    team = crud_team.get(db, id=team_id)
    if not team:
        raise NotFoundError(f"Team {team_id} not found")

    # Check if user is owner or admin
    if not crud_team.has_role(db, team_id=team_id, user_id=current_user.id, role=TeamRole.OWNER):
        if not crud_team.has_role(db, team_id=team_id, user_id=current_user.id, role=TeamRole.ADMIN):
            raise BadRequestError("Only team owners or admins can add members")

    # Check if user exists
    user = crud_user.get(db, id=member_in.user_id)
    if not user:
        raise NotFoundError(f"User {member_in.user_id} not found")

    # Check if user is already a member
    if crud_team.is_member(db, team_id=team_id, user_id=member_in.user_id):
        raise BadRequestError(f"User {member_in.user_id} is already a member of this team")

    # Add member
    team_member = crud_team.add_member(
        db,
        team_id=team_id,
        user_id=member_in.user_id,
        role=member_in.role
    )

    return team_member


@router.delete("/{team_id}/members/{user_id}", response_model=SuccessResponse)
def remove_team_member(
    team_id: Annotated[int, Path(description="Team ID")],
    user_id: Annotated[int, Path(description="User ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Remove a member from the team

    Removes a member from the team. Owners and admins can remove members.
    """
    # Check if team exists
    team = crud_team.get(db, id=team_id)
    if not team:
        raise NotFoundError(f"Team {team_id} not found")

    # Check if user is owner or admin
    if not crud_team.has_role(db, team_id=team_id, user_id=current_user.id, role=TeamRole.OWNER):
        if not crud_team.has_role(db, team_id=team_id, user_id=current_user.id, role=TeamRole.ADMIN):
            raise BadRequestError("Only team owners or admins can remove members")

    # Check if member exists
    if not crud_team.is_member(db, team_id=team_id, user_id=user_id):
        raise NotFoundError(f"User {user_id} is not a member of this team")

    # Cannot remove owner
    if crud_team.has_role(db, team_id=team_id, user_id=user_id, role=TeamRole.OWNER):
        raise BadRequestError("Cannot remove team owner")

    # Remove member
    crud_team.remove_member(db, team_id=team_id, user_id=user_id)

    return SuccessResponse(
        success=True,
        message=f"User {user_id} removed from team successfully"
    )


@router.patch("/{team_id}/members/{user_id}/role", response_model=TeamMemberResponse)
def update_member_role(
    team_id: Annotated[int, Path(description="Team ID")],
    user_id: Annotated[int, Path(description="User ID")],
    role: Annotated[TeamRole, Body(embed=True, description="New role")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Update team member role

    Updates the role of a team member. Only owners can change roles.

    **Roles**:
    - **OWNER**: Team owner (full control)
    - **ADMIN**: Team admin (can manage members)
    - **MEMBER**: Regular member
    - **VIEWER**: Read-only access
    """
    # Check if team exists
    team = crud_team.get(db, id=team_id)
    if not team:
        raise NotFoundError(f"Team {team_id} not found")

    # Check if user is owner
    if not crud_team.has_role(db, team_id=team_id, user_id=current_user.id, role=TeamRole.OWNER):
        raise BadRequestError("Only team owners can change member roles")

    # Check if member exists
    if not crud_team.is_member(db, team_id=team_id, user_id=user_id):
        raise NotFoundError(f"User {user_id} is not a member of this team")

    # Update role
    team_member = crud_team.update_member_role(
        db,
        team_id=team_id,
        user_id=user_id,
        role=role
    )

    return team_member
