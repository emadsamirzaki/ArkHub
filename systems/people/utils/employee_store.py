"""
systems/people/utils/employee_store.py
Central employee store — used by all ArkHub systems that need a people reference.
"""

from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
EMP_FILE = DATA_DIR / "employees.json"


def _ensure() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not EMP_FILE.exists():
        EMP_FILE.write_text("[]", encoding="utf-8")


def load_employees() -> list[dict]:
    _ensure()
    return json.loads(EMP_FILE.read_text(encoding="utf-8"))


def save_employees(employees: list[dict]) -> None:
    _ensure()
    EMP_FILE.write_text(
        json.dumps(employees, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def get_all_roles() -> list[str]:
    return sorted({e["role"] for e in load_employees() if e.get("role")})


def get_active_employees() -> list[dict]:
    return [e for e in load_employees() if e.get("status") == "Active"]


def add_employee(name: str, email: str, role: str) -> dict:
    employees = load_employees()
    emp: dict = {
        "id":         str(uuid.uuid4()),
        "name":       name.strip(),
        "email":      email.strip().lower(),
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
