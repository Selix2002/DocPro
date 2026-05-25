"""add usage_count to section_templates

Revision ID: 7f3a9c2d8e1b
Revises: baa89440b9ab
Create Date: 2026-05-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7f3a9c2d8e1b'
down_revision: Union[str, Sequence[str], None] = 'baa89440b9ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'section_templates',
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_column('section_templates', 'usage_count')
