"""drop_city_from_clients

Revision ID: a1b2c3d4e5f6
Revises: 7f3a9c2d8e1b
Create Date: 2026-05-19 19:58:15.571456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7f3a9c2d8e1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys=OFF"))
    with op.batch_alter_table("clients") as batch_op:
        batch_op.drop_column("city")
    conn.execute(sa.text("PRAGMA foreign_keys=ON"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("PRAGMA foreign_keys=OFF"))
    with op.batch_alter_table("clients") as batch_op:
        batch_op.add_column(sa.Column("city", sa.String(), nullable=True))
    conn.execute(sa.text("PRAGMA foreign_keys=ON"))
