"""
systems/project_hours/utils/clockify.py
Minimal Clockify REST client for pulling billable hours per month.

Auth: an API key in st.secrets["CLOCKIFY_API_KEY"] (Clockify → Profile Settings
→ API). Workspace is auto-detected from the key's active workspace.

Docs: https://docs.clockify.me/  ·  API  https://api.clockify.me/api/v1
      Reports API  https://reports.api.clockify.me/v1
"""
from __future__ import annotations

import calendar

import requests
import streamlit as st

_API   = "https://api.clockify.me/api/v1"
_REPORTS = "https://reports.api.clockify.me/v1"
_TIMEOUT = 30

# Clockify Reports API returns durations in SECONDS.
_SECONDS_PER_HOUR = 3600.0


class ClockifyError(Exception):
    """Raised for any Clockify configuration or request failure."""


def is_configured() -> bool:
    try:
        return bool(st.secrets.get("CLOCKIFY_API_KEY"))
    except Exception:
        return False


def _api_key() -> str:
    key = ""
    try:
        key = st.secrets.get("CLOCKIFY_API_KEY", "")
    except Exception:
        key = ""
    if not key:
        raise ClockifyError(
            "No Clockify API key found. Add CLOCKIFY_API_KEY to .streamlit/secrets.toml."
        )
    return key


def _headers() -> dict:
    return {"X-Api-Key": _api_key(), "Content-Type": "application/json"}


def _get(url: str, params: dict | None = None):
    try:
        r = requests.get(url, headers=_headers(), params=params, timeout=_TIMEOUT)
    except requests.RequestException as e:
        raise ClockifyError(f"Network error contacting Clockify: {e}") from e
    if r.status_code == 401:
        raise ClockifyError("Clockify rejected the API key (401). Check CLOCKIFY_API_KEY.")
    if not r.ok:
        raise ClockifyError(f"Clockify GET {url} failed ({r.status_code}): {r.text[:200]}")
    return r.json()


def _post(url: str, body: dict):
    try:
        r = requests.post(url, headers=_headers(), json=body, timeout=_TIMEOUT)
    except requests.RequestException as e:
        raise ClockifyError(f"Network error contacting Clockify: {e}") from e
    if r.status_code == 401:
        raise ClockifyError("Clockify rejected the API key (401). Check CLOCKIFY_API_KEY.")
    if not r.ok:
        raise ClockifyError(f"Clockify POST {url} failed ({r.status_code}): {r.text[:200]}")
    return r.json()


@st.cache_data(ttl=300, show_spinner=False)
def get_active_workspace_id() -> str:
    user = _get(f"{_API}/user")
    wid = user.get("activeWorkspace") or user.get("defaultWorkspace")
    if not wid:
        workspaces = _get(f"{_API}/workspaces")
        if workspaces:
            wid = workspaces[0]["id"]
    if not wid:
        raise ClockifyError("Could not determine a Clockify workspace for this key.")
    return wid


@st.cache_data(ttl=300, show_spinner=False)
def list_projects(workspace_id: str) -> list[dict]:
    """All projects in the workspace as [{'id', 'name'}], following pagination."""
    out: list[dict] = []
    page = 1
    while page <= 100:  # safety cap
        batch = _get(
            f"{_API}/workspaces/{workspace_id}/projects",
            params={"page": page, "page-size": 200, "archived": "false"},
        )
        if not batch:
            break
        out.extend({"id": p["id"], "name": p["name"]} for p in batch)
        page += 1
    return out


def match_project(project_name: str, projects: list[dict]) -> str | None:
    """Return the Clockify project id whose name matches (case-insensitive), else None."""
    target = (project_name or "").strip().lower()
    for p in projects:
        if p["name"].strip().lower() == target:
            return p["id"]
    return None


def _month_range_iso(month_key: str) -> tuple[str, str]:
    """'2025-03' -> ('2025-03-01T00:00:00.000Z', '2025-03-31T23:59:59.999Z')."""
    year, month = (int(x) for x in month_key.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    start = f"{year:04d}-{month:02d}-01T00:00:00.000Z"
    end   = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59.999Z"
    return start, end


def _summary_totals(workspace_id: str, project_id: str, start_iso: str, end_iso: str) -> dict:
    """POST a summary report filtered to one project; return the totals[0] dict (or {})."""
    body = {
        "dateRangeStart": start_iso,
        "dateRangeEnd":   end_iso,
        "summaryFilter":  {"groups": ["PROJECT"]},
        "projects":       {"ids": [project_id], "contains": "CONTAINS", "status": "ALL"},
    }
    data = _post(f"{_REPORTS}/workspaces/{workspace_id}/reports/summary", body)
    totals = data.get("totals") or []
    return totals[0] if totals else {}


def monthly_billable_hours(
    workspace_id: str,
    project_id: str,
    month_keys: list[str],
    current_month_key: str,
) -> dict[str, float]:
    """
    Billable hours per month for a project. Months after `current_month_key`
    are skipped (they're zero / not yet logged).
    """
    result: dict[str, float] = {}
    for key in month_keys:
        if key > current_month_key:
            continue
        start, end = _month_range_iso(key)
        totals = _summary_totals(workspace_id, project_id, start, end)
        seconds = float(totals.get("totalBillableTime") or 0)
        result[key] = round(seconds / _SECONDS_PER_HOUR, 2)
    return result
