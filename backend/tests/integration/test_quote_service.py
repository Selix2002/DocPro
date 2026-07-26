"""Integration tests for quote_service.

The quote flow is the app's core business: draft → autosave → finalize →
snapshot → approve/reject. These tests walk the whole lifecycle against a
real DB and pin down the pieces most likely to regress silently: total
computation (with the 19% IVA rule), snapshot cadence, and the guarantee
that duplicate re-numbers but preserves everything else.
"""
from __future__ import annotations

import json
from typing import Callable

import pytest
from freezegun import freeze_time

from docpro_backend.dtos import QuoteInput, QuoteItemInput
from docpro_backend.repositories.config.settings import SettingRepository
from docpro_backend.repositories.documents.document_versions import (
    DocumentVersionRepository,
)
from docpro_backend.schema import Client, Document, Quote, QuoteItem
from docpro_backend.services.quote_service import (
    approve_quote,
    create_quote,
    duplicate_quote,
    finalize_quote,
    get_quote,
    reject_quote,
    update_quote,
)


pytestmark = pytest.mark.integration


ClientFactory = Callable[..., Client]


def _input(client_id: int, **overrides) -> QuoteInput:
    """Convenience: a valid QuoteInput with sensible defaults."""
    defaults = dict(
        client_id=client_id,
        number="",
        issue_date="2026-01-15",
        observations=None,
        show_iva=True,
        items=[
            QuoteItemInput(quantity=2, description="Widget", unit_price=1000),
            QuoteItemInput(quantity=1, description="Gadget", unit_price=500),
        ],
    )
    defaults.update(overrides)
    return QuoteInput(**defaults)


# ── create_quote ────────────────────────────────────────────────────────

def test_create_auto_number_uses_default_prefix(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    result = create_quote(session, _input(client.id))

    assert result.number == "COT-0001"


def test_create_custom_number_syncs_counter(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    create_quote(session, _input(client.id, number="COT-0050"))

    assert SettingRepository(session).get("quote_number") == "50"


def test_create_empty_number_string_falls_back_to_auto(
    session, make_client: ClientFactory
) -> None:
    """`number=""` is the frontend's way of saying 'auto-generate', not
    'use empty' — the check is `.strip()`."""
    client = make_client()
    result = create_quote(session, _input(client.id, number="   "))

    assert result.number == "COT-0001"


def test_create_persists_document_quote_and_items(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    result = create_quote(session, _input(client.id))

    doc = session.get(Document, result.document_id)
    quote = session.get(Quote, result.document_id)
    items = (
        session.query(QuoteItem)
        .filter(QuoteItem.document_id == result.document_id)
        .order_by(QuoteItem.position)
        .all()
    )
    assert doc is not None
    assert doc.type == "quote"
    assert doc.status == "Borrador"
    assert quote is not None
    assert quote.show_iva is True
    assert [i.description for i in items] == ["Widget", "Gadget"]


def test_create_computes_totals_with_iva(
    session, make_client: ClientFactory
) -> None:
    """2 * 1000 + 1 * 500 = 2500 neto; 2500 * 0.19 = 475 IVA; total = 2975."""
    client = make_client()
    result = create_quote(session, _input(client.id))

    assert result.neto == 2500.0
    assert result.iva == 475.0
    assert result.total == 2975.0


def test_create_items_have_correct_position_and_subtotal(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    result = create_quote(session, _input(client.id))

    positions = [i.position for i in result.items]
    subtotals = [i.subtotal for i in result.items]
    assert positions == [1, 2]
    assert subtotals == [2000.0, 500.0]


def test_create_without_items_zeroes_totals(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    result = create_quote(session, _input(client.id, items=[]))

    assert (result.neto, result.iva, result.total) == (0.0, 0.0, 0.0)
    assert result.items == ()


def test_create_show_iva_false_persists(
    session, make_client: ClientFactory
) -> None:
    """`show_iva` is a display flag — the IVA is still computed and stored
    on the row, but the template hides it. Confirm the flag survives."""
    client = make_client()
    result = create_quote(session, _input(client.id, show_iva=False))

    assert result.show_iva is False
    stored = session.get(Quote, result.document_id)
    assert stored.show_iva is False


def test_create_saves_initial_snapshot(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    result = create_quote(session, _input(client.id))

    versions = DocumentVersionRepository(session).list_versions(result.document_id)
    assert len(versions) == 1
    assert versions[0].version_num == 1


def test_create_snapshot_json_captures_totals_and_items(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    result = create_quote(session, _input(client.id))
    snap = json.loads(
        DocumentVersionRepository(session)
        .list_versions(result.document_id)[0]
        .snapshot_json
    )

    assert snap["quote"]["neto"] == 2500.0
    assert snap["quote"]["iva"] == 475.0
    assert snap["quote"]["total"] == 2975.0
    assert len(snap["items"]) == 2
    assert snap["items"][0]["subtotal"] == 2000.0


# ── update_quote ────────────────────────────────────────────────────────

def test_update_recalculates_totals(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    created = create_quote(session, _input(client.id))

    updated = update_quote(
        session,
        created.document_id,
        _input(
            client.id,
            items=[QuoteItemInput(quantity=3, description="X", unit_price=100)],
        ),
    )

    assert updated.neto == 300.0
    assert updated.iva == 57.0
    assert updated.total == 357.0


def test_update_replaces_items_completely(
    session, make_client: ClientFactory
) -> None:
    """The service DELETEs old items before inserting new ones — verify no
    orphan rows remain from the original create."""
    client = make_client()
    created = create_quote(session, _input(client.id))

    update_quote(
        session,
        created.document_id,
        _input(
            client.id,
            items=[QuoteItemInput(quantity=1, description="Only", unit_price=99)],
        ),
    )

    items = (
        session.query(QuoteItem)
        .filter(QuoteItem.document_id == created.document_id)
        .all()
    )
    assert [i.description for i in items] == ["Only"]


def test_update_does_not_save_snapshot(
    session, make_client: ClientFactory
) -> None:
    """Autosave calls update_quote on every keystroke — a snapshot per call
    would flood the versions table. Snapshots only happen at create/finalize."""
    client = make_client()
    created = create_quote(session, _input(client.id))

    update_quote(session, created.document_id, _input(client.id))
    update_quote(session, created.document_id, _input(client.id))

    versions = DocumentVersionRepository(session).list_versions(created.document_id)
    assert len(versions) == 1


# ── finalize_quote ──────────────────────────────────────────────────────

def test_finalize_sets_status_and_finalized_at(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    created = create_quote(session, _input(client.id))

    finalized = finalize_quote(session, created.document_id)

    assert finalized.status == "Finalizado"
    assert finalized.finalized_at is not None


def test_finalize_saves_a_second_snapshot(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    created = create_quote(session, _input(client.id))

    finalize_quote(session, created.document_id)

    versions = DocumentVersionRepository(session).list_versions(created.document_id)
    assert [v.version_num for v in versions] == [2, 1]


# ── approve / reject ────────────────────────────────────────────────────

def test_approve_sets_status_and_no_snapshot(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    created = create_quote(session, _input(client.id))

    approved = approve_quote(session, created.document_id)

    assert approved.status == "Aprobado"
    versions = DocumentVersionRepository(session).list_versions(created.document_id)
    assert len(versions) == 1


def test_reject_sets_status_and_no_snapshot(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    created = create_quote(session, _input(client.id))

    rejected = reject_quote(session, created.document_id)

    assert rejected.status == "Rechazado"
    versions = DocumentVersionRepository(session).list_versions(created.document_id)
    assert len(versions) == 1


# ── duplicate_quote ─────────────────────────────────────────────────────

def test_duplicate_creates_new_document_with_new_number(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    source = create_quote(session, _input(client.id))

    clone = duplicate_quote(session, source.document_id)

    assert clone.document_id != source.document_id
    assert clone.number != source.number
    assert clone.number == "COT-0002"


def test_duplicate_preserves_items_client_and_flags(
    session, make_client: ClientFactory
) -> None:
    client = make_client()
    source = create_quote(
        session,
        _input(client.id, observations="notas", show_iva=False),
    )

    clone = duplicate_quote(session, source.document_id)

    assert clone.client_id == source.client_id
    assert clone.observations == "notas"
    assert clone.show_iva is False
    assert [i.description for i in clone.items] == [
        i.description for i in source.items
    ]
    assert clone.total == source.total


@freeze_time("2026-07-25")
def test_duplicate_uses_today_as_issue_date(
    session, make_client: ClientFactory
) -> None:
    """Duplicate resets issue_date to 'today' — the old date is rarely what
    the user wants when copying a quote from a previous month."""
    client = make_client()
    source = create_quote(session, _input(client.id, issue_date="2020-01-01"))

    clone = duplicate_quote(session, source.document_id)

    assert clone.issue_date == "2026-07-25"


# ── get_quote ───────────────────────────────────────────────────────────

def test_get_quote_returns_read_model_with_client_data(
    session, make_client: ClientFactory
) -> None:
    client = make_client(name="ACME", rut="76.111.111-1")
    created = create_quote(session, _input(client.id))

    fetched = get_quote(session, created.document_id)

    assert fetched.document_id == created.document_id
    assert fetched.client_name == "ACME"
    assert fetched.client_rut == "76.111.111-1"
    assert fetched.number == created.number
