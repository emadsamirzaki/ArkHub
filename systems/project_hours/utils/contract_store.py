"""
systems/project_hours/utils/contract_store.py
Persist per-project retainer contracts (period, total hours, monthly burn).

One row per project, keyed by the ArkScore project id.
"""
from __future__ import annotations

import json
from datetime import datetime

import psycopg2.extras
import streamlit as st

from systems.utils.db import db_cursor

_COLUMNS = ("project_id, from_date, to_date, total_hours, monthly_hours, "
            "updated_at, clockify_project_id")


def _row_to_dict(row: dict | None) -> dict | None:
    if not row:
        return None
    r = dict(row)
    if isinstance(r.get("monthly_hours"), str):
        r["monthly_hours"] = json.loads(r["monthly_hours"])
    if r.get("monthly_hours") is None:
        r["monthly_hours"] = {}
    r["total_hours"] = float(r["total_hours"]) if r.get("total_hours") is not None else 0.0
    return r


@st.cache_data(ttl=60)
def get_contract(project_id: str) -> dict | None:
    with db_cursor() as cur:
        cur.execute(
            f"SELECT {_COLUMNS} FROM project_contracts WHERE project_id = %s",
            (project_id,),
        )
        return _row_to_dict(cur.fetchone())


@st.cache_data(ttl=60)
def get_all_contracts() -> list[dict]:
    with db_cursor() as cur:
        cur.execute(f"SELECT {_COLUMNS} FROM project_contracts")
        return [_row_to_dict(row) for row in cur.fetchall()]


def upsert_contract(
    project_id: str,
    from_date: str,
    to_date: str,
    total_hours: float,
    monthly_hours: dict,
    clockify_project_id: str | None = None,
) -> dict:
    """
    Insert or update a contract. `clockify_project_id=None` keeps any existing
    mapping (so saving monthly hours manually never wipes the Clockify link).
    """
    updated_at = datetime.now().isoformat()
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO project_contracts
                (project_id, from_date, to_date, total_hours, monthly_hours,
                 updated_at, clockify_project_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE SET
                from_date           = EXCLUDED.from_date,
                to_date             = EXCLUDED.to_date,
                total_hours         = EXCLUDED.total_hours,
                monthly_hours       = EXCLUDED.monthly_hours,
                updated_at          = EXCLUDED.updated_at,
                clockify_project_id = COALESCE(EXCLUDED.clockify_project_id,
                                               project_contracts.clockify_project_id)
            """,
            (project_id, from_date, to_date, float(total_hours),
             psycopg2.extras.Json(monthly_hours), updated_at, clockify_project_id),
        )
    get_contract.clear()
    get_all_contracts.clear()
    return {
        "project_id":          project_id,
        "from_date":           from_date,
        "to_date":             to_date,
        "total_hours":         float(total_hours),
        "monthly_hours":       monthly_hours,
        "updated_at":          updated_at,
        "clockify_project_id": clockify_project_id,
    }


def delete_contract(project_id: str) -> bool:
    with db_cursor() as cur:
        cur.execute(
            "DELETE FROM project_contracts WHERE project_id = %s RETURNING project_id",
            (project_id,),
        )
        deleted = cur.fetchone() is not None
    if deleted:
        get_contract.clear()
        get_all_contracts.clear()
    return deleted
