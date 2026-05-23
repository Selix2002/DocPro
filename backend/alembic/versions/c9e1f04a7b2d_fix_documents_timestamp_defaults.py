"""fix documents timestamp literal defaults

Revision ID: c9e1f04a7b2d
Revises: a1b2c3d4e5f6
Create Date: 2026-05-21

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'c9e1f04a7b2d'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default='CURRENT_TIMESTAMP' (string) produced DEFAULT 'CURRENT_TIMESTAMP'
    # in SQLite DDL — a string literal, not the timestamp function.  Rows inserted
    # by the app received the literal text instead of an actual datetime.
    # Reset those rows to the current time so relative-time labels work correctly.
    op.execute("""
        UPDATE documents
        SET created_at = strftime('%Y-%m-%d %H:%M:%S', 'now'),
            updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now')
        WHERE created_at = 'CURRENT_TIMESTAMP'
    """)


def downgrade() -> None:
    pass
