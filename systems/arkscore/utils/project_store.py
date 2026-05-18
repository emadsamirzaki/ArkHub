"""
utils/project_store.py
Load / save project data.
"""

from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

from systems.utils.github_store import read_json, write_json

_REPO_PATH  = "systems/arkscore/data/projects.json"
_LOCAL_PATH = Path(__file__).parent.parent / "data" / "projects.json"


def load_projects() -> list[dict]:
    return read_json(_REPO_PATH, _LOCAL_PATH, [])


def save_projects(projects: list[dict]) -> None:
    write_json(_REPO_PATH, _LOCAL_PATH, projects, "Update projects")


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
