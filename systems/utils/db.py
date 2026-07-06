"""
systems/utils/db.py
Shared Neon (PostgreSQL) connection for ArkPanel.

Set DATABASE_URL in .streamlit/secrets.toml (local dev) or
Streamlit Cloud's secrets panel (production).
"""
from __future__ import annotations

import threading
import time
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
import streamlit as st

_DDL = """
CREATE TABLE IF NOT EXISTS employees (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL,
    mobile        TEXT NOT NULL DEFAULT '',
    role          TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'Active',
    created_at    TEXT NOT NULL
);

ALTER TABLE employees ADD COLUMN IF NOT EXISTS clockify_name TEXT NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS working_patterns (
    employee_id TEXT PRIMARY KEY,
    patterns    JSONB NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    pm         TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'Active',
    created_at TEXT NOT NULL
);

ALTER TABLE projects ADD COLUMN IF NOT EXISTS retainer BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS entries (
    id            TEXT PRIMARY KEY,
    project_id    TEXT NOT NULL,
    week_label    TEXT NOT NULL,
    health_status TEXT NOT NULL,
    note_type     TEXT,
    note_text     TEXT,
    submitted_at  TEXT NOT NULL,
    UNIQUE (project_id, week_label)
);

CREATE TABLE IF NOT EXISTS utilization_reports (
    id          TEXT PRIMARY KEY,
    week_label  TEXT UNIQUE NOT NULL,
    week_start  TEXT NOT NULL,
    week_end    TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    raw_rows    JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS scorecard_entries (
    id           TEXT PRIMARY KEY,
    week_label   TEXT UNIQUE NOT NULL,
    data         JSONB NOT NULL,
    submitted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_contracts (
    project_id    TEXT PRIMARY KEY,
    from_date     TEXT NOT NULL,
    to_date       TEXT NOT NULL,
    total_hours   NUMERIC NOT NULL,
    monthly_hours JSONB NOT NULL DEFAULT '{}',
    updated_at    TEXT NOT NULL
);

ALTER TABLE project_contracts ADD COLUMN IF NOT EXISTS clockify_project_id TEXT;

ALTER TABLE project_contracts ADD COLUMN IF NOT EXISTS clockify_project_ids JSONB;
ALTER TABLE project_contracts ALTER COLUMN clockify_project_ids DROP NOT NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'project_contracts' AND column_name = 'clockify_project_id'
    ) THEN
        UPDATE project_contracts
        SET clockify_project_ids = jsonb_build_array(clockify_project_id)
        WHERE clockify_project_id IS NOT NULL
          AND (clockify_project_ids IS NULL OR clockify_project_ids = '[]'::jsonb);
        ALTER TABLE project_contracts DROP COLUMN clockify_project_id;
    END IF;
END $$;
"""

_KEEPALIVE_INTERVAL = 240  # 4 minutes — resets Neon's 5-min auto-suspend timer


def _start_keepalive(url: str) -> None:
    """Daemon thread: ping DB every 4 minutes to prevent Neon auto-suspend."""
    def _ping() -> None:
        while True:
            time.sleep(_KEEPALIVE_INTERVAL)
            try:
                conn = psycopg2.connect(url, connect_timeout=10)
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                conn.close()
            except Exception:
                pass  # best-effort; next tick will retry

    t = threading.Thread(target=_ping, daemon=True)
    t.start()


@st.cache_resource
def _init_db() -> str:
    """Connect, create schema if needed, start keep-alive, return URL. Runs once per process."""
    url = st.secrets["DATABASE_URL"]
    conn = psycopg2.connect(url, connect_timeout=15)
    try:
        with conn.cursor() as cur:
            cur.execute(_DDL)
        conn.commit()
    finally:
        conn.close()
    _start_keepalive(url)
    return url


_CONNECT_RETRIES = 2
_CONNECT_RETRY_DELAY = 2.0  # seconds between retries


@contextmanager
def db_cursor(*, dict_cursor: bool = True):
    """Yield a psycopg2 cursor in a transaction. Retries on OperationalError (Neon wakeup)."""
    url = _init_db()
    conn = None
    last_err: Exception | None = None
    for attempt in range(_CONNECT_RETRIES + 1):
        try:
            conn = psycopg2.connect(url, connect_timeout=15)
            break
        except psycopg2.OperationalError as exc:
            last_err = exc
            if attempt < _CONNECT_RETRIES:
                time.sleep(_CONNECT_RETRY_DELAY)
    if conn is None:
        raise last_err  # type: ignore[misc]

    factory = psycopg2.extras.RealDictCursor if dict_cursor else None
    try:
        cur = conn.cursor(cursor_factory=factory)
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
