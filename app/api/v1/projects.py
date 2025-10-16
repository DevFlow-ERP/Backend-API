"""
Project API endpoints
프로젝트 관리 API
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import crud_project
from app.dependencies import CurrentUser, DBSession
from app.core.exceptions import ProjectNotFoundError, BadRequestError
from app.models.project import Project, ProjectStatus
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.utils import (
    paginate,
    create_paginated_response,
    QueryBuilder,
    SortOrder,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=PaginatedResponse[ProjectListResponse])
def list_projects(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    page_size: int = Query(default=20, ge=1, le=100, description="페이지 크기"),
    team_id: int | None = Query(default=None, description="팀 ID 필터"),
    status: ProjectStatus | None = Query(default=None, description="프로젝트 상태 필터"),
    search: str | None = Query(default=None, description="검색어 (이름, 설명)"),
    sort_by: str = Query(default="created_at", description="정렬 필드"),
    order: SortOrder = Query(default=SortOrder.DESC, description="정렬 순서"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    프로젝트 목록 조회

    - **page**: 페이지 번호 (1부터 시작)
    - **page_size**: 페이지 크기 (최대 100)
    - **team_id**: 특정 팀의 프로젝트만 조회
    - **status**: 프로젝트 상태로 필터링
    - **search**: 프로젝트 이름 또는 설명에서 검색
    - **sort_by**: 정렬 기준 필드
    - **order**: 정렬 순서 (asc 또는 desc)
    """
    # 쿼리 빌더로 복잡한 조건 구성
    builder = QueryBuilder(select(Project), Project)

    # 팀 필터
    if team_id:
        builder.filter(team_id=team_id)

    # 상태 필터
    if status:
        builder.filter(status=status)

    # 검색
    if search:
        builder.search(["name", "description"], search)

    # 정렬
    builder.sort(sort_by, order)

    # 쿼리 빌드
    query = builder.build()

    # 페이지네이션
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    project_in: ProjectCreate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    프로젝트 생성

    새로운 프로젝트를 생성합니다.
    프로젝트 키는 자동으로 대문자로 변환됩니다.

    **필수 필드**:
    - **team_id**: 팀 ID
    - **key**: 프로젝트 키 (예: PROJ, DEV)
    - **name**: 프로젝트 이름
    """
    # 프로젝트 키 중복 확인
    existing_project = crud_project.get_by_key(db, key=project_in.key)
    if existing_project:
        raise BadRequestError(f"Project with key '{project_in.key}' already exists")

    # 프로젝트 생성
    project = crud_project.create(db, obj_in=project_in)

    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: Annotated[int, Path(description="프로젝트 ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    프로젝트 상세 조회

    특정 프로젝트의 상세 정보를 조회합니다.
    """
    project = crud_project.get(db, id=project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: Annotated[int, Path(description="프로젝트 ID")],
    project_in: ProjectUpdate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    프로젝트 수정

    프로젝트 정보를 수정합니다.
    제공된 필드만 업데이트됩니다.

    **수정 가능 필드**:
    - **name**: 프로젝트 이름
    - **description**: 프로젝트 설명
    - **status**: 프로젝트 상태
    """
    # 프로젝트 존재 확인
    project = crud_project.get(db, id=project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    # 프로젝트 키 중복 확인 (키가 변경되는 경우)
    if project_in.key and project_in.key != project.key:
        existing_project = crud_project.get_by_key(db, key=project_in.key)
        if existing_project:
            raise BadRequestError(f"Project with key '{project_in.key}' already exists")

    # 프로젝트 업데이트
    updated_project = crud_project.update(db, db_obj=project, obj_in=project_in)

    return updated_project


@router.delete("/{project_id}", response_model=SuccessResponse)
def delete_project(
    project_id: Annotated[int, Path(description="프로젝트 ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    프로젝트 삭제

    프로젝트를 삭제합니다.
    연관된 스프린트, 이슈 등도 함께 삭제될 수 있으므로 주의하세요.
    """
    # 프로젝트 존재 확인
    project = crud_project.get(db, id=project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    # 프로젝트 삭제
    crud_project.delete(db, id=project_id)

    return SuccessResponse(
        success=True,
        message=f"Project '{project.name}' deleted successfully"
    )


@router.get("/key/{project_key}", response_model=ProjectResponse)
def get_project_by_key(
    project_key: Annotated[str, Path(description="프로젝트 키")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    프로젝트 키로 조회

    프로젝트 키(예: PROJ, DEV)로 프로젝트를 조회합니다.
    """
    project = crud_project.get_by_key(db, key=project_key)
    if not project:
        raise ProjectNotFoundError(f"Project with key '{project_key}' not found")

    return project


@router.patch("/{project_id}/status", response_model=ProjectResponse)
def update_project_status(
    project_id: Annotated[int, Path(description="프로젝트 ID")],
    status: Annotated[ProjectStatus, Query(description="새로운 프로젝트 상태")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    프로젝트 상태 변경

    프로젝트의 상태만 변경합니다.

    **상태 종류**:
    - **PLANNING**: 계획 중
    - **ACTIVE**: 진행 중
    - **ON_HOLD**: 보류
    - **COMPLETED**: 완료
    - **ARCHIVED**: 보관
    """
    # 프로젝트 존재 확인
    project = crud_project.get(db, id=project_id)
    if not project:
        raise ProjectNotFoundError(project_id)

    # 상태 변경
    updated_project = crud_project.update_status(db, project_id=project_id, status=status)

    return updated_project


@router.get("/team/{team_id}", response_model=PaginatedResponse[ProjectListResponse])
def list_team_projects(
    team_id: Annotated[int, Path(description="팀 ID")],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: ProjectStatus | None = Query(default=None),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    팀의 프로젝트 목록 조회

    특정 팀에 속한 프로젝트 목록을 조회합니다.
    """
    builder = QueryBuilder(select(Project), Project).filter(team_id=team_id)

    if status:
        builder.filter(status=status)

    builder.sort("created_at", SortOrder.DESC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)
