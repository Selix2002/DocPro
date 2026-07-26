# Backend tests

Every test runs against an isolated tmp profile — nothing touches
`~/.docpro/` or your real DB.

## Install

```bash
uv sync --group test
```

The `test` group lives in `backend/pyproject.toml` and stays out of the
production dependency tree.

## Run

From the repo root:

```bash
uv run --package docpro-backend pytest backend/tests
```

With coverage:

```bash
uv run --package docpro-backend pytest backend/tests --cov=docpro_backend
```

Only fast unit tests (skip the DB/Alembic layer):

```bash
uv run --package docpro-backend pytest backend/tests -m "not integration"
```

## Layout

- `conftest.py` — autouse fixture redirects `default_root_dir()` to
  `tmp_path` and resets the `ProfileContext` singleton + engine/session
  caches between tests. `active_profile` factory creates a profile and
  runs Alembic to `head`.
- `unit/` — no DB.
- `integration/` — spins up a real SQLite DB per test.
