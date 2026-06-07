"""
utils/entry_store.py
Load / save weekly check-in entries.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from systems.utils.db import db_cursor


def load_entries() -> list[dict]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, project_id, week_label, health_status, note_type, note_text, submitted_at"
            " FROM entries"
        )
        return [dict(row) for row in cur.fetchall()]


def save_entries(entries: list[dict]) -> None:
    with db_cursor() as cur:
        cur.execute("DELETE FROM entries")
        for e in entries:
            cur.execute(
                "INSERT INTO entries"
                " (id, project_id, week_label, health_status, note_type, note_text, submitted_at)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (e["id"], e["project_id"], e["week_label"], e["health_status"],
                 e.get("note_type"), e.get("note_text"), e["submitted_at"]),
            )


def get_entry(project_id: str, week_label: str) -> dict | None:
    for e in load_entries():
        if e["project_id"] == project_id and e["week_label"] == week_label:
            return e
    return None


def get_entries_for_week(week_label: str) -> list[dict]:
    return [e for e in load_entries() if e["week_label"] == week_label]


def upsert_entry(
    project_id: str,
    week_label: str,
    health_status: str,
    note_type: str | None,
    note_text: str | None,
) -> dict:
    entries = load_entries()
    for e in entries:
        if e["project_id"] == project_id and e["week_label"] == week_label:
            e["health_status"] = health_status
            e["note_type"]     = note_type
            e["note_text"]     = note_text
            e["submitted_at"]  = datetime.now().isoformat()
            save_entries(entries)
            return e
    entry: dict = {
        "id":            str(uuid.uuid4()),
        "project_id":    project_id,
        "week_label":    week_label,
        "health_status": health_status,
        "note_type":     note_type,
        "note_text":     note_text,
        "submitted_at":  datetime.now().isoformat(),
    }
    entries.append(entry)
    save_entries(entries)
    return entry


def delete_week_entries(week_label: str) -> int:
    entries = load_entries()
    kept = [e for e in entries if e["week_label"] != week_label]
    removed = len(entries) - len(kept)
    if removed:
        save_entries(kept)
    return removed


def get_all_weeks() -> list[str]:
    entries = load_entries()
    return sorted({e["week_label"] for e in entries}, reverse=True)


def week_bounds(d: date) -> tuple[date, date]:
    days_since_sunday = (d.weekday() + 1) % 7
    sunday   = d - timedelta(days=days_since_sunday)
    thursday = sunday + timedelta(days=4)
    return sunday, thursday


def week_label_from_date(d: date) -> str:
    sunday, thursday = week_bounds(d)
    iso_week = thursday.isocalendar()[1]
    iso_year = thursday.isocalendar()[0]

    if sunday.month == thursday.month:
        date_range = (
            f"{sunday.strftime('%b')} {sunday.day} – {thursday.day}, {thursday.year}"
        )
    else:
        date_range = (
            f"{sunday.strftime('%b')} {sunday.day} – "
            f"{thursday.strftime('%b')} {thursday.day}, {thursday.year}"
        )

    return f"{iso_year}-W{iso_week:02d} – {date_range}"


def current_week_label() -> str:
    return week_label_from_date(date.today())
