"""
Pydantic schemas package
®‡ §§»| ÑÏ∏i»‰.
"""

# Common schemas
from app.schemas.common import (
    PaginationParams,
    PaginationMeta,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
    TimestampSchema,
)

# User schemas
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    CurrentUserResponse,
)

# Team schemas
from app.schemas.team import (
    TeamBase,
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamListResponse,
    TeamMemberBase,
    TeamMemberCreate,
    TeamMemberUpdate,
    TeamMemberResponse,
    TeamDetailResponse,
)

# Project schemas
from app.schemas.project import (
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)

# Sprint schemas
from app.schemas.sprint import (
    SprintBase,
    SprintCreate,
    SprintUpdate,
    SprintResponse,
    SprintListResponse,
)

# Issue schemas
from app.schemas.issue import (
    IssueBase,
    IssueCreate,
    IssueUpdate,
    IssueResponse,
    IssueListResponse,
)

# Server schemas
from app.schemas.server import (
    ServerBase,
    ServerCreate,
    ServerUpdate,
    ServerResponse,
    ServerListResponse,
)

# Service schemas
from app.schemas.service import (
    ServiceBase,
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceListResponse,
)

# Deployment schemas
from app.schemas.deployment import (
    DeploymentBase,
    DeploymentCreate,
    DeploymentUpdate,
    DeploymentResponse,
    DeploymentListResponse,
    DeploymentRollbackRequest,
)

__all__ = [
    # Common
    "PaginationParams",
    "PaginationMeta",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    "TimestampSchema",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "CurrentUserResponse",
    # Team
    "TeamBase",
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    "TeamListResponse",
    "TeamMemberBase",
    "TeamMemberCreate",
    "TeamMemberUpdate",
    "TeamMemberResponse",
    "TeamDetailResponse",
    # Project
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    # Sprint
    "SprintBase",
    "SprintCreate",
    "SprintUpdate",
    "SprintResponse",
    "SprintListResponse",
    # Issue
    "IssueBase",
    "IssueCreate",
    "IssueUpdate",
    "IssueResponse",
    "IssueListResponse",
    # Server
    "ServerBase",
    "ServerCreate",
    "ServerUpdate",
    "ServerResponse",
    "ServerListResponse",
    # Service
    "ServiceBase",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    "ServiceListResponse",
    # Deployment
    "DeploymentBase",
    "DeploymentCreate",
    "DeploymentUpdate",
    "DeploymentResponse",
    "DeploymentListResponse",
    "DeploymentRollbackRequest",
]
