"""
systems/arkscore/project_management.py
Admin view — create, edit, deactivate and reactivate projects.
"""

from __future__ import annotations

import streamlit as st

from systems.arkscore.utils.constants import PM_LIST
from systems.arkscore.utils.project_store import add_project, load_projects, update_project
from systems.utils import ui


def main() -> None:
    st.title("⚙️ Project Management")
    st.divider()

    ui.section("Add New Project")

    with st.form("add_project_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([3, 3, 2])
        with c1:
            new_name = st.text_input("Project Name *")
        with c2:
            new_pm = st.selectbox("PM Name *", PM_LIST)
        with c3:
            new_status = st.radio("Status", ["Active", "Inactive"], horizontal=True, index=0)
        new_retainer = st.checkbox(
            "🔁 Retainer (hours contract)",
            help="Tracked in the Projects Hours Tracking system.",
        )
        submitted = st.form_submit_button("Save Project", type="primary")

    if submitted:
        if not new_name.strip():
            st.error("Project Name is required.")
        else:
            existing_names = [p["name"].lower() for p in load_projects()]
            if new_name.strip().lower() in existing_names:
                st.warning(
                    f'A project named "{new_name.strip()}" already exists. '
                    "Saving anyway — check for duplicates below."
                )
            add_project(new_name.strip(), new_pm.strip(), new_status, new_retainer)
            st.success(f'✅ Project "{new_name.strip()}" added.')
            st.rerun()

    ui.section("All Projects")

    projects = load_projects()
    if not projects:
        st.info("No projects yet. Use the form above to add your first project.")
        return

    h = st.columns([3, 2, 1.5, 1.5, 2.5])
    for col, label in zip(h, ["Project Name", "PM", "Status", "Created", "Actions"]):
        col.markdown(f"**{label}**")
    st.divider()

    edit_id = st.session_state.get("pm_edit_id")

    for p in projects:
        if edit_id == p["id"]:
            with st.form(f"edit_form_{p['id']}"):
                ec1, ec2, ec3 = st.columns([3, 2, 2])
                with ec1:
                    e_name = st.text_input("Name", value=p["name"])
                with ec2:
                    pm_idx = PM_LIST.index(p["pm"]) if p["pm"] in PM_LIST else 0
                    e_pm = st.selectbox("PM", PM_LIST, index=pm_idx)
                with ec3:
                    e_status = st.radio(
                        "Status", ["Active", "Inactive"],
                        index=0 if p["status"] == "Active" else 1,
                        horizontal=True,
                    )
                e_retainer = st.checkbox(
                    "🔁 Retainer (hours contract)",
                    value=p.get("retainer", False),
                    help="Tracked in the Projects Hours Tracking system.",
                )
                sc, cc, _ = st.columns([1, 1, 4])
                with sc:
                    save = st.form_submit_button("💾 Save", type="primary")
                with cc:
                    cancel = st.form_submit_button("✕ Cancel")

            if save:
                if not e_name.strip():
                    st.error("Project Name is required.")
                else:
                    update_project(
                        p["id"], name=e_name.strip(), pm=e_pm.strip(),
                        status=e_status, retainer=e_retainer,
                    )
                    st.session_state.pop("pm_edit_id", None)
                    st.success(f'✅ "{e_name.strip()}" updated.')
                    st.rerun()
            if cancel:
                st.session_state.pop("pm_edit_id", None)
                st.rerun()

        else:
            r = st.columns([3, 2, 1.5, 1.5, 2.5], vertical_alignment="center")
            name_md = f"**{p['name']}**"
            if p.get("retainer"):
                name_md += "　:blue-badge[🔁 Retainer]"
            r[0].markdown(name_md)
            r[1].markdown(p["pm"])
            if p["status"] == "Active":
                r[2].markdown(":green-badge[🟢 Active]")
            else:
                r[2].markdown(":gray-badge[⚫ Inactive]")
            r[3].caption(p.get("created_at", "—"))

            a1, a2, _ = r[4].columns([1, 1.2, 0.3])
            if a1.button("✏️ Edit", key=f"edit_btn_{p['id']}"):
                st.session_state["pm_edit_id"] = p["id"]
                st.rerun()
            if p["status"] == "Active":
                if a2.button("🔒 Deactivate", key=f"deact_{p['id']}"):
                    update_project(p["id"], status="Inactive")
                    st.rerun()
            else:
                if a2.button("🔓 Reactivate", key=f"react_{p['id']}"):
                    update_project(p["id"], status="Active")
                    st.rerun()

        st.divider()


main()
