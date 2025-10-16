"""
Service API endpoints
Service management API
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.crud import crud_service, crud_server
from app.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.service import Service, ServiceType, ServiceStatus
from app.models.deployment import Deployment
from app.schemas.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceListResponse,
)
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.utils import (
    paginate,
    create_paginated_response,
    QueryBuilder,
    SortOrder,
)

router = APIRouter(prefix="/services", tags=["Services"])


@router.get("", response_model=PaginatedResponse[ServiceListResponse])
def list_services(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    server_id: int | None = Query(default=None, description="Filter by server ID"),
    type: ServiceType | None = Query(default=None, description="Filter by service type"),
    status: ServiceStatus | None = Query(default=None, description="Filter by service status"),
    search: str | None = Query(default=None, description="Search in name"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    order: SortOrder = Query(default=SortOrder.DESC, description="Sort order"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get service list

    - **page**: Page number (starting from 1)
    - **page_size**: Page size (max 100)
    - **server_id**: Filter by server ID
    - **type**: Filter by service type
    - **status**: Filter by service status
    - **search**: Search in service name
    - **sort_by**: Sort field
    - **order**: Sort order (asc or desc)
    """
    builder = QueryBuilder(select(Service), Service)

    # Filters
    if server_id:
        builder.filter(server_id=server_id)
    if type:
        builder.filter(type=type)
    if status:
        builder.filter(status=status)

    # Search
    if search:
        builder.search(["name"], search)

    # Sort
    builder.sort(sort_by, order)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.post("", response_model=ServiceResponse, status_code=201)
def create_service(
    service_in: ServiceCreate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Register a new service

    Registers a new service running on a server.

    **Required fields**:
    - **name**: Service name
    - **server_id**: Server ID where service runs
    - **type**: Service type

    **Optional fields**:
    - **status**: Service status (default: stopped)
    - **version**: Service version
    - **port**: Service port
    - **url**: Service URL
    - **process_name**: Process name
    - **pid**: Process ID
    - **container_id**: Container ID (for Docker, etc.)
    - **image_name**: Container image name
    - **cpu_limit**: CPU limit (%)
    - **memory_limit_mb**: Memory limit (MB)
    - **health_check_url**: Health check URL
    - **health_check_enabled**: Enable health check (default: false)
    - **environment_variables**: Environment variables (JSON)
    - **config_path**: Configuration file path
    - **log_path**: Log file path
    - **auto_start**: Auto start on boot (default: false)
    - **description**: Service description
    - **notes**: Additional notes
    """
    # Check if server exists
    server = crud_server.get(db, id=service_in.server_id)
    if not server:
        raise NotFoundError(f"Server {service_in.server_id} not found")

    # Create service
    service = crud_service.create(db, obj_in=service_in)

    # Add deployment count
    service.deployment_count = 0

    return service


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(
    service_id: Annotated[int, Path(description="Service ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get service details

    Returns detailed information about a specific service.
    """
    service = crud_service.get(db, id=service_id)
    if not service:
        raise NotFoundError(f"Service {service_id} not found")

    # Add deployment count
    service.deployment_count = db.query(func.count(Deployment.id)).filter(
        Deployment.service_id == service_id
    ).scalar() or 0

    return service


@router.put("/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: Annotated[int, Path(description="Service ID")],
    service_in: ServiceUpdate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Update service information

    Updates service information. Only provided fields will be updated.

    **Updatable fields**:
    - All fields except id and server_id
    """
    # Check if service exists
    service = crud_service.get(db, id=service_id)
    if not service:
        raise NotFoundError(f"Service {service_id} not found")

    # Update service
    updated_service = crud_service.update(db, db_obj=service, obj_in=service_in)

    # Add deployment count
    updated_service.deployment_count = db.query(func.count(Deployment.id)).filter(
        Deployment.service_id == service_id
    ).scalar() or 0

    return updated_service


@router.delete("/{service_id}", response_model=SuccessResponse)
def delete_service(
    service_id: Annotated[int, Path(description="Service ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Delete a service

    Deletes a service from the inventory.
    All deployment history for this service will also be deleted (cascade).
    """
    # Check if service exists
    service = crud_service.get(db, id=service_id)
    if not service:
        raise NotFoundError(f"Service {service_id} not found")

    # Check if service has deployments
    deployment_count = db.query(func.count(Deployment.id)).filter(
        Deployment.service_id == service_id
    ).scalar() or 0

    # Delete service
    crud_service.delete(db, id=service_id)

    return SuccessResponse(
        success=True,
        message=f"Service '{service.name}' deleted successfully ({deployment_count} deployment records removed)"
    )


@router.patch("/{service_id}/status", response_model=ServiceResponse)
def update_service_status(
    service_id: Annotated[int, Path(description="Service ID")],
    status: Annotated[ServiceStatus, Query(description="New service status")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Update service status

    Updates the status of a service.

    **Service Status**:
    - **RUNNING**: Service is running normally
    - **STOPPED**: Service is stopped
    - **DEGRADED**: Service is running but degraded
    - **MAINTENANCE**: Service is under maintenance
    - **FAILED**: Service has failed
    """
    # Check if service exists
    service = crud_service.get(db, id=service_id)
    if not service:
        raise NotFoundError(f"Service {service_id} not found")

    # Update status
    updated_service = crud_service.update_status(db, service_id=service_id, status=status)

    # Add deployment count
    updated_service.deployment_count = db.query(func.count(Deployment.id)).filter(
        Deployment.service_id == service_id
    ).scalar() or 0

    return updated_service


@router.get("/server/{server_id}", response_model=PaginatedResponse[ServiceListResponse])
def list_services_by_server(
    server_id: Annotated[int, Path(description="Server ID")],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: ServiceStatus | None = Query(default=None),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get services running on a server

    Returns a list of services running on the specified server.
    """
    # Check if server exists
    server = crud_server.get(db, id=server_id)
    if not server:
        raise NotFoundError(f"Server {server_id} not found")

    builder = QueryBuilder(select(Service), Service).filter(server_id=server_id)

    if status:
        builder.filter(status=status)

    builder.sort("name", SortOrder.ASC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/type/{service_type}", response_model=PaginatedResponse[ServiceListResponse])
def list_services_by_type(
    service_type: Annotated[ServiceType, Path(description="Service type")],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get services by type

    Returns a list of services of the specified type.

    **Service Types**:
    - **WEB**: Web application
    - **API**: API service
    - **DATABASE**: Database service
    - **CACHE**: Cache service (Redis, Memcached)
    - **QUEUE**: Message queue (RabbitMQ, Kafka)
    - **WORKER**: Background worker
    - **CRON**: Scheduled tasks
    - **OTHER**: Other types
    """
    builder = QueryBuilder(select(Service), Service).filter(type=service_type)
    builder.sort("name", SortOrder.ASC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)


@router.get("/status/running", response_model=PaginatedResponse[ServiceListResponse])
def list_running_services(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get running services

    Returns a list of all services that are currently running.
    """
    builder = QueryBuilder(select(Service), Service).filter(status=ServiceStatus.RUNNING)
    builder.sort("name", SortOrder.ASC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    return create_paginated_response(items, meta)
