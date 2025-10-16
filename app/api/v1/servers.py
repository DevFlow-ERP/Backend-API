"""
Server API endpoints
Server management API
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.crud import crud_server
from app.dependencies import CurrentUser, DBSession
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.server import Server, ServerType, ServerStatus
from app.models.service import Service
from app.schemas.server import (
    ServerCreate,
    ServerUpdate,
    ServerResponse,
    ServerListResponse,
)
from app.schemas.common import PaginatedResponse, SuccessResponse
from app.utils import (
    paginate,
    create_paginated_response,
    QueryBuilder,
    SortOrder,
)

router = APIRouter(prefix="/servers", tags=["Servers"])


@router.get("", response_model=PaginatedResponse[ServerListResponse])
def list_servers(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    type: ServerType | None = Query(default=None, description="Filter by server type"),
    status: ServerStatus | None = Query(default=None, description="Filter by server status"),
    environment: str | None = Query(default=None, description="Filter by environment"),
    search: str | None = Query(default=None, description="Search in name, hostname"),
    sort_by: str = Query(default="created_at", description="Sort field"),
    order: SortOrder = Query(default=SortOrder.DESC, description="Sort order"),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get server list

    - **page**: Page number (starting from 1)
    - **page_size**: Page size (max 100)
    - **type**: Filter by server type (physical, virtual, cloud, container)
    - **status**: Filter by server status (active, inactive, maintenance, decommissioned)
    - **environment**: Filter by environment (dev, staging, production)
    - **search**: Search in server name and hostname
    - **sort_by**: Sort field
    - **order**: Sort order (asc or desc)
    """
    builder = QueryBuilder(select(Server), Server)

    # Filters
    if type:
        builder.filter(type=type)
    if status:
        builder.filter(status=status)
    if environment:
        builder.filter(environment=environment)

    # Search
    if search:
        builder.search(["name", "hostname"], search)

    # Sort
    builder.sort(sort_by, order)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    # Add service count to each server
    for server in items:
        server.service_count = db.query(func.count(Service.id)).filter(
            Service.server_id == server.id
        ).scalar() or 0

    return create_paginated_response(items, meta)


@router.post("", response_model=ServerResponse, status_code=201)
def create_server(
    server_in: ServerCreate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Register a new server

    Registers a new server in the infrastructure inventory.

    **Required fields**:
    - **name**: Server name
    - **hostname**: Hostname
    - **ip_address**: IP address (IPv4 or IPv6)
    - **environment**: Environment (dev, staging, production)

    **Optional fields**:
    - **type**: Server type (default: virtual)
    - **status**: Server status (default: active)
    - **cpu_cores**: Number of CPU cores
    - **memory_gb**: Memory in GB
    - **disk_gb**: Disk capacity in GB
    - **os_name**: Operating system name
    - **os_version**: Operating system version
    - **provider**: Cloud provider (AWS, GCP, Azure, etc.)
    - **region**: Cloud region
    - **instance_id**: Cloud instance ID
    - **ssh_port**: SSH port (default: 22)
    - **ssh_user**: SSH username
    - **monitoring_enabled**: Enable monitoring (default: false)
    - **monitoring_url**: Monitoring dashboard URL
    - **description**: Server description
    - **notes**: Additional notes
    """
    # Check if server with same hostname exists
    existing_server = crud_server.get_by_hostname(db, hostname=server_in.hostname)
    if existing_server:
        raise BadRequestError(f"Server with hostname '{server_in.hostname}' already exists")

    # Create server
    server = crud_server.create(db, obj_in=server_in)

    # Add service count
    server.service_count = 0

    return server


@router.get("/{server_id}", response_model=ServerResponse)
def get_server(
    server_id: Annotated[int, Path(description="Server ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get server details

    Returns detailed information about a specific server.
    """
    server = crud_server.get(db, id=server_id)
    if not server:
        raise NotFoundError(f"Server {server_id} not found")

    # Add service count
    server.service_count = db.query(func.count(Service.id)).filter(
        Service.server_id == server_id
    ).scalar() or 0

    return server


@router.put("/{server_id}", response_model=ServerResponse)
def update_server(
    server_id: Annotated[int, Path(description="Server ID")],
    server_in: ServerUpdate,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Update server information

    Updates server information. Only provided fields will be updated.

    **Updatable fields**:
    - All fields except id
    """
    # Check if server exists
    server = crud_server.get(db, id=server_id)
    if not server:
        raise NotFoundError(f"Server {server_id} not found")

    # Check if hostname already exists (if updating)
    if server_in.hostname and server_in.hostname != server.hostname:
        existing_server = crud_server.get_by_hostname(db, hostname=server_in.hostname)
        if existing_server:
            raise BadRequestError(f"Server with hostname '{server_in.hostname}' already exists")

    # Update server
    updated_server = crud_server.update(db, db_obj=server, obj_in=server_in)

    # Add service count
    updated_server.service_count = db.query(func.count(Service.id)).filter(
        Service.server_id == server_id
    ).scalar() or 0

    return updated_server


@router.delete("/{server_id}", response_model=SuccessResponse)
def delete_server(
    server_id: Annotated[int, Path(description="Server ID")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Delete a server

    Deletes a server from the inventory.
    All services running on this server will also be deleted (cascade).
    """
    # Check if server exists
    server = crud_server.get(db, id=server_id)
    if not server:
        raise NotFoundError(f"Server {server_id} not found")

    # Check if server has services
    service_count = db.query(func.count(Service.id)).filter(
        Service.server_id == server_id
    ).scalar() or 0

    # Delete server
    crud_server.delete(db, id=server_id)

    return SuccessResponse(
        success=True,
        message=f"Server '{server.name}' deleted successfully ({service_count} services removed)"
    )


@router.patch("/{server_id}/status", response_model=ServerResponse)
def update_server_status(
    server_id: Annotated[int, Path(description="Server ID")],
    status: Annotated[ServerStatus, Query(description="New server status")],
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Update server status

    Updates the status of a server.

    **Server Status**:
    - **ACTIVE**: Server is active and running
    - **INACTIVE**: Server is inactive
    - **MAINTENANCE**: Server is under maintenance
    - **DECOMMISSIONED**: Server is decommissioned
    """
    # Check if server exists
    server = crud_server.get(db, id=server_id)
    if not server:
        raise NotFoundError(f"Server {server_id} not found")

    # Update status
    updated_server = crud_server.update_status(db, server_id=server_id, status=status)

    # Add service count
    updated_server.service_count = db.query(func.count(Service.id)).filter(
        Service.server_id == server_id
    ).scalar() or 0

    return updated_server


@router.get("/environment/{environment}", response_model=PaginatedResponse[ServerListResponse])
def list_servers_by_environment(
    environment: Annotated[str, Path(description="Environment name")],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get servers by environment

    Returns a list of servers in the specified environment.
    """
    builder = QueryBuilder(select(Server), Server).filter(environment=environment)
    builder.sort("name", SortOrder.ASC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    # Add service count to each server
    for server in items:
        server.service_count = db.query(func.count(Service.id)).filter(
            Service.server_id == server.id
        ).scalar() or 0

    return create_paginated_response(items, meta)


@router.get("/type/{server_type}", response_model=PaginatedResponse[ServerListResponse])
def list_servers_by_type(
    server_type: Annotated[ServerType, Path(description="Server type")],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    Get servers by type

    Returns a list of servers of the specified type.

    **Server Types**:
    - **PHYSICAL**: Physical server
    - **VIRTUAL**: Virtual machine
    - **CLOUD**: Cloud instance
    - **CONTAINER**: Container host
    """
    builder = QueryBuilder(select(Server), Server).filter(type=server_type)
    builder.sort("name", SortOrder.ASC)

    query = builder.build()
    items, meta = paginate(db, query, page=page, page_size=page_size)

    # Add service count to each server
    for server in items:
        server.service_count = db.query(func.count(Service.id)).filter(
            Service.server_id == server.id
        ).scalar() or 0

    return create_paginated_response(items, meta)
