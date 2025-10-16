"""add_performance_indexes

Revision ID: f14235f9eab8
Revises: 54312775cac4
Create Date: 2025-10-16 21:34:03.679369

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f14235f9eab8'
down_revision: Union[str, Sequence[str], None] = '54312775cac4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Projects table indexes
    op.create_index('ix_projects_team_id', 'projects', ['team_id'])
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_projects_key', 'projects', ['key'], unique=True)

    # Sprints table indexes
    op.create_index('ix_sprints_project_id', 'sprints', ['project_id'])
    op.create_index('ix_sprints_status', 'sprints', ['status'])
    op.create_index('ix_sprints_dates', 'sprints', ['start_date', 'end_date'])

    # Issues table indexes
    op.create_index('ix_issues_project_id', 'issues', ['project_id'])
    op.create_index('ix_issues_sprint_id', 'issues', ['sprint_id'])
    op.create_index('ix_issues_assignee_id', 'issues', ['assignee_id'])
    op.create_index('ix_issues_creator_id', 'issues', ['creator_id'])
    op.create_index('ix_issues_status', 'issues', ['status'])
    op.create_index('ix_issues_priority', 'issues', ['priority'])
    op.create_index('ix_issues_type', 'issues', ['type'])

    # Team members table indexes
    op.create_index('ix_team_members_team_id', 'team_members', ['team_id'])
    op.create_index('ix_team_members_user_id', 'team_members', ['user_id'])
    op.create_index('ix_team_members_role', 'team_members', ['role'])

    # Servers table indexes
    op.create_index('ix_servers_environment', 'servers', ['environment'])
    op.create_index('ix_servers_type', 'servers', ['type'])
    op.create_index('ix_servers_status', 'servers', ['status'])
    op.create_index('ix_servers_hostname', 'servers', ['hostname'], unique=True)

    # Services table indexes
    op.create_index('ix_services_server_id', 'services', ['server_id'])
    op.create_index('ix_services_type', 'services', ['type'])
    op.create_index('ix_services_status', 'services', ['status'])
    op.create_index('ix_services_name', 'services', ['name'])

    # Deployments table indexes
    op.create_index('ix_deployments_service_id', 'deployments', ['service_id'])
    op.create_index('ix_deployments_environment', 'deployments', ['environment'])
    op.create_index('ix_deployments_status', 'deployments', ['status'])
    op.create_index('ix_deployments_deployed_by', 'deployments', ['deployed_by'])
    # Composite index for getting latest deployment by service
    op.create_index('ix_deployments_service_created', 'deployments', ['service_id', 'created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes in reverse order
    op.drop_index('ix_deployments_service_created', table_name='deployments')
    op.drop_index('ix_deployments_deployed_by', table_name='deployments')
    op.drop_index('ix_deployments_status', table_name='deployments')
    op.drop_index('ix_deployments_environment', table_name='deployments')
    op.drop_index('ix_deployments_service_id', table_name='deployments')

    op.drop_index('ix_services_name', table_name='services')
    op.drop_index('ix_services_status', table_name='services')
    op.drop_index('ix_services_type', table_name='services')
    op.drop_index('ix_services_server_id', table_name='services')

    op.drop_index('ix_servers_hostname', table_name='servers')
    op.drop_index('ix_servers_status', table_name='servers')
    op.drop_index('ix_servers_type', table_name='servers')
    op.drop_index('ix_servers_environment', table_name='servers')

    op.drop_index('ix_team_members_role', table_name='team_members')
    op.drop_index('ix_team_members_user_id', table_name='team_members')
    op.drop_index('ix_team_members_team_id', table_name='team_members')

    op.drop_index('ix_issues_type', table_name='issues')
    op.drop_index('ix_issues_priority', table_name='issues')
    op.drop_index('ix_issues_status', table_name='issues')
    op.drop_index('ix_issues_creator_id', table_name='issues')
    op.drop_index('ix_issues_assignee_id', table_name='issues')
    op.drop_index('ix_issues_sprint_id', table_name='issues')
    op.drop_index('ix_issues_project_id', table_name='issues')

    op.drop_index('ix_sprints_dates', table_name='sprints')
    op.drop_index('ix_sprints_status', table_name='sprints')
    op.drop_index('ix_sprints_project_id', table_name='sprints')

    op.drop_index('ix_projects_key', table_name='projects')
    op.drop_index('ix_projects_status', table_name='projects')
    op.drop_index('ix_projects_team_id', table_name='projects')
