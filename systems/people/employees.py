"""
systems/people/employees.py
Employee directory — add, edit, deactivate company employees.
"""

from __future__ import annotations

import streamlit as st

from systems.people.utils.employee_store import (
    add_employee,
    delete_employee,
    get_all_roles,
    load_employees,
    update_employee,
)
from systems.utils import ui

_NEW_ROLE = "✏️  Add new role…"


def _role_picker(key: str, current: str = "") -> str:
    """Selectbox of existing roles with a free-text fallback for new ones."""
    roles = get_all_roles()
    options = roles + [_NEW_ROLE]
    default_idx = roles.index(current) if current in roles else len(roles)
    picked = st.selectbox("Role", options, index=default_idx, key=key)
    if picked == _NEW_ROLE:
        return st.text_input("New role name", value="" if current in roles else current,
                             placeholder="e.g. Engineer, PM, Designer",
                             key=key + "_new")
    return picked


def _add_form() -> None:
    with st.expander("➕  Add Employee", expanded=st.session_state.get("emp_add_open", False)):
        with st.form("add_employee_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            name   = c1.text_input("Full Name *")
            email  = c2.text_input("Email *")
            mobile = c3.text_input("Mobile")
            with c4:
                role = _role_picker("add_role")
            submitted = st.form_submit_button("Add Employee", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Full Name is required.")
                elif not email.strip():
                    st.error("Email is required.")
                elif not role.strip():
                    st.error("Role is required.")
                else:
                    add_employee(name, email, role, mobile)
                    st.session_state["emp_add_open"] = False
                    st.success(f"✅ {name.strip()} added.")
                    st.rerun()


def _employee_table() -> None:
    employees = load_employees()

    if not employees:
        st.info("No employees yet — add one above.")
        return

    ui.section("All Employees")

    # Column headers
    h1, h2, h3, h4, h5, h6, h7 = st.columns([3, 2.5, 2, 2, 1.5, 1, 1])
    h1.markdown("**Name**")
    h2.markdown("**Email**")
    h3.markdown("**Mobile**")
    h4.markdown("**Role**")
    h5.markdown("**Status**")

    st.divider()

    for emp in employees:
        eid = emp["id"]

        if st.session_state.get(f"emp_edit_{eid}"):
            # ── Edit row ──────────────────────────────────────────────────────
            with st.container(border=True):
                ec1, ec2, ec3, ec4, ec5 = st.columns([3, 2.5, 2, 2, 1.5])
                new_name   = ec1.text_input("Name",   value=emp["name"],            key=f"ename_{eid}")
                new_email  = ec2.text_input("Email",  value=emp["email"],           key=f"eemail_{eid}")
                new_mobile = ec3.text_input("Mobile", value=emp.get("mobile", ""),  key=f"emobile_{eid}")
                with ec4:
                    new_role = _role_picker(f"erole_{eid}", current=emp["role"])
                new_status = ec5.selectbox("Status",  ["Active", "Inactive"],
                                           index=0 if emp.get("status") == "Active" else 1,
                                           key=f"estatus_{eid}")
                sa, ca = st.columns([1, 5])
                if sa.button("Save", key=f"esave_{eid}", type="primary"):
                    if not new_name.strip() or not new_email.strip() or not new_role.strip():
                        st.error("All fields are required.")
                    else:
                        update_employee(eid, name=new_name.strip(),
                                        email=new_email.strip().lower(),
                                        mobile=new_mobile.strip(),
                                        role=new_role.strip(), status=new_status)
                        st.session_state.pop(f"emp_edit_{eid}", None)
                        st.success("Saved.")
                        st.rerun()
                if ca.button("Cancel", key=f"ecancel_{eid}"):
                    st.session_state.pop(f"emp_edit_{eid}", None)
                    st.rerun()
        else:
            # ── Display row ───────────────────────────────────────────────────
            c1, c2, c3, c4, c5, c6, c7 = st.columns([3, 2.5, 2, 2, 1.5, 1, 1],
                                                    vertical_alignment="center")
            badge = (
                ":green-badge[Active]"
                if emp.get("status") == "Active"
                else ":gray-badge[Inactive]"
            )
            c1.markdown(f"**{emp['name']}**")
            c2.caption(emp["email"])
            c3.caption(emp.get("mobile", "") or "—")
            c4.markdown(emp["role"])
            c5.markdown(badge)

            if c6.button("Edit", key=f"ebtn_{eid}", use_container_width=True):
                st.session_state[f"emp_edit_{eid}"] = True
                st.rerun()

            if c7.button("Delete", key=f"ddel_{eid}", use_container_width=True):
                st.session_state[f"emp_confirm_del_{eid}"] = True
                st.rerun()

        if st.session_state.get(f"emp_confirm_del_{eid}"):
            st.warning(f"Delete **{emp['name']}**? This cannot be undone.")
            ok, cancel, _ = st.columns([1, 1, 6])
            if ok.button("Yes, delete", key=f"eydel_{eid}", type="primary"):
                delete_employee(eid)
                st.session_state.pop(f"emp_confirm_del_{eid}", None)
                st.rerun()
            if cancel.button("Cancel", key=f"ecdel_{eid}"):
                st.session_state.pop(f"emp_confirm_del_{eid}", None)
                st.rerun()


def main() -> None:
    st.title("👥 Employees")
    st.markdown(
        "Central employee directory — names, emails, and roles used across all ArkPanel systems."
    )
    st.divider()
    _add_form()
    _employee_table()


main()
