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
from systems.utils.db import db_cursor

_NEW_ROLE = "✏️  Add new role…"


@st.cache_data(ttl=60)
def _get_clockify_users() -> list[str]:
    """Unique User names seen across all stored Clockify utilization reports."""
    with db_cursor() as cur:
        cur.execute("SELECT raw_rows FROM utilization_reports")
        rows = cur.fetchall()
    users: set[str] = set()
    for row in rows:
        for entry in (row["raw_rows"] or []):
            user = str(entry.get("User") or "").strip()
            if user:
                users.add(user)
    return sorted(users)


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
            _ck_users = _get_clockify_users()
            clockify_name = st.selectbox(
                "Clockify Name",
                options=[""] + _ck_users,
                format_func=lambda x: "— same as Full Name —" if x == "" else x,
                help="Select the name as it appears in Clockify. Leave blank if it matches Full Name exactly.",
                key="add_ck_name",
            )
            submitted = st.form_submit_button("Add Employee", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Full Name is required.")
                elif not email.strip():
                    st.error("Email is required.")
                elif not role.strip():
                    st.error("Role is required.")
                else:
                    add_employee(name, email, role, mobile, clockify_name)
                    st.session_state["emp_add_open"] = False
                    st.success(f"✅ {name.strip()} added.")
                    st.rerun()


def _employee_table() -> None:
    employees = sorted(load_employees(), key=lambda e: e["name"].lower())

    if not employees:
        st.info("No employees yet — add one above.")
        return

    ui.section("All Employees")

    # Column headers
    h0, h1, h2, h3, h4, h5, h6, h7 = st.columns([0.4, 3, 2.5, 2, 2, 1.5, 1, 1])
    h0.markdown("**#**")
    h1.markdown("**Name**")
    h2.markdown("**Email**")
    h3.markdown("**Mobile**")
    h4.markdown("**Role**")
    h5.markdown("**Status**")

    st.divider()

    for i, emp in enumerate(employees):
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
                _ck_users = _get_clockify_users()
                _ck_current = emp.get("clockify_name", "")
                _ck_options = [""] + (
                    _ck_users if _ck_current in ("", *_ck_users)
                    else [_ck_current] + _ck_users
                )
                new_ck = st.selectbox(
                    "Clockify Name",
                    options=_ck_options,
                    index=_ck_options.index(_ck_current) if _ck_current in _ck_options else 0,
                    format_func=lambda x: "— same as Full Name —" if x == "" else x,
                    key=f"eckname_{eid}",
                    help="Select the name as it appears in Clockify. Leave blank to use Full Name.",
                )
                sa, ca = st.columns([1, 5])
                if sa.button("Save", key=f"esave_{eid}", type="primary"):
                    if not new_name.strip() or not new_email.strip() or not new_role.strip():
                        st.error("All fields are required.")
                    else:
                        update_employee(eid, name=new_name.strip(),
                                        email=new_email.strip().lower(),
                                        mobile=new_mobile.strip(),
                                        role=new_role.strip(), status=new_status,
                                        clockify_name=new_ck.strip())
                        st.session_state.pop(f"emp_edit_{eid}", None)
                        st.success("Saved.")
                        st.rerun()
                if ca.button("Cancel", key=f"ecancel_{eid}"):
                    st.session_state.pop(f"emp_edit_{eid}", None)
                    st.rerun()
        else:
            # ── Display row ───────────────────────────────────────────────────
            c0, c1, c2, c3, c4, c5, c6, c7 = st.columns([0.4, 3, 2.5, 2, 2, 1.5, 1, 1],
                                                          vertical_alignment="center")
            badge = (
                ":green-badge[Active]"
                if emp.get("status") == "Active"
                else ":gray-badge[Inactive]"
            )
            c0.caption(str(i + 1))
            c1.markdown(f"**{emp['name']}**")
            if emp.get("clockify_name"):
                c1.caption(f"Clockify: {emp['clockify_name']}")
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


def _clockify_mapping() -> None:
    with st.expander("🔗 Clockify Name Mapping", expanded=False):
        st.caption(
            "Match each employee to their exact name in Clockify. "
            "Leave blank to use the employee's Full Name as the match key."
        )

        employees = load_employees()
        ck_users  = _get_clockify_users()

        if not ck_users:
            st.info(
                "No Clockify reports uploaded yet — go to "
                "**ArkScore → Utilization Check-in** to upload a report first."
            )
            return

        ck_base_options = [""] + ck_users

        h1, h2, h3 = st.columns([3, 4, 1])
        h1.markdown("**Employee**")
        h2.markdown("**Clockify Name**")
        st.divider()

        for emp in employees:
            eid     = emp["id"]
            current = emp.get("clockify_name", "")
            opts    = (
                ck_base_options
                if current in ("", *ck_users)
                else ["", current] + ck_users
            )
            idx = opts.index(current) if current in opts else 0

            c1, c2, c3 = st.columns([3, 4, 1], vertical_alignment="center")
            c1.markdown(f"**{emp['name']}**")
            c1.caption(emp.get("role", ""))

            c2.selectbox(
                "ck",
                options=opts,
                index=idx,
                format_func=lambda x: "— same as Full Name —" if x == "" else x,
                key=f"ckmap_{eid}",
                label_visibility="collapsed",
            )

            if c3.button("Save", key=f"cksave_{eid}", use_container_width=True):
                new_val = st.session_state.get(f"ckmap_{eid}", "")
                update_employee(eid, clockify_name=new_val)
                st.success(f"✅ Saved for **{emp['name']}**.")
                st.rerun()

        st.divider()
        if st.button("💾 Save All", type="primary"):
            for emp in employees:
                new_val = st.session_state.get(f"ckmap_{emp['id']}", emp.get("clockify_name", ""))
                update_employee(emp["id"], clockify_name=new_val)
            st.success(f"✅ Clockify names saved for all {len(employees)} employees.")
            st.rerun()


def main() -> None:
    st.title("👥 Employees")
    st.markdown(
        "Central employee directory — names, emails, and roles used across all ArkPanel systems."
    )
    st.divider()
    _add_form()
    _employee_table()
    _clockify_mapping()


main()
