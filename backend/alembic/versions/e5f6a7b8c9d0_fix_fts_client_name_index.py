"""Fix FTS client_name index: add clients trigger + rebuild index

Revision ID: e5f6a7b8c9d0
Revises: d3e4f5a6b7c8
Create Date: 2026-05-26

Problem: the fts_documents table was never updated when a client's name or
rut changed (no trigger existed on the clients table). After any autosave
that called ClientRepository.update(), the FTS index retained the old name,
making client-name searches return no results.

Fix:
  1. Add trigger fts_clients_au — fires on clients AFTER UPDATE OF name, rut
     and re-indexes every document belonging to that client.
  2. Rebuild the full FTS index so existing documents get their current
     client name indexed correctly.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None

# Shared section_content expression (used in both the trigger and the rebuild)
_SECTION_CONTENT = """
    CASE d.type
        WHEN 'quote' THEN
            COALESCE((SELECT observations FROM quotes WHERE document_id = d.id), '')
        ELSE
            COALESCE((
                SELECT GROUP_CONCAT(rs.title || ' ' || COALESCE(rs.content, ''), ' ')
                FROM report_sections rs WHERE rs.document_id = d.id
            ), '')
    END
"""


def upgrade() -> None:
    # ── 1. Rebuild the full FTS index with current client names ───────────────
    # Delete all FTS content and re-insert from the canonical tables.
    # This corrects any stale client_name entries caused by the missing trigger.
    op.execute("INSERT INTO fts_documents(fts_documents) VALUES('delete-all')")
    op.execute(f"""
        INSERT INTO fts_documents(rowid, doc_type, doc_number, client_name, client_rut, section_content)
        SELECT d.id, d.type, d.number, c.name, c.rut, {_SECTION_CONTENT}
        FROM documents d
        JOIN clients c ON c.id = d.client_id
    """)

    # ── 2. Add trigger: re-index all documents when a client name/rut changes ─
    op.execute(f"""
        CREATE TRIGGER fts_clients_au
        AFTER UPDATE OF name, rut ON clients
        BEGIN
            INSERT INTO fts_documents(fts_documents, rowid, doc_type, doc_number, client_name, client_rut, section_content)
            SELECT 'delete', d.id, d.type, d.number, OLD.name, OLD.rut, {_SECTION_CONTENT}
            FROM documents d WHERE d.client_id = OLD.id;

            INSERT INTO fts_documents(rowid, doc_type, doc_number, client_name, client_rut, section_content)
            SELECT d.id, d.type, d.number, NEW.name, NEW.rut, {_SECTION_CONTENT}
            FROM documents d WHERE d.client_id = NEW.id;
        END
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS fts_clients_au")
