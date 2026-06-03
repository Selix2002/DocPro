"""add show_iva to quotes

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
Create Date: 2026-06-03
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "quotes",
        sa.Column("show_iva", sa.Boolean(), server_default="1", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("quotes", "show_iva")
