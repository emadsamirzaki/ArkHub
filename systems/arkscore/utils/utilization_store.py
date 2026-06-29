"""
utils/utilization_store.py
Persist weekly Clockify reports in Neon PostgreSQL.
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import datetime

import psycopg2.extras
import streamlit as st

from systems.utils.db import db_cursor


def _sanitize(obj):
    """Recursively convert raw Clockify row data to JSON-safe Python types."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if hasattr(obj, "item"):  # numpy scalar
        return obj.item()
    if hasattr(obj, "isoformat"):  # datetime
        return obj.isoformat()
    return obj


def _row_to_dict(row: dict) -> dict:
    r = dict(row)
    if isinstance(r["raw_rows"], str):
        r["raw_rows"] = json.loads(r["raw_rows"])
    return r


@st.cache_data(ttl=60)
def get_all_reports() -> list[dict]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, week_label, week_start, week_end, uploaded_at, raw_rows"
            " FROM utilization_reports ORDER BY week_start DESC"
        )
        return [_row_to_dict(row) for row in cur.fetchall()]


def get_all_week_labels() -> list[str]:
    return [r["week_label"] for r in get_all_reports()]


@st.cache_data(ttl=60)
def get_all_clockify_users() -> list[str]:
    """Return sorted unique User names seen across all stored utilization reports."""
    users: set[str] = set()
    for report in get_all_reports():
        for row in report["raw_rows"]:
            user = str(row.get("User") or "").strip()
            if user:
                users.add(user)
    return sorted(users)


@st.cache_data(ttl=60)
def get_report(week_label: str) -> dict | None:
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, week_label, week_start, week_end, uploaded_at, raw_rows"
            " FROM utilization_reports WHERE week_label = %s",
            (week_label,),
        )
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def upsert_report(
    week_label: str,
    week_start: str,
    week_end: str,
    raw_rows: list[dict],
) -> dict:
    safe_rows   = _sanitize(raw_rows)
    uploaded_at = datetime.now().isoformat()
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO utilization_reports (id, week_label, week_start, week_end, uploaded_at, raw_rows)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (week_label) DO UPDATE SET
                week_start  = EXCLUDED.week_start,
                week_end    = EXCLUDED.week_end,
                uploaded_at = EXCLUDED.uploaded_at,
                raw_rows    = EXCLUDED.raw_rows
            RETURNING id
            """,
            (str(uuid.uuid4()), week_label, week_start, week_end,
             uploaded_at, psycopg2.extras.Json(safe_rows)),
        )
        actual_id = cur.fetchone()["id"]
    get_all_reports.clear()
    get_report.clear()
    return {
        "id":          actual_id,
        "week_label":  week_label,
        "week_start":  week_start,
        "week_end":    week_end,
        "uploaded_at": uploaded_at,
        "raw_rows":    safe_rows,
    }


def delete_report(week_label: str) -> bool:
    with db_cursor() as cur:
        cur.execute(
            "DELETE FROM utilization_reports WHERE week_label = %s RETURNING id",
            (week_label,),
        )
        deleted = cur.fetchone() is not None
    if deleted:
        get_all_reports.clear()
        get_report.clear()
    return deleted


def report_exists(week_label: str) -> bool:
    with db_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM utilization_reports WHERE week_label = %s",
            (week_label,),
        )
        return cur.fetchone() is not None
