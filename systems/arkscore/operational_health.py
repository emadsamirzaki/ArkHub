"""
systems/arkscore/operational_health.py
Dashboard view — read-only L10 display for Operational Health.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from systems.arkscore.utils.entry_store import delete_week_entries, get_all_weeks, get_entries_for_week
from systems.arkscore.utils.project_store import get_active_projects
from systems.utils import ui

ON_TRACK_THRESHOLD = 85.0
NOTE_ICONS = {"Note": "📝", "Red Flag": "🚩", "Success Story": "🏆"}


def _render_hero(score: float, on_count: int, total: int) -> None:
    on_track = score >= ON_TRACK_THRESHOLD
    with st.container(border=True):
        c1, c2 = st.columns([1, 2], vertical_alignment="center")
        with c1:
            st.metric("Operational Health Score", f"{score:.0f}%")
        with c2:
            if on_track:
                st.markdown("### :green[🟢 On Track]")
            else:
                st.markdown("### :red[🔴 Needs Attention]")
            st.caption(f"{on_count} of {total} checked-in projects on track")
    if not on_track:
        st.error("⚠️ Below 85% threshold — action required in this L10 meeting")


def _project_card(project: dict, entry: dict | None) -> None:
    name = project["name"]
    pm   = project["pm"]

    with st.container(border=True):
        if entry is None:
            st.markdown(f"**⏳ {name}**")
            st.caption(f"PM: {pm}")
            st.markdown(":gray-badge[Awaiting check-in]")
            return

        st.markdown(f"**{name}**")
        st.caption(f"PM: {pm}")
        st.markdown(ui.status_badge(entry["health_status"]))

        if entry.get("note_type") and entry.get("note_text"):
            n_icon = NOTE_ICONS.get(entry["note_type"], "📝")
            st.caption(f"{n_icon} **{entry['note_type']}:** {entry['note_text']}")


def main() -> None:
    st.title("📊 Operational Health")
    st.divider()

    projects  = get_active_projects()
    all_weeks = get_all_weeks()

    if not all_weeks:
        st.info(
            "No check-ins have been submitted yet.\n\n"
            "Go to **Weekly Check-in** to submit entries, "
            "then return here for the dashboard."
        )
        if not projects:
            st.warning("You also have no active projects. Add them in **Project Management**.")
        return

    col_sel, col_del, _ = st.columns([2, 1, 4])
    with col_sel:
        week_label = st.selectbox("Select Week", all_weeks, index=0)
    with col_del:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("🗑️ Delete Week", type="secondary"):
            st.session_state["_oh_confirm_delete"] = week_label

    if st.session_state.get("_oh_confirm_delete") == week_label:
        st.warning(
            f"Delete **all check-in entries** for **{week_label}**? This cannot be undone.",
            icon="⚠️",
        )
        c1, c2, *_ = st.columns([1, 1, 6])
        with c1:
            if st.button("Yes, delete", type="primary"):
                removed = delete_week_entries(week_label)
                st.session_state.pop("_oh_confirm_delete", None)
                st.success(f"Deleted {removed} entries for {week_label}.")
                st.rerun()
        with c2:
            if st.button("Cancel"):
                st.session_state.pop("_oh_confirm_delete", None)
                st.rerun()

    entries_this_week = get_entries_for_week(week_label)
    entry_by_project  = {e["project_id"]: e for e in entries_this_week}

    projects_with_entries = [p for p in projects if p["id"] in entry_by_project]
    on_track_count = sum(
        1 for p in projects_with_entries
        if entry_by_project[p["id"]]["health_status"] == "On Track"
    )
    total_checked = len(projects_with_entries)
    score = (on_track_count / total_checked * 100) if total_checked else 0.0

    if total_checked == 0:
        st.warning(f"No check-ins found for **{week_label}**.")
    else:
        _render_hero(score, on_track_count, total_checked)

    if not projects:
        st.warning("No active projects. Add them in **Project Management**.")
        return

    ui.section("Project Status")
    cols = st.columns(3)
    for i, project in enumerate(projects):
        with cols[i % 3]:
            _project_card(project, entry_by_project.get(project["id"]))

    ui.section("Summary")

    rows = []
    for p in projects:
        e = entry_by_project.get(p["id"])
        note_preview = ""
        if e and e.get("note_text"):
            t = e["note_text"]
            note_preview = t[:80] + ("…" if len(t) > 80 else "")
        rows.append({
            "Project":      p["name"],
            "PM":           p["pm"],
            "Status":       e["health_status"] if e else "⏳ Awaiting",
            "Note Type":    e.get("note_type") or "—" if e else "—",
            "Note Preview": note_preview or "—",
        })

    order = {"Off Track": 0, "On Track": 1, "⏳ Awaiting": 2}
    rows.sort(key=lambda r: (order.get(r["Status"], 3), r["Project"].lower()))
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


main()
