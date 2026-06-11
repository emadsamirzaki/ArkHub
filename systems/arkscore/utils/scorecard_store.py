"""
systems/arkscore/utils/scorecard_store.py
Persist weekly L10 scorecard entries.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime

import psycopg2.extras
import streamlit as st

from systems.utils.db import db_cursor


@st.cache_data(ttl=60)
def get_entry(week_label: str) -> dict | None:
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, week_label, data, submitted_at FROM scorecard_entries WHERE week_label = %s",
            (week_label,),
        )
        row = cur.fetchone()
    if not row:
        return None
    r = dict(row)
    if isinstance(r["data"], str):
        r["data"] = json.loads(r["data"])
    return r


def upsert_entry(week_label: str, data: dict) -> dict:
    submitted_at = datetime.now().isoformat()
    entry_id = str(uuid.uuid4())
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO scorecard_entries (id, week_label, data, submitted_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (week_label) DO UPDATE SET
                data         = EXCLUDED.data,
                submitted_at = EXCLUDED.submitted_at
            RETURNING id
            """,
            (entry_id, week_label, psycopg2.extras.Json(data), submitted_at),
        )
        actual_id = cur.fetchone()["id"]
    get_entry.clear()
    get_all_weeks.clear()
    return {"id": actual_id, "week_label": week_label, "data": data, "submitted_at": submitted_at}


@st.cache_data(ttl=60)
def get_all_weeks() -> list[str]:
    with db_cursor() as cur:
        cur.execute("SELECT week_label FROM scorecard_entries ORDER BY week_label DESC")
        return [row["week_label"] for row in cur.fetchall()]


def delete_entry(week_label: str) -> None:
    with db_cursor() as cur:
        cur.execute("DELETE FROM scorecard_entries WHERE week_label = %s", (week_label,))
    get_entry.clear()
    get_all_weeks.clear()
