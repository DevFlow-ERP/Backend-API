"""
Dashboard API endpoints
대시보드 통계 및 요약 정보 제공
"""

from typing import Any
from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.dependencies import CurrentUser, DBSession
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.issue import Issue
from app.models.deployment import Deployment

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    db: DBSession = None,
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    """
    대시보드 통계 데이터 조회

    Returns:
        - total_projects: 전체 프로젝트 수
        - active_sprints: 활성 스프린트 수
        - open_issues: 오픈 이슈 수 (TODO, IN_PROGRESS, IN_REVIEW, TESTING)
        - my_tasks: 내가 담당한 이슈 수
    """

    # 전체 프로젝트 수
    total_projects_query = select(func.count(Project.id))
    total_projects_result = db.execute(total_projects_query)
    total_projects = total_projects_result.scalar() or 0

    # 활성 스프린트 수 (status = 'active')
    active_sprints_query = select(func.count(Sprint.id)).where(Sprint.status == "active")
    active_sprints_result = db.execute(active_sprints_query)
    active_sprints = active_sprints_result.scalar() or 0

    # 오픈 이슈 수 (DONE, CLOSED 제외)
    open_issues_query = select(func.count(Issue.id)).where(
        Issue.status.in_(["todo", "in_progress", "in_review", "testing"])
    )
    open_issues_result = db.execute(open_issues_query)
    open_issues = open_issues_result.scalar() or 0

    # 내가 담당한 이슈 수 (assignee_id = current_user.id)
    my_tasks_query = select(func.count(Issue.id)).where(
        Issue.assignee_id == current_user.id,
        Issue.status.in_(["todo", "in_progress", "in_review", "testing"])
    )
    my_tasks_result = db.execute(my_tasks_query)
    my_tasks = my_tasks_result.scalar() or 0

    return {
        "total_projects": total_projects,
        "active_sprints": active_sprints,
        "open_issues": open_issues,
        "my_tasks": my_tasks,
    }


@router.get("/recent-projects")
def get_recent_projects(
    limit: int = Query(default=5, ge=1, le=20),
    db: DBSession = None,
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    """
    최근 프로젝트 목록 조회 (updated_at 기준)

    Args:
        limit: 조회할 프로젝트 수 (기본값: 5)
    """
    from app.schemas.project import ProjectResponse

    query = (
        select(Project)
        .order_by(Project.updated_at.desc())
        .limit(limit)
    )
    result = db.execute(query)
    projects = result.scalars().all()

    return {
        "items": [ProjectResponse.model_validate(project) for project in projects]
    }


@router.get("/active-sprint")
def get_active_sprint(
    db: DBSession = None,
    current_user: CurrentUser = None,
) -> dict[str, Any] | None:
    """
    현재 활성 스프린트 조회 (가장 최근 활성 스프린트)
    번다운 차트용
    """
    from app.schemas.sprint import SprintResponse

    query = (
        select(Sprint)
        .where(Sprint.status == "active")
        .order_by(Sprint.start_date.desc())
        .limit(1)
    )
    result = db.execute(query)
    sprint = result.scalar_one_or_none()

    if not sprint:
        return None

    return SprintResponse.model_validate(sprint).model_dump()


@router.get("/my-issues")
def get_my_issues(
    limit: int = Query(default=10, ge=1, le=50),
    db: DBSession = None,
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    """
    내가 담당한 이슈 목록 조회

    Args:
        limit: 조회할 이슈 수 (기본값: 10)
    """
    from app.schemas.issue import IssueResponse

    query = (
        select(Issue)
        .where(
            Issue.assignee_id == current_user.id,
            Issue.status.in_(["todo", "in_progress", "in_review", "testing"])
        )
        .order_by(Issue.priority.desc(), Issue.updated_at.desc())
        .limit(limit)
    )
    result = db.execute(query)
    issues = result.scalars().all()

    return {
        "items": [IssueResponse.model_validate(issue) for issue in issues]
    }


@router.get("/recent-deployments")
def get_recent_deployments(
    limit: int = Query(default=5, ge=1, le=20),
    db: DBSession = None,
    current_user: CurrentUser = None,
) -> dict[str, Any]:
    """
    최근 배포 목록 조회

    Args:
        limit: 조회할 배포 수 (기본값: 5)
    """
    from app.schemas.deployment import DeploymentResponse

    query = (
        select(Deployment)
        .order_by(Deployment.created_at.desc())
        .limit(limit)
    )
    result = db.execute(query)
    deployments = result.scalars().all()

    return {
        "items": [DeploymentResponse.model_validate(deployment) for deployment in deployments]
    }
