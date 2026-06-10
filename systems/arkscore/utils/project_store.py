"""
utils/project_store.py
Load / save project data.
"""

from __future__ import annotations

import uuid
from datetime import date

import streamlit as st

from systems.utils.db import db_cursor


@st.cache_data(ttl=60)
def load_projects() -> list[dict]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, name, pm, status, created_at, retainer FROM projects ORDER BY created_at"
        )
        return [dict(row) for row in cur.fetchall()]


def save_projects(projects: list[dict]) -> None:
    with db_cursor() as cur:
        cur.execute("DELETE FROM projects")
        for p in projects:
            cur.execute(
                "INSERT INTO projects (id, name, pm, status, created_at, retainer)"
                " VALUES (%s,%s,%s,%s,%s,%s)",
                (p["id"], p["name"], p["pm"], p["status"], p["created_at"],
                 p.get("retainer", False)),
            )
    load_projects.clear()


def get_active_projects() -> list[dict]:
    return [p for p in load_projects() if p.get("status") == "Active"]


def get_retainer_projects() -> list[dict]:
    return [p for p in load_projects() if p.get("retainer")]


def add_project(name: str, pm: str, status: str = "Active", retainer: bool = False) -> dict:
    projects = load_projects()
    project: dict = {
        "id":         str(uuid.uuid4()),
        "name":       name.strip(),
        "pm":         pm.strip(),
        "status":     status,
        "created_at": date.today().isoformat(),
        "retainer":   retainer,
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
