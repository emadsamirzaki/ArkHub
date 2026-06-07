"""
systems/people/utils/pattern_store.py
Working-pattern store — weekly schedules for each employee.
"""

from __future__ import annotations

import json
from datetime import datetime

import psycopg2.extras

from systems.utils.db import db_cursor

DAYS = ["sunday", "monday", "tuesday", "wednesday", "thursday"]


def load_patterns() -> dict:
    with db_cursor() as cur:
        cur.execute("SELECT employee_id, patterns, updated_at FROM working_patterns")
        result = {}
        for row in cur.fetchall():
            emp_id   = row["employee_id"]
            patterns = row["patterns"]
            if isinstance(patterns, str):
                patterns = json.loads(patterns)
            result[emp_id] = {
                "employee_id": emp_id,
                "patterns":    patterns,
                "updated_at":  row["updated_at"],
            }
        return result


def save_patterns(data: dict) -> None:
    with db_cursor() as cur:
        cur.execute("DELETE FROM working_patterns")
        for emp_id, record in data.items():
            cur.execute(
                "INSERT INTO working_patterns (employee_id, patterns, updated_at) VALUES (%s,%s,%s)",
                (emp_id, psycopg2.extras.Json(record["patterns"]), record["updated_at"]),
            )


def get_pattern(emp_id: str) -> dict | None:
    return load_patterns().get(emp_id)


def upsert_pattern(emp_id: str, patterns: dict) -> None:
    data = load_patterns()
    data[emp_id] = {
        "employee_id": emp_id,
        "patterns":    patterns,
        "updated_at":  datetime.utcnow().isoformat(),
    }
    save_patterns(data)


def delete_pattern(emp_id: str) -> bool:
    data = load_patterns()
    if emp_id not in data:
        return False
    del data[emp_id]
    save_patterns(data)
    return True


def get_status_now(emp_id: str, day: str, time_str: str) -> str:
    """Return 'home' | 'office' | 'away' | 'off' for the given day/time."""
    pat = get_pattern(emp_id)
    if not pat:
        return "off"
    slots = pat.get("patterns", {}).get(day, [])
    for slot in slots:
        if slot["start"] <= time_str < slot["end"]:
            return slot["location"]
    return "off"


def get_next_transition(emp_id: str, day: str, time_str: str) -> tuple[str, str] | None:
    """Return (time_str, new_status) of the next status change after time_str, or None."""
    pat = get_pattern(emp_id)
    if not pat:
        return None
    slots = pat.get("patterns", {}).get(day, [])
    current = get_status_now(emp_id, day, time_str)

    boundaries: list[str] = []
    for slot in slots:
        if slot["start"] > time_str:
            boundaries.append(slot["start"])
        if slot["end"] > time_str:
            boundaries.append(slot["end"])
    if not boundaries:
        return None

    next_time = min(boundaries)
    next_status = get_status_now(emp_id, day, next_time)
    if next_status == current:
        return None
    return next_time, next_status


def to_12h(t: str) -> str:
    """Convert 'HH:MM' (24h) to '8:00 AM' style."""
    h, m = map(int, t.split(":"))
    period = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {period}"


def format_slots(slots: list[dict]) -> str:
    """Format a list of slots into a human-readable string."""
    if not slots:
        return "—"
    parts = []
    for s in slots:
        loc = {"home": "Home", "office": "Office", "away": "Away"}.get(s["location"], s["location"])
        parts.append(f'{to_12h(s["start"])}–{to_12h(s["end"])} {loc}')
    return ",  ".join(parts)


def total_hours(slots: list[dict]) -> float:
    """Sum working hours (excluding 'away' slots) for a day."""
    total = 0.0
    for s in slots:
        if s["location"] == "away":
            continue
        fmt = "%H:%M"
        delta = datetime.strptime(s["end"], fmt) - datetime.strptime(s["start"], fmt)
        total += delta.seconds / 3600
    return round(total, 2)
