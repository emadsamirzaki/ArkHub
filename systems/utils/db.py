"""
systems/utils/db.py
Shared Neon (PostgreSQL) connection for ArkPanel.

Set DATABASE_URL in .streamlit/secrets.toml (local dev) or
Streamlit Cloud's secrets panel (production).
"""
from __future__ import annotations

from contextlib import contextmanager

import psycopg2
import psycopg2.extras
import streamlit as st

_DDL = """
CREATE TABLE IF NOT EXISTS employees (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL,
    mobile     TEXT NOT NULL DEFAULT '',
    role       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'Active',
    created_at TEXT NOT NULL
);

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
"""


@st.cache_resource
def _init_db() -> str:
    """Connect, create schema if needed, return URL. Runs once per Streamlit process."""
    url = st.secrets["DATABASE_URL"]
    conn = psycopg2.connect(url)
    try:
        with conn.cursor() as cur:
            cur.execute(_DDL)
        conn.commit()
    finally:
        conn.close()
    return url


@contextmanager
def db_cursor(*, dict_cursor: bool = True):
    """Yield a psycopg2 cursor in a transaction. Commits on exit, rolls back on error."""
    conn = psycopg2.connect(_init_db())
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
