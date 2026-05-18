"""
systems/people/utils/employee_store.py
Central employee store — used by all ArkPanel systems that need a people reference.
"""

from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

from systems.utils.github_store import read_json, write_json

_REPO_PATH  = "systems/people/data/employees.json"
_LOCAL_PATH = Path(__file__).parent.parent / "data" / "employees.json"


def load_employees() -> list[dict]:
    return read_json(_REPO_PATH, _LOCAL_PATH, [])


def save_employees(employees: list[dict]) -> None:
    write_json(_REPO_PATH, _LOCAL_PATH, employees, "Update employees")


def get_all_roles() -> list[str]:
    return sorted({e["role"] for e in load_employees() if e.get("role")})


def get_active_employees() -> list[dict]:
    return [e for e in load_employees() if e.get("status") == "Active"]


def add_employee(name: str, email: str, role: str, mobile: str = "") -> dict:
    employees = load_employees()
    emp: dict = {
        "id":         str(uuid.uuid4()),
        "name":       name.strip(),
        "email":      email.strip().lower(),
        "mobile":     mobile.strip(),
        "role":       role.strip(),
        "status":     "Active",
        "created_at": date.today().isoformat(),
    }
    employees.append(emp)
    save_employees(employees)
    return emp


def update_employee(emp_id: str, **kwargs) -> bool:
    employees = load_employees()
    for e in employees:
        if e["id"] == emp_id:
            for k, v in kwargs.items():
                e[k] = v
            save_employees(employees)
            return True
    return False


def delete_employee(emp_id: str) -> bool:
    employees = load_employees()
    filtered = [e for e in employees if e["id"] != emp_id]
    if len(filtered) == len(employees):
        return False
    save_employees(filtered)
    return True
