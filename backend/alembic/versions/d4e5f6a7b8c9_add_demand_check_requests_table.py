"""Add demand_check_requests table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-02-23 12:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create demand_check_requests table."""
    op.create_table(
        'demand_check_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('business_idea', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('demand_score', sa.Float(), nullable=True),
        sa.Column('analysis_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_demand_check_requests_user_id'),
        'demand_check_requests',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_demand_check_requests_created_at'),
        'demand_check_requests',
        ['created_at'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema - drop demand_check_requests table."""
    op.drop_index(op.f('ix_demand_check_requests_created_at'), table_name='demand_check_requests')
    op.drop_index(op.f('ix_demand_check_requests_user_id'), table_name='demand_check_requests')
    op.drop_table('demand_check_requests')
