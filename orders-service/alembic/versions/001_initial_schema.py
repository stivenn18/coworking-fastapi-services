"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('space_id', sa.Integer(), nullable=False),
        sa.Column('space_name', sa.String(length=255), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('hours', sa.Integer(), nullable=False),
        sa.Column('price_per_hour', sa.Float(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'CONFIRMED', 'CANCELLED', name='orderstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_space_id'), 'orders', ['space_id'], unique=False)
    op.create_index(op.f('ix_orders_user_email'), 'orders', ['user_email'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_orders_user_email'), table_name='orders')
    op.drop_index(op.f('ix_orders_space_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_id'), table_name='orders')
    op.drop_table('orders')
