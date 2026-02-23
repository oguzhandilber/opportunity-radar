"""Add user_profiles table

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-02-23 08:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create user_profiles table."""
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_user_profiles_email'),
    )
    op.create_index(
        op.f('ix_user_profiles_id'),
        'user_profiles',
        ['id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_user_profiles_phone_number'),
        'user_profiles',
        ['phone_number'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema - drop user_profiles table."""
    op.drop_index(op.f('ix_user_profiles_phone_number'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_email'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_id'), table_name='user_profiles')
    op.drop_table('user_profiles')
