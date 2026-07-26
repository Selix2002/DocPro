"""Integration tests for number_service.

The service both reads existing document numbers from the DB and writes a
counter into `settings`, so we exercise it against a real migrated DB
rather than mocks — that way we also catch drift between the ORM schema
and what the service expects.
"""
from __future__ import annotations

from typing import Callable

import pytest
from sqlalchemy.orm import Session

from docpro_backend.repositories.config.settings import SettingRepository
from docpro_backend.schema import Document
from docpro_backend.services.number_service import (
    next_number,
    preview_next_number,
    reset_counter,
    sync_counter,
)


pytestmark = pytest.mark.integration


DocFactory = Callable[..., Document]


# ── next_number ────────────────────────────────────────────────────────

def test_next_number_from_empty_uses_default_prefix(session: Session) -> None:
    assert next_number(session, "quote") == "COT-0001"


def test_next_number_uses_custom_prefix(session: Session) -> None:
    SettingRepository(session).set("quote_prefix", "QTE-")
    assert next_number(session, "quote") == "QTE-0001"


def test_next_number_increments_across_calls(session: Session) -> None:
    assert next_number(session, "quote") == "COT-0001"
    assert next_number(session, "quote") == "COT-0002"
    assert next_number(session, "quote") == "COT-0003"


def test_next_number_advances_past_existing_document(
    session: Session, make_document: DocFactory
) -> None:
    """A pre-existing document with a higher tail bumps the counter — the
    counter must never hand out a number that already exists in the DB."""
    make_document(type="quote", number="COT-0050")

    assert next_number(session, "quote") == "COT-0051"


def test_next_number_uses_max_of_db_and_counter(
    session: Session, make_document: DocFactory
) -> None:
    """When the stored counter is ahead of the DB max, it wins."""
    make_document(type="quote", number="COT-0005")
    SettingRepository(session).set("quote_number", "20")

    assert next_number(session, "quote") == "COT-0021"


def test_next_number_report_uses_report_defaults(session: Session) -> None:
    assert next_number(session, "report") == "IT-0001"


def test_next_number_counts_by_type_independently(
    session: Session, make_document: DocFactory
) -> None:
    make_document(type="quote", number="COT-0009")
    make_document(type="report", number="IT-0002")

    assert next_number(session, "quote") == "COT-0010"
    assert next_number(session, "report") == "IT-0003"


def test_next_number_ignores_non_numeric_tail(
    session: Session, make_document: DocFactory
) -> None:
    """Custom numbers without a trailing digit block should not corrupt the
    counter — the service must skip them when scanning the DB max."""
    make_document(type="quote", number="LEGACY-A")

    assert next_number(session, "quote") == "COT-0001"


# ── preview_next_number ────────────────────────────────────────────────

def test_preview_does_not_advance_counter(session: Session) -> None:
    assert preview_next_number(session, "quote") == "COT-0001"
    assert preview_next_number(session, "quote") == "COT-0001"


def test_preview_uses_db_max_when_docs_exist(
    session: Session, make_document: DocFactory
) -> None:
    make_document(type="quote", number="COT-0007")
    assert preview_next_number(session, "quote") == "COT-0008"


def test_preview_falls_back_to_counter_when_no_docs(session: Session) -> None:
    SettingRepository(session).set("quote_number", "15")
    assert preview_next_number(session, "quote") == "COT-0016"


def test_preview_matches_next_when_called_together(session: Session) -> None:
    assert preview_next_number(session, "quote") == next_number(session, "quote")


# ── sync_counter ───────────────────────────────────────────────────────

def test_sync_counter_advances_when_used_is_higher(session: Session) -> None:
    sync_counter(session, "quote", "COT-0100")

    assert SettingRepository(session).get("quote_number") == "100"


def test_sync_counter_ignores_lower(session: Session) -> None:
    SettingRepository(session).set("quote_number", "50")
    sync_counter(session, "quote", "COT-0003")

    assert SettingRepository(session).get("quote_number") == "50"


def test_sync_counter_noop_when_no_digits(session: Session) -> None:
    """A number like 'MANUAL' has no digit tail — must not touch the counter."""
    SettingRepository(session).set("quote_number", "7")
    sync_counter(session, "quote", "MANUAL")

    assert SettingRepository(session).get("quote_number") == "7"


# ── reset_counter ──────────────────────────────────────────────────────

def test_reset_counter_defaults_to_zero(session: Session) -> None:
    SettingRepository(session).set("quote_number", "42")
    reset_counter(session, "quote")

    assert SettingRepository(session).get("quote_number") == "0"


def test_reset_counter_to_custom_value(session: Session) -> None:
    reset_counter(session, "quote", 500)

    assert SettingRepository(session).get("quote_number") == "500"
    assert next_number(session, "quote") == "COT-0501"
