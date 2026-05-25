"""add Aprobado/Rechazado statuses to documents

Revision ID: d3e4f5a6b7c8
Revises: c9e1f04a7b2d
Create Date: 2026-05-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, Sequence[str], None] = 'c9e1f04a7b2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# SQLite does not support ALTER TABLE ADD/DROP CONSTRAINT.
# The usual workaround (recreate the table) causes data loss: engine.py sets
# PRAGMA foreign_keys = ON on every connection, and SQLAlchemy starts an
# implicit transaction before the migration body runs, making
# "PRAGMA foreign_keys = OFF" a no-op.  As a result, DROP TABLE documents
# cascades into quotes, reports, quote_items, etc.
#
# Instead, we update the CHECK constraint text directly in sqlite_master via
# PRAGMA writable_schema.  This leaves every row, index, trigger, and FK
# relationship untouched — only the constraint definition changes.

_OLD_STATUS_VALUES = "'Borrador', 'Finalizado', 'Enviado'"
_NEW_STATUS_VALUES = "'Borrador', 'Finalizado', 'Enviado', 'Aprobado', 'Rechazado'"


def _patch_constraint(find: str, replace: str) -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA writable_schema = ON"))
    result = conn.execute(
        sa.text(
            "UPDATE sqlite_master "
            "SET sql = REPLACE(sql, :find, :replace) "
            "WHERE type = 'table' AND name = 'documents' AND sql LIKE :like"
        ),
        {"find": find, "replace": replace, "like": f"%{find}%"},
    )
    conn.execute(sa.text("PRAGMA writable_schema = OFF"))
    rows = conn.execute(sa.text("PRAGMA integrity_check")).fetchall()
    if rows[0][0] != "ok":
        raise RuntimeError(f"integrity_check failed after schema patch: {rows}")


def upgrade() -> None:
    _patch_constraint(_OLD_STATUS_VALUES, _NEW_STATUS_VALUES)


def downgrade() -> None:
    # Reset any documents that have already reached the new statuses before
    # tightening the constraint back to the original three values.
    op.execute(
        sa.text("UPDATE documents SET status = 'Enviado' "
                "WHERE status IN ('Aprobado', 'Rechazado')")
    )
    _patch_constraint(_NEW_STATUS_VALUES, _OLD_STATUS_VALUES)
