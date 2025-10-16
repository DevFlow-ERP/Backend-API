"""
Deployment API endpoints
Deployment history and management API
"""

from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import crud_deployment, crud_service
from app.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.deployment import Deployment, DeploymentType, DeploymentStatus
from app.schemas.deployment import (
    DeploymentCreate,
    DeploymentUpdate,
    DeploymentResponse,
    DeploymentListResponse,
    DeploymentRollbackRequest,
)
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.utils import (
    paginate,
    create_paginated_response,
    QueryBuilder,
    SortOrder,
)

router = APIRouter(prefix="/deployments", tags=["Deployments"])


@router.get("", response_model=PaginatedResponse[DeploymentListResponse])
def list_deployments(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    service_id: int | None = Query(default=None, description="Filter by service ID"),
    environment: str | None = Query(default=None, description="Filter by environment"),
    type: DeploymentType | None = Query(default=None, description="Filter by deployment type"),
    status: DeploymentStatus | None = Query(default=None, description="Filter by deployment status"),
    deployed_by: int | None = Query(default=None, description="Filter by deployer user ID"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    order: SortOrder = Query(default=SortOrder.DESC, description="Sort order"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get deployment history

    - **page**: Page number (starting from 1)
    - **page_size**: Page size (max 100)
    - **service_id**: Filter by service ID
    - **environment**: Filter by environment
    - **type**: Filter by deployment type
    - **status**: Filter by deployment status
    - **deployed_by**: Filter by deployer user ID
    - **sort_by**: Sort field
    - **order**: Sort order (asc or desc)
    """
    builder = QueryBuilder(select(Deployment), Deployment)

    # Filters
    if service_id:
        builder.filter(service_id=service_id)
    if environment:
        builder.filter(environment=environment)
    if type:
        builder.filter(type=type)
    if status:
        builder.filter(status=status)
    if deployed_by:
        builder.filter(deployed_by=deployed_by)

    # Sort
    builder.sort(sort_by, order)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.post("", response_model=DeploymentResponse, status_code=201)
def create_deployment(
    deployment_in: DeploymentCreate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Record a new deployment

    Records a new deployment for a service.

    **Required fields**:
    - **service_id**: Service ID
    - **version**: Deployment version
    - **environment**: Deployment environment (dev, staging, production, test)

    **Optional fields**:
    - **commit_hash**: Git commit hash (40 characters)
    - **branch**: Git branch name
    - **tag**: Git tag
    - **type**: Deployment type (default: manual)
    - **status**: Deployment status (default: pending)
    - **notes**: Deployment notes
    """
    # Check if service exists
    service = crud_service.get(db, id=deployment_in.service_id)
    if not service:
        raise NotFoundError(f"Service {deployment_in.service_id} not found")

    # Create deployment with deployed_by set to current user
    deployment_data = deployment_in.model_dump()
    deployment_data["deployed_by"] = current_user.id
    deployment_data["started_at"] = datetime.now()

    deployment = crud_deployment.create(db, obj_in=deployment_data)

    return deployment


@router.get("/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(
    deployment_id: Annotated[int, Path(description="Deployment ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get deployment details

    Returns detailed information about a specific deployment.
    """
    deployment = crud_deployment.get(db, id=deployment_id)
    if not deployment:
        raise NotFoundError(f"Deployment {deployment_id} not found")

    return deployment


@router.put("/{deployment_id}", response_model=DeploymentResponse)
def update_deployment(
    deployment_id: Annotated[int, Path(description="Deployment ID")],
    deployment_in: DeploymentUpdate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Update deployment information

    Updates deployment information. Only provided fields will be updated.

    **Updatable fields**:
    - **status**: Deployment status
    - **started_at**: Deployment start time
    - **completed_at**: Deployment completion time
    - **notes**: Deployment notes
    - **error_message**: Error message (if failed)
    - **log_url**: Deployment log URL
    """
    # Check if deployment exists
    deployment = crud_deployment.get(db, id=deployment_id)
    if not deployment:
        raise NotFoundError(f"Deployment {deployment_id} not found")

    # Update deployment
    updated_deployment = crud_deployment.update(db, db_obj=deployment, obj_in=deployment_in)

    return updated_deployment


@router.delete("/{deployment_id}", response_model=SuccessResponse)
def delete_deployment(
    deployment_id: Annotated[int, Path(description="Deployment ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Delete a deployment record

    Deletes a deployment record from the history.
    """
    # Check if deployment exists
    deployment = crud_deployment.get(db, id=deployment_id)
    if not deployment:
        raise NotFoundError(f"Deployment {deployment_id} not found")

    # Delete deployment
    crud_deployment.delete(db, id=deployment_id)

    return SuccessResponse(
        success=True,
        message=f"Deployment {deployment.version} (ID: {deployment_id}) deleted successfully"
    )


@router.patch("/{deployment_id}/status", response_model=DeploymentResponse)
def update_deployment_status(
    deployment_id: Annotated[int, Path(description="Deployment ID")],
    status: Annotated[DeploymentStatus, Query(description="New deployment status")],
    error_message: str | None = Query(default=None, description="Error message (if status is failed)"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Update deployment status

    Updates the status of a deployment.

    **Deployment Status**:
    - **PENDING**: Deployment is pending
    - **IN_PROGRESS**: Deployment is in progress
    - **SUCCESS**: Deployment completed successfully
    - **FAILED**: Deployment failed
    - **ROLLED_BACK**: Deployment was rolled back
    """
    # Check if deployment exists
    deployment = crud_deployment.get(db, id=deployment_id)
    if not deployment:
        raise NotFoundError(f"Deployment {deployment_id} not found")

    # Update status
    update_data = {"status": status}

    # Set completed_at if status is terminal (SUCCESS, FAILED, ROLLED_BACK)
    if status in [DeploymentStatus.SUCCESS, DeploymentStatus.FAILED, DeploymentStatus.ROLLED_BACK]:
        update_data["completed_at"] = datetime.now()

    # Set error_message if status is FAILED
    if status == DeploymentStatus.FAILED and error_message:
        update_data["error_message"] = error_message

    updated_deployment = crud_deployment.update(db, db_obj=deployment, obj_in=update_data)

    return updated_deployment


@router.post("/{deployment_id}/rollback", response_model=DeploymentResponse, status_code=201)
def rollback_deployment(
    deployment_id: Annotated[int, Path(description="Deployment ID to rollback to")],
    notes: str | None = Query(default=None, description="Rollback notes"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Rollback to a previous deployment

    Creates a new rollback deployment that reverts to the specified deployment version.
    The target deployment must be a successful deployment.

    **Process**:
    1. Validates that target deployment exists and was successful
    2. Creates a new deployment record of type ROLLBACK
    3. Copies version, commit_hash, branch, tag from target deployment
    4. Sets rollback_from_id to reference the target deployment
    """
    # Check if target deployment exists
    target_deployment = crud_deployment.get(db, id=deployment_id)
    if not target_deployment:
        raise NotFoundError(f"Deployment {deployment_id} not found")

    # Validate target deployment status
    if target_deployment.status != DeploymentStatus.SUCCESS:
        raise BadRequestError(
            f"Cannot rollback to deployment {deployment_id} with status '{target_deployment.status}'. "
            "Only successful deployments can be used as rollback targets."
        )

    # Create rollback deployment
    rollback_data = {
        "service_id": target_deployment.service_id,
        "deployed_by": current_user.id,
        "version": target_deployment.version,
        "commit_hash": target_deployment.commit_hash,
        "branch": target_deployment.branch,
        "tag": target_deployment.tag,
        "type": DeploymentType.ROLLBACK,
        "status": DeploymentStatus.PENDING,
        "environment": target_deployment.environment,
        "rollback_from_id": deployment_id,
        "notes": notes or f"Rollback to deployment {deployment_id} (version {target_deployment.version})",
        "started_at": datetime.now(),
    }

    rollback_deployment = crud_deployment.create(db, obj_in=rollback_data)

    return rollback_deployment


@router.get("/service/{service_id}", response_model=PaginatedResponse[DeploymentListResponse])
def list_deployments_by_service(
    service_id: Annotated[int, Path(description="Service ID")],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: DeploymentStatus | None = Query(default=None),
    type: DeploymentType | None = Query(default=None),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get deployment history for a service

    Returns a list of deployments for the specified service.
    """
    # Check if service exists
    service = crud_service.get(db, id=service_id)
    if not service:
        raise NotFoundError(f"Service {service_id} not found")

    builder = QueryBuilder(select(Deployment), Deployment).filter(service_id=service_id)

    if status:
        builder.filter(status=status)
    if type:
        builder.filter(type=type)

    builder.sort("created_at", SortOrder.DESC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/environment/{environment}", response_model=PaginatedResponse[DeploymentListResponse])
def list_deployments_by_environment(
    environment: Annotated[str, Path(description="Environment name")],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: DeploymentStatus | None = Query(default=None),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get deployments by environment

    Returns a list of deployments for the specified environment.

    **Environments**:
    - **dev**: Development environment
    - **staging**: Staging environment
    - **production**: Production environment
    - **test**: Test environment
    """
    builder = QueryBuilder(select(Deployment), Deployment).filter(environment=environment)

    if status:
        builder.filter(status=status)

    builder.sort("created_at", SortOrder.DESC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/status/success", response_model=PaginatedResponse[DeploymentListResponse])
def list_successful_deployments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service_id: int | None = Query(default=None, description="Filter by service ID"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get successful deployments

    Returns a list of all deployments that completed successfully.
    """
    builder = QueryBuilder(select(Deployment), Deployment).filter(status=DeploymentStatus.SUCCESS)

    if service_id:
        builder.filter(service_id=service_id)

    builder.sort("created_at", SortOrder.DESC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/type/rollback", response_model=PaginatedResponse[DeploymentListResponse])
def list_rollback_deployments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get rollback deployments

    Returns a list of all rollback deployments.
    """
    builder = QueryBuilder(select(Deployment), Deployment).filter(type=DeploymentType.ROLLBACK)
    builder.sort("created_at", SortOrder.DESC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/status/failed", response_model=PaginatedResponse[DeploymentListResponse])
def list_failed_deployments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service_id: int | None = Query(default=None, description="Filter by service ID"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get failed deployments

    Returns a list of all deployments that failed.
    """
    builder = QueryBuilder(select(Deployment), Deployment).filter(status=DeploymentStatus.FAILED)

    if service_id:
        builder.filter(service_id=service_id)

    builder.sort("created_at", SortOrder.DESC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/user/{user_id}", response_model=PaginatedResponse[DeploymentListResponse])
def list_deployments_by_user(
    user_id: Annotated[int, Path(description="User ID")],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get deployments by user

    Returns a list of deployments performed by the specified user.
    """
    builder = QueryBuilder(select(Deployment), Deployment).filter(deployed_by=user_id)
    builder.sort("created_at", SortOrder.DESC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)
