"""Add call_history table

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-02-23 13:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create call_history table."""
    op.create_table(
        'call_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('demand_check_id', sa.Integer(), nullable=True),
        sa.Column('elevenlabs_call_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['demand_check_id'], ['demand_check_requests.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_call_history_id'),
        'call_history',
        ['id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_call_history_user_id'),
        'call_history',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_call_history_demand_check_id'),
        'call_history',
        ['demand_check_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_call_history_elevenlabs_call_id'),
        'call_history',
        ['elevenlabs_call_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_call_history_created_at'),
        'call_history',
        ['created_at'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema - drop call_history table."""
    op.drop_index(op.f('ix_call_history_created_at'), table_name='call_history')
    op.drop_index(op.f('ix_call_history_elevenlabs_call_id'), table_name='call_history')
    op.drop_index(op.f('ix_call_history_demand_check_id'), table_name='call_history')
    op.drop_index(op.f('ix_call_history_user_id'), table_name='call_history')
    op.drop_index(op.f('ix_call_history_id'), table_name='call_history')
    op.drop_table('call_history')
