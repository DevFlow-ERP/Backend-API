"""
Team API endpoints
Team management API
"""
import re

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.crud import crud_team, crud_user
from app.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.team import Team, TeamMember, TeamRole
from app.models.project import Project
from app.models.user import User
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamListResponse,
    TeamDetailResponse,
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberResponse,
    TeamStatsResponse,
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

def create_slug(name: str) -> str:
    """
    팀 이름으로 슬러그 생성
    소문자, 숫자, 하이픈만 허용
    """
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug

@router.post("", response_model=TeamResponse, status_code=201)
def create_team(
    team_in: TeamCreate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Create a new team
    """
    # Check if team with same name exists
    existing_team = crud_team.get_by_name(db, name=team_in.name)
    if existing_team:
        raise BadRequestError(f"Team with name '{team_in.name}' already exists")
    
    if not team_in.slug:
        team_in.slug = create_slug(team_in.name)

    team_data = team_in.model_dump(exclude={"member_ids"})
    # Create team
    team = crud_team.create(db, obj_in=team_data)

    # Add creator as owner
    crud_team.add_member(
        db,
        team_id=team.id,
        user_id=current_user.id,
        role=TeamRole.OWNER
    )
    # 4. [추가] 선택된 초기 멤버들을 MEMBER로 추가
    if team_in.member_ids:
        for user_id in team_in.member_ids:
            # 본인을 중복 추가하지 않도록 체크
            if user_id == current_user.id:
                continue
                
            # 사용자 존재 여부 확인 (선택 사항: 생략 시 FK 에러 발생 가능)
            user = crud_user.get(db, id=user_id)
            if user:
                # 이미 멤버인지 확인 (새 팀이라 없겠지만 방어 코드)
                if not crud_team.is_member(db, team_id=team.id, user_id=user_id):
                    crud_team.add_member(
                        db,
                        team_id=team.id,
                        user_id=user_id,
                        role=TeamRole.MEMBER
                    )

    # Add member count
        team.member_count = db.query(func.count(TeamMember.id)).filter(
        TeamMember.team_id == team.id
        ).scalar() or 0

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
    """
    # [수정됨] joinedload 사용 시 .unique() 필수 호출
    stmt = (
        select(Team)
        .options(
            joinedload(Team.members).joinedload(TeamMember.user)
        )
        .where(Team.id == team_id)
    )
    
    # execute() 후 unique()를 호출해야 1:N 관계 중복 데이터가 병합됩니다.
    team = db.execute(stmt).unique().scalar_one_or_none()

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
    """
    # Check if team exists
    team = crud_team.get(db, id=team_id)
    if not team:
        raise NotFoundError(f"Team {team_id} not found")

    # Build query
    # [수정됨] joinedload를 명확한 select 구문에 적용
    base_query = select(TeamMember).options(joinedload(TeamMember.user)).filter(TeamMember.team_id == team_id)
    
    builder = QueryBuilder(base_query, TeamMember)

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

@router.get("/{team_id}/stats", response_model=TeamStatsResponse)
def get_team_stats(
    team_id: Annotated[int, Path(description="Team ID")],
    db: DBSession,
    current_user: CurrentUser,
):
    """
    팀 관련 통계 조회
    """
    team = crud_team.get(db, id=team_id)
    if not team:
        raise NotFoundError(f"Team {team_id} not found")

    # 멤버 수
    member_count = db.query(func.count(TeamMember.id)).filter(
        TeamMember.team_id == team_id
    ).scalar() or 0

    # 프로젝트 수
    project_count = db.query(func.count(Project.id)).filter(
        Project.team_id == team_id
    ).scalar() or 0

    # [FIX] 활성 스프린트 수 (팀 내 모든 프로젝트의 활성 스프린트 합계)
    from app.models.sprint import Sprint, SprintStatus
    active_sprint_count = db.query(func.count(Sprint.id)).join(Project).filter(
        Project.team_id == team_id,
        Sprint.status == SprintStatus.ACTIVE
    ).scalar() or 0

    # [FIX] 전체 이슈 수 (팀 내 모든 프로젝트의 이슈 합계)
    from app.models.issue import Issue
    total_issues = db.query(func.count(Issue.id)).join(Project).filter(
        Project.team_id == team_id
    ).scalar() or 0
    
    return TeamStatsResponse(
        member_count=member_count,
        project_count=project_count,
        active_sprint_count=active_sprint_count,
        total_issues=total_issues,
    )