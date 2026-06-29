"""
systems/people/utils/employee_store.py
Central employee store — used by all ArkPanel systems that need a people reference.
"""

from __future__ import annotations

import uuid
from datetime import date

import streamlit as st

from systems.utils.db import db_cursor


@st.cache_data(ttl=60)
def load_employees() -> list[dict]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, name, email, mobile, role, status, clockify_name, created_at FROM employees ORDER BY created_at"
        )
        return [dict(row) for row in cur.fetchall()]


def save_employees(employees: list[dict]) -> None:
    with db_cursor() as cur:
        cur.execute("DELETE FROM employees")
        for e in employees:
            cur.execute(
                "INSERT INTO employees (id, name, email, mobile, role, status, clockify_name, created_at)"
                " VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (e["id"], e["name"], e["email"], e.get("mobile", ""),
                 e["role"], e["status"], e.get("clockify_name", ""), e["created_at"]),
            )
    load_employees.clear()


def get_all_roles() -> list[str]:
    return sorted({e["role"] for e in load_employees() if e.get("role")})


def get_active_employees() -> list[dict]:
    return [e for e in load_employees() if e.get("status") == "Active"]


def add_employee(name: str, email: str, role: str, mobile: str = "", clockify_name: str = "") -> dict:
    employees = load_employees()
    emp: dict = {
        "id":            str(uuid.uuid4()),
        "name":          name.strip(),
        "email":         email.strip().lower(),
        "mobile":        mobile.strip(),
        "role":          role.strip(),
        "status":        "Active",
        "clockify_name": clockify_name.strip(),
        "created_at":    date.today().isoformat(),
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
