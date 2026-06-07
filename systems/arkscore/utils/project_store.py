"""
utils/project_store.py
Load / save project data.
"""

from __future__ import annotations

import uuid
from datetime import date

from systems.utils.db import db_cursor


def load_projects() -> list[dict]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, name, pm, status, created_at FROM projects ORDER BY created_at"
        )
        return [dict(row) for row in cur.fetchall()]


def save_projects(projects: list[dict]) -> None:
    with db_cursor() as cur:
        cur.execute("DELETE FROM projects")
        for p in projects:
            cur.execute(
                "INSERT INTO projects (id, name, pm, status, created_at) VALUES (%s,%s,%s,%s,%s)",
                (p["id"], p["name"], p["pm"], p["status"], p["created_at"]),
            )


def get_active_projects() -> list[dict]:
    return [p for p in load_projects() if p.get("status") == "Active"]


def add_project(name: str, pm: str, status: str = "Active") -> dict:
    projects = load_projects()
    project: dict = {
        "id":         str(uuid.uuid4()),
        "name":       name.strip(),
        "pm":         pm.strip(),
        "status":     status,
        "created_at": date.today().isoformat(),
    }
    projects.append(project)
    save_projects(projects)
    return project


def update_project(project_id: str, **kwargs) -> bool:
    projects = load_projects()
    for p in projects:
        if p["id"] == project_id:
            for k, v in kwargs.items():
                p[k] = v
            save_projects(projects)
            return True
    return False
