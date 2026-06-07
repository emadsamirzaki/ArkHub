"""
scripts/migrate_to_db.py
One-time migration: copy existing JSON file data into Neon PostgreSQL.

Run this ONCE after setting up your Neon database and before switching the app to DB mode.

Usage:
    # Option A — environment variable:
    $env:DATABASE_URL = "postgresql://user:pass@ep-xxx.aws.neon.tech/neondb?sslmode=require"
    python scripts/migrate_to_db.py

    # Option B — set DATABASE_URL in .streamlit/secrets.toml, then:
    python scripts/migrate_to_db.py
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras

ROOT = Path(__file__).parent.parent

EMPLOYEES_FILE   = ROOT / "systems" / "people"   / "data" / "employees.json"
PATTERNS_FILE    = ROOT / "systems" / "people"   / "data" / "working_patterns.json"
PROJECTS_FILE    = ROOT / "systems" / "arkscore" / "data" / "projects.json"
ENTRIES_FILE     = ROOT / "systems" / "arkscore" / "data" / "entries.json"
UTILIZATION_FILE = ROOT / "systems" / "arkscore" / "data" / "utilization_reports.json"

DDL = """
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
"""


def _sanitize(obj):
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if hasattr(obj, "item"):
        return obj.item()
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return obj


def _load(path: Path, default):
    if not path.exists():
        print(f"  [skip] {path.name} not found")
        return default
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"  [read] {path.name}")
    return data


def _get_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    secrets_path = ROOT / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        import tomllib
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        url = secrets.get("DATABASE_URL")
        if url:
            return url
    print("ERROR: DATABASE_URL not set.")
    print("  Set it as an env var or add it to .streamlit/secrets.toml")
    sys.exit(1)


def main():
    url = _get_url()
    print("Connecting...")
    conn = psycopg2.connect(url)

    print("Creating tables (IF NOT EXISTS)...")
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()

    # ── Employees ─────────────────────────────────────────────────────────────
    employees = _load(EMPLOYEES_FILE, [])
    if employees:
        print(f"Inserting {len(employees)} employees...")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM employees")
            for e in employees:
                cur.execute(
                    "INSERT INTO employees (id, name, email, mobile, role, status, created_at)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (e["id"], e["name"], e["email"], e.get("mobile", ""),
                     e["role"], e.get("status", "Active"), e["created_at"]),
                )
        conn.commit()

    # ── Working Patterns ──────────────────────────────────────────────────────
    patterns = _load(PATTERNS_FILE, {})
    if patterns:
        print(f"Inserting {len(patterns)} working patterns...")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM working_patterns")
            for emp_id, record in patterns.items():
                cur.execute(
                    "INSERT INTO working_patterns (employee_id, patterns, updated_at)"
                    " VALUES (%s,%s,%s)",
                    (emp_id, psycopg2.extras.Json(record["patterns"]), record["updated_at"]),
                )
        conn.commit()

    # ── Projects ──────────────────────────────────────────────────────────────
    projects = _load(PROJECTS_FILE, [])
    if projects:
        print(f"Inserting {len(projects)} projects...")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM projects")
            for p in projects:
                cur.execute(
                    "INSERT INTO projects (id, name, pm, status, created_at) VALUES (%s,%s,%s,%s,%s)",
                    (p["id"], p["name"], p["pm"], p.get("status", "Active"), p["created_at"]),
                )
        conn.commit()

    # ── Check-in Entries ──────────────────────────────────────────────────────
    entries = _load(ENTRIES_FILE, [])
    if entries:
        print(f"Inserting {len(entries)} check-in entries...")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM entries")
            for e in entries:
                cur.execute(
                    "INSERT INTO entries"
                    " (id, project_id, week_label, health_status, note_type, note_text, submitted_at)"
                    " VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (e["id"], e["project_id"], e["week_label"], e["health_status"],
                     e.get("note_type"), e.get("note_text"), e["submitted_at"]),
                )
        conn.commit()

    # ── Utilization Reports ───────────────────────────────────────────────────
    reports_raw = _load(UTILIZATION_FILE, {})
    if reports_raw:
        report_list = list(reports_raw.values()) if isinstance(reports_raw, dict) else reports_raw
        print(f"Inserting {len(report_list)} utilization reports...")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM utilization_reports")
            for r in report_list:
                safe_rows = _sanitize(r.get("raw_rows", []))
                cur.execute(
                    "INSERT INTO utilization_reports"
                    " (id, week_label, week_start, week_end, uploaded_at, raw_rows)"
                    " VALUES (%s,%s,%s,%s,%s,%s)",
                    (r["id"], r["week_label"], r["week_start"], r["week_end"],
                     r["uploaded_at"], psycopg2.extras.Json(safe_rows)),
                )
        conn.commit()

    # ── Verification ──────────────────────────────────────────────────────────
    print("\nRow counts:")
    with conn.cursor() as cur:
        for table in ["employees", "working_patterns", "projects", "entries", "utilization_reports"]:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"  {table}: {cur.fetchone()[0]}")

    conn.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    main()
