"""
utils/utilization_store.py
Persist weekly Clockify reports as JSON.
Structure: { week_label: { id, week_label, week_start, week_end, uploaded_at, raw_rows } }
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path


def _default(obj):
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


DATA_DIR  = Path(__file__).parent.parent / "data"
UTIL_FILE = DATA_DIR / "utilization_reports.json"


def _ensure() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not UTIL_FILE.exists():
        UTIL_FILE.write_text("{}", encoding="utf-8")


def _load() -> dict:
    _ensure()
    return json.loads(UTIL_FILE.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    _ensure()
    UTIL_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=_default), encoding="utf-8"
    )


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
