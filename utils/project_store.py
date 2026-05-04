"""
utils/project_store.py
Load / save project data from data/projects.json.
"""

from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path

DATA_DIR  = Path(__file__).parent.parent / "data"
PROJ_FILE = DATA_DIR / "projects.json"


def _ensure() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not PROJ_FILE.exists():
        PROJ_FILE.write_text("[]", encoding="utf-8")


def load_projects() -> list[dict]:
    _ensure()
    return json.loads(PROJ_FILE.read_text(encoding="utf-8"))


def save_projects(projects: list[dict]) -> None:
    _ensure()
    PROJ_FILE.write_text(
        json.dumps(projects, indent=2, ensure_ascii=False), encoding="utf-8"
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
