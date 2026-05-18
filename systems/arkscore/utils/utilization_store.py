"""
utils/utilization_store.py
Persist weekly Clockify reports as JSON.
Structure: { week_label: { id, week_label, week_start, week_end, uploaded_at, raw_rows } }
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from systems.utils.github_store import read_json, write_json

_REPO_PATH  = "systems/arkscore/data/utilization_reports.json"
_LOCAL_PATH = Path(__file__).parent.parent / "data" / "utilization_reports.json"


def _default(obj):
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _load() -> dict:
    return read_json(_REPO_PATH, _LOCAL_PATH, {})


def _save(data: dict) -> None:
    write_json(_REPO_PATH, _LOCAL_PATH, data, "Update utilization reports", json_default=_default)


def get_all_reports() -> list[dict]:
    data = _load()
    reports = list(data.values())
    reports.sort(key=lambda r: r.get("week_start", ""), reverse=True)
    return reports


def get_all_week_labels() -> list[str]:
    return [r["week_label"] for r in get_all_reports()]


def get_report(week_label: str) -> dict | None:
    return _load().get(week_label)


def upsert_report(
    week_label: str,
    week_start: str,
    week_end: str,
    raw_rows: list[dict],
) -> dict:
    data = _load()
    existing = data.get(week_label, {})
    report: dict = {
        "id":          existing.get("id", str(uuid.uuid4())),
        "week_label":  week_label,
        "week_start":  week_start,
        "week_end":    week_end,
        "uploaded_at": datetime.now().isoformat(),
        "raw_rows":    raw_rows,
    }
    data[week_label] = report
    _save(data)
    return report


def delete_report(week_label: str) -> bool:
    data = _load()
    if week_label in data:
        del data[week_label]
        _save(data)
        return True
    return False


def report_exists(week_label: str) -> bool:
    return week_label in _load()
