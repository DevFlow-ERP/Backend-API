"""
Sprint API endpoints
스프린트 관리 API
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import crud_sprint
from app.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.sprint import Sprint, SprintStatus
from app.schemas.sprint import (
    SprintCreate,
    SprintUpdate,
    SprintResponse,
    SprintListResponse,
)
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.utils import (
    paginate,
    create_paginated_response,
    QueryBuilder,
    SortOrder,
)

router = APIRouter(prefix="/sprints", tags=["Sprints"])


@router.get("", response_model=PaginatedResponse[SprintListResponse])
def list_sprints(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    page_size: int = Query(default=20, ge=1, le=100, description="페이지 크기"),
    project_id: int | None = Query(default=None, description="프로젝트 ID 필터"),
    status: SprintStatus | None = Query(default=None, description="스프린트 상태 필터"),
    sort_by: str = Query(default="created_at", description="정렬 필드"),
    order: SortOrder = Query(default=SortOrder.DESC, description="정렬 순서"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    스프린트 목록 조회

    - **page**: 페이지 번호 (1부터 시작)
    - **page_size**: 페이지 크기 (최대 100)
    - **project_id**: 특정 프로젝트의 스프린트만 조회
    - **status**: 스프린트 상태로 필터링
    - **sort_by**: 정렬 기준 필드
    - **order**: 정렬 순서 (asc 또는 desc)
    """
    builder = QueryBuilder(select(Sprint), Sprint)

    # 프로젝트 필터
    if project_id:
        builder.filter(project_id=project_id)

    # 상태 필터
    if status:
        builder.filter(status=status)

    # 정렬
    builder.sort(sort_by, order)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.post("", response_model=SprintResponse, status_code=201)
def create_sprint(
    sprint_in: SprintCreate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    스프린트 생성

    새로운 스프린트를 생성합니다.

    **필수 필드**:
    - **project_id**: 프로젝트 ID
    - **name**: 스프린트 이름

    **선택 필드**:
    - **goal**: 스프린트 목표
    - **start_date**: 시작일
    - **end_date**: 종료일
    - **status**: 스프린트 상태 (기본값: PLANNED)
    """
    # 스프린트 생성
    sprint = crud_sprint.create(db, obj_in=sprint_in)

    return sprint


@router.get("/{sprint_id}", response_model=SprintResponse)
def get_sprint(
    sprint_id: Annotated[int, Path(description="스프린트 ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    스프린트 상세 조회

    특정 스프린트의 상세 정보를 조회합니다.
    """
    sprint = crud_sprint.get(db, id=sprint_id)
    if not sprint:
        raise NotFoundError(f"Sprint {sprint_id} not found")

    return sprint


@router.put("/{sprint_id}", response_model=SprintResponse)
def update_sprint(
    sprint_id: Annotated[int, Path(description="스프린트 ID")],
    sprint_in: SprintUpdate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    스프린트 수정

    스프린트 정보를 수정합니다.
    제공된 필드만 업데이트됩니다.

    **수정 가능 필드**:
    - **name**: 스프린트 이름
    - **goal**: 스프린트 목표
    - **start_date**: 시작일
    - **end_date**: 종료일
    - **status**: 스프린트 상태
    """
    # 스프린트 존재 확인
    sprint = crud_sprint.get(db, id=sprint_id)
    if not sprint:
        raise NotFoundError(f"Sprint {sprint_id} not found")

    # 스프린트 업데이트
    updated_sprint = crud_sprint.update(db, db_obj=sprint, obj_in=sprint_in)

    return updated_sprint


@router.delete("/{sprint_id}", response_model=SuccessResponse)
def delete_sprint(
    sprint_id: Annotated[int, Path(description="스프린트 ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    스프린트 삭제

    스프린트를 삭제합니다.
    연관된 이슈들은 백로그로 이동됩니다.
    """
    # 스프린트 존재 확인
    sprint = crud_sprint.get(db, id=sprint_id)
    if not sprint:
        raise NotFoundError(f"Sprint {sprint_id} not found")

    # 스프린트 삭제
    crud_sprint.delete(db, id=sprint_id)

    return SuccessResponse(
        success=True,
        message=f"Sprint '{sprint.name}' deleted successfully"
    )


@router.post("/{sprint_id}/start", response_model=SprintResponse)
def start_sprint(
    sprint_id: Annotated[int, Path(description="스프린트 ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    스프린트 시작

    스프린트를 시작합니다. 상태가 ACTIVE로 변경됩니다.

    **제약 조건**:
    - 프로젝트당 하나의 활성 스프린트만 가능
    - PLANNED 상태의 스프린트만 시작 가능
    """
    # 스프린트 존재 확인
    sprint = crud_sprint.get(db, id=sprint_id)
    if not sprint:
        raise NotFoundError(f"Sprint {sprint_id} not found")

    # 이미 활성화된 스프린트가 있는지 확인
    active_sprint = crud_sprint.get_active_sprint(db, project_id=sprint.project_id)
    if active_sprint and active_sprint.id != sprint_id:
        raise BadRequestError(
            f"Project already has an active sprint: '{active_sprint.name}'"
        )

    # 스프린트 시작
    started_sprint = crud_sprint.start_sprint(db, sprint_id=sprint_id)

    return started_sprint


@router.post("/{sprint_id}/complete", response_model=SprintResponse)
def complete_sprint(
    sprint_id: Annotated[int, Path(description="스프린트 ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    스프린트 완료

    스프린트를 완료합니다. 상태가 COMPLETED로 변경됩니다.

    **참고**:
    - 완료되지 않은 이슈는 백로그로 이동할 수 있습니다.
    """
    # 스프린트 존재 확인
    sprint = crud_sprint.get(db, id=sprint_id)
    if not sprint:
        raise NotFoundError(f"Sprint {sprint_id} not found")

    # 스프린트 완료
    completed_sprint = crud_sprint.complete_sprint(db, sprint_id=sprint_id)

    return completed_sprint


@router.patch("/{sprint_id}/status", response_model=SprintResponse)
def update_sprint_status(
    sprint_id: Annotated[int, Path(description="스프린트 ID")],
    status: Annotated[SprintStatus, Query(description="새로운 스프린트 상태")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    스프린트 상태 변경

    스프린트의 상태만 변경합니다.

    **상태 종류**:
    - **PLANNED**: 계획됨
    - **ACTIVE**: 진행 중
    - **COMPLETED**: 완료
    """
    # 스프린트 존재 확인
    sprint = crud_sprint.get(db, id=sprint_id)
    if not sprint:
        raise NotFoundError(f"Sprint {sprint_id} not found")

    # ACTIVE로 변경하는 경우, 다른 활성 스프린트 확인
    if status == SprintStatus.ACTIVE:
        active_sprint = crud_sprint.get_active_sprint(db, project_id=sprint.project_id)
        if active_sprint and active_sprint.id != sprint_id:
            raise BadRequestError(
                f"Project already has an active sprint: '{active_sprint.name}'"
            )

    # 상태 변경
    sprint.status = status
    db.add(sprint)
    db.commit()
    db.refresh(sprint)

    return sprint


@router.get("/project/{project_id}", response_model=PaginatedResponse[SprintListResponse])
def list_project_sprints(
    project_id: Annotated[int, Path(description="프로젝트 ID")],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: SprintStatus | None = Query(default=None),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    프로젝트의 스프린트 목록 조회

    특정 프로젝트에 속한 스프린트 목록을 조회합니다.
    """
    builder = QueryBuilder(select(Sprint), Sprint).filter(project_id=project_id)

    if status:
        builder.filter(status=status)

    builder.sort("created_at", SortOrder.DESC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/project/{project_id}/active", response_model=SprintResponse)
def get_active_sprint(
    project_id: Annotated[int, Path(description="프로젝트 ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    프로젝트의 활성 스프린트 조회

    프로젝트의 현재 진행 중인 스프린트를 조회합니다.
    """
    sprint = crud_sprint.get_active_sprint(db, project_id=project_id)
    if not sprint:
        raise NotFoundError(f"No active sprint found for project {project_id}")

    return sprint
