"""
Issue API endpoints
이슈 관리 API
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.crud import crud_issue, crud_project
from app.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.issue import Issue, IssueType, IssuePriority, IssueStatus
from app.schemas.issue import (
    IssueCreate,
    IssueUpdate,
    IssueResponse,
    IssueListResponse,
)
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.utils import (
    paginate,
    create_paginated_response,
    QueryBuilder,
    SortOrder,
)

router = APIRouter(prefix="/issues", tags=["Issues"])


def generate_issue_key(db: Session, project_id: int) -> str:
    """
    이슈 키 생성 (예: PROJ-123)

    Args:
        db: 데이터베이스 세션
        project_id: 프로젝트 ID

    Returns:
        str: 생성된 이슈 키
    """
    # 프로젝트 조회
    project = crud_project.get(db, id=project_id)
    if not project:
        raise NotFoundError(f"Project {project_id} not found")

    # 프로젝트의 마지막 이슈 번호 조회
    last_issue = (
        db.query(Issue)
        .filter(Issue.project_id == project_id)
        .order_by(Issue.id.desc())
        .first()
    )

    # 다음 번호 계산
    if last_issue and last_issue.key:
        # 기존 이슈가 있으면 마지막 번호에서 +1
        try:
            last_number = int(last_issue.key.split("-")[-1])
            next_number = last_number + 1
        except (ValueError, IndexError):
            # 파싱 실패 시 프로젝트의 전체 이슈 수 + 1
            issue_count = db.query(func.count(Issue.id)).filter(Issue.project_id == project_id).scalar()
            next_number = (issue_count or 0) + 1
    else:
        # 첫 번째 이슈
        next_number = 1

    return f"{project.key}-{next_number}"


@router.get("", response_model=PaginatedResponse[IssueListResponse])
def list_issues(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    page_size: int = Query(default=20, ge=1, le=100, description="페이지 크기"),
    project_id: int | None = Query(default=None, description="프로젝트 ID 필터"),
    sprint_id: int | None = Query(default=None, description="스프린트 ID 필터 (null=백로그)"),
    assignee_id: int | None = Query(default=None, description="담당자 ID 필터"),
    type: IssueType | None = Query(default=None, description="이슈 타입 필터"),
    priority: IssuePriority | None = Query(default=None, description="우선순위 필터"),
    status: IssueStatus | None = Query(default=None, description="이슈 상태 필터"),
    search: str | None = Query(default=None, description="검색어 (제목, 설명)"),
    sort_by: str = Query(default="order", description="정렬 필드"),
    order: SortOrder = Query(default=SortOrder.ASC, description="정렬 순서"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    이슈 목록 조회

    - **page**: 페이지 번호 (1부터 시작)
    - **page_size**: 페이지 크기 (최대 100)
    - **project_id**: 특정 프로젝트의 이슈만 조회
    - **sprint_id**: 특정 스프린트의 이슈만 조회 (null로 전달하면 백로그)
    - **assignee_id**: 특정 담당자의 이슈만 조회
    - **type**: 이슈 타입으로 필터링
    - **priority**: 우선순위로 필터링
    - **status**: 이슈 상태로 필터링
    - **search**: 제목, 설명에서 검색
    - **sort_by**: 정렬 기준 필드
    - **order**: 정렬 순서 (asc 또는 desc)
    """
    builder = QueryBuilder(select(Issue), Issue)

    # 필터링
    if project_id:
        builder.filter(project_id=project_id)
    if sprint_id is not None:
        builder.filter(sprint_id=sprint_id)
    if assignee_id:
        builder.filter(assignee_id=assignee_id)
    if type:
        builder.filter(type=type)
    if priority:
        builder.filter(priority=priority)
    if status:
        builder.filter(status=status)

    # 검색
    if search:
        builder.search(["title", "description"], search)

    # 정렬
    builder.sort(sort_by, order)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.post("", response_model=IssueResponse, status_code=201)
def create_issue(
    issue_in: IssueCreate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    이슈 생성

    새로운 이슈를 생성합니다. 이슈 키는 자동으로 생성됩니다.

    **필수 필드**:
    - **project_id**: 프로젝트 ID
    - **title**: 이슈 제목

    **선택 필드**:
    - **description**: 이슈 설명
    - **type**: 이슈 타입 (기본값: TASK)
    - **priority**: 우선순위 (기본값: MEDIUM)
    - **status**: 이슈 상태 (기본값: TODO)
    - **sprint_id**: 스프린트 ID (null이면 백로그)
    - **assignee_id**: 담당자 ID
    - **estimate_hours**: 예상 소요 시간
    """
    # 프로젝트 존재 확인
    project = crud_project.get(db, id=issue_in.project_id)
    if not project:
        raise NotFoundError(f"Project {issue_in.project_id} not found")

    # 이슈 키 생성
    issue_key = generate_issue_key(db, issue_in.project_id)

    # 이슈 생성 데이터 준비
    issue_data = issue_in.model_dump()
    issue_data["key"] = issue_key
    issue_data["creator_id"] = current_user.id

    # 이슈 생성
    db_issue = Issue(**issue_data)
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)

    return db_issue


@router.get("/my", response_model=PaginatedResponse[IssueListResponse])
def list_my_issues(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: IssueStatus | None = Query(default=None),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    내가 담당한 이슈 목록 조회

    현재 로그인한 사용자가 담당한 이슈 목록을 조회합니다.
    """
    builder = QueryBuilder(select(Issue), Issue).filter(assignee_id=current_user.id)

    if status:
        builder.filter(status=status)

    builder.sort("order", SortOrder.ASC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/project/{project_id}/backlog", response_model=PaginatedResponse[IssueListResponse])
def list_backlog(
    project_id: Annotated[int, Path(description="프로젝트 ID")],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    프로젝트 백로그 조회

    스프린트에 할당되지 않은 이슈 목록을 조회합니다.
    """
    # 프로젝트 존재 확인
    project = crud_project.get(db, id=project_id)
    if not project:
        raise NotFoundError(f"Project {project_id} not found")

    builder = QueryBuilder(select(Issue), Issue).filter(
        project_id=project_id,
        sprint_id=None
    )
    builder.sort("order", SortOrder.ASC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/sprint/{sprint_id}", response_model=PaginatedResponse[IssueListResponse])
def list_sprint_issues(
    sprint_id: Annotated[int, Path(description="스프린트 ID")],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: IssueStatus | None = Query(default=None),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    스프린트 이슈 목록 조회

    특정 스프린트에 할당된 이슈 목록을 조회합니다.
    """
    builder = QueryBuilder(select(Issue), Issue).filter(sprint_id=sprint_id)

    if status:
        builder.filter(status=status)

    builder.sort("order", SortOrder.ASC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(
    issue_id: Annotated[int, Path(description="이슈 ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    이슈 상세 조회

    특정 이슈의 상세 정보를 조회합니다.
    """
    issue = crud_issue.get(db, id=issue_id)
    if not issue:
        raise NotFoundError(f"Issue {issue_id} not found")

    return issue


@router.put("/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: Annotated[int, Path(description="이슈 ID")],
    issue_in: IssueUpdate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    이슈 수정

    이슈 정보를 수정합니다.
    제공된 필드만 업데이트됩니다.

    **수정 가능 필드**:
    - **title**: 이슈 제목
    - **description**: 이슈 설명
    - **type**: 이슈 타입
    - **priority**: 우선순위
    - **status**: 이슈 상태
    - **sprint_id**: 스프린트 ID
    - **assignee_id**: 담당자 ID
    - **estimate_hours**: 예상 소요 시간
    - **actual_hours**: 실제 소요 시간
    - **order**: 정렬 순서
    """
    # 이슈 존재 확인
    issue = crud_issue.get(db, id=issue_id)
    if not issue:
        raise NotFoundError(f"Issue {issue_id} not found")

    # 이슈 업데이트
    updated_issue = crud_issue.update(db, db_obj=issue, obj_in=issue_in)

    return updated_issue


@router.delete("/{issue_id}", response_model=SuccessResponse)
def delete_issue(
    issue_id: Annotated[int, Path(description="이슈 ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    이슈 삭제

    이슈를 삭제합니다.
    """
    # 이슈 존재 확인
    issue = crud_issue.get(db, id=issue_id)
    if not issue:
        raise NotFoundError(f"Issue {issue_id} not found")

    # 이슈 삭제
    crud_issue.delete(db, id=issue_id)

    return SuccessResponse(
        success=True,
        message=f"Issue '{issue.key}' deleted successfully"
    )


@router.patch("/{issue_id}/status", response_model=IssueResponse)
def update_issue_status(
    issue_id: Annotated[int, Path(description="이슈 ID")],
    status: Annotated[IssueStatus, Query(description="새로운 이슈 상태")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    이슈 상태 변경

    이슈의 상태만 변경합니다.

    **상태 종류**:
    - **TODO**: 할 일
    - **IN_PROGRESS**: 진행 중
    - **IN_REVIEW**: 리뷰 중
    - **TESTING**: 테스트 중
    - **DONE**: 완료
    - **CLOSED**: 종료
    """
    # 이슈 존재 확인
    issue = crud_issue.get(db, id=issue_id)
    if not issue:
        raise NotFoundError(f"Issue {issue_id} not found")

    # 상태 변경
    updated_issue = crud_issue.update_status(db, issue_id=issue_id, status=status)

    return updated_issue


@router.patch("/{issue_id}/assign", response_model=IssueResponse)
def assign_issue(
    issue_id: Annotated[int, Path(description="이슈 ID")],
    assignee_id: Annotated[int | None, Body(embed=True, description="담당자 ID (null이면 할당 해제)")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    이슈 담당자 변경

    이슈의 담당자를 변경합니다.
    assignee_id를 null로 전달하면 담당자 할당이 해제됩니다.
    """
    # 이슈 존재 확인
    issue = crud_issue.get(db, id=issue_id)
    if not issue:
        raise NotFoundError(f"Issue {issue_id} not found")

    # 담당자 변경
    issue.assignee_id = assignee_id
    db.add(issue)
    db.commit()
    db.refresh(issue)

    return issue


@router.patch("/{issue_id}/sprint", response_model=IssueResponse)
def move_issue_to_sprint(
    issue_id: Annotated[int, Path(description="이슈 ID")],
    sprint_id: Annotated[int | None, Body(embed=True, description="스프린트 ID (null이면 백로그로 이동)")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    이슈를 스프린트에 할당 또는 백로그로 이동

    이슈를 특정 스프린트에 할당하거나 백로그로 이동합니다.
    sprint_id를 null로 전달하면 백로그로 이동합니다.
    """
    # 이슈 존재 확인
    issue = crud_issue.get(db, id=issue_id)
    if not issue:
        raise NotFoundError(f"Issue {issue_id} not found")

    # 스프린트 할당
    updated_issue = crud_issue.assign_to_sprint(db, issue_id=issue_id, sprint_id=sprint_id)

    return updated_issue
