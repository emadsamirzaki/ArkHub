"""
systems/arkscore/operational_health.py
Dashboard view — read-only L10 display for Operational Health.
"""

from __future__ import annotations

import html as _html

import pandas as pd
import streamlit as st

from systems.arkscore.utils.entry_store import delete_week_entries, get_all_weeks, get_entries_for_week
from systems.arkscore.utils.project_store import get_active_projects

ON_TRACK_THRESHOLD = 85.0
NOTE_ICONS = {"Note": "📝", "Red Flag": "🚩", "Success Story": "🏆"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important}

.oh-section{
    font-size:.75rem;font-weight:700;color:#94A3B8;
    margin:28px 0 14px;padding-bottom:8px;
    border-bottom:1px solid #334155;
    text-transform:uppercase;letter-spacing:.1em;
}
.oh-hero{
    text-align:center;padding:36px 24px;border-radius:16px;
    background:#1E293B;border:1px solid #334155;margin-bottom:12px;
}
.oh-score{font-size:4.5rem;font-weight:800;line-height:1;margin:0;}
.oh-label{font-size:1rem;margin:10px 0 4px;}
.oh-count{font-size:.85rem;color:#64748B;margin:0;}
.oh-alert{
    background:#450a0a;border:1px solid #EF4444;border-radius:10px;
    padding:12px 18px;margin-bottom:18px;color:#FCA5A5;
    font-weight:600;font-size:.9rem;
}
.pcard{
    border-radius:12px;padding:16px 18px;margin-bottom:4px;
    border-left:5px solid;min-height:130px;
}
.pcard-on  {border-left-color:#22C55E;background:#0d2017;}
.pcard-off {border-left-color:#EF4444;background:#200d0d;}
.pcard-wait{border-left-color:#475569;background:#1E293B;}
.pcard-title{font-size:.95rem;font-weight:700;color:#F1F5F9;margin:0 0 4px;}
.pcard-pm   {font-size:.78rem;color:#94A3B8;margin:0 0 8px;}
.pcard-status{font-size:.85rem;font-weight:600;margin:0;}
.pcard-note{
    font-size:.78rem;color:#CBD5E1;margin:8px 0 0;
    font-style:italic;border-top:1px solid #334155;padding-top:6px;
}
</style>
"""


def _color(score: float) -> str:
    return "#22C55E" if score >= ON_TRACK_THRESHOLD else "#EF4444"


def _render_hero(score: float, on_count: int, total: int) -> None:
    color = _color(score)
    icon  = "🟢" if score >= ON_TRACK_THRESHOLD else "🔴"
    label = "On Track" if score >= ON_TRACK_THRESHOLD else "Needs Attention"
    st.markdown(
        f"""
<div class="oh-hero">
  <p style="font-size:.7rem;font-weight:700;color:#64748B;text-transform:uppercase;
            letter-spacing:.1em;margin:0 0 14px">Operational Health Score</p>
  <p class="oh-score" style="color:{color};">{score:.0f}%&nbsp;{icon}</p>
  <p class="oh-label" style="color:{color};">{label}</p>
  <p class="oh-count">{on_count} of {total} checked-in projects on track</p>
</div>""",
        unsafe_allow_html=True,
    )
    if score < ON_TRACK_THRESHOLD:
        st.markdown(
            '<div class="oh-alert">⚠️ Below 85 % threshold — action required in this L10 meeting</div>',
            unsafe_allow_html=True,
        )


def _project_card(project: dict, entry: dict | None) -> None:
    name = _html.escape(project["name"])
    pm   = _html.escape(project["pm"])

    if entry is None:
        st.markdown(
            f"""<div class="pcard pcard-wait">
  <p class="pcard-title">⏳ {name}</p>
  <p class="pcard-pm">PM: {pm}</p>
  <p class="pcard-status" style="color:#64748B;">Awaiting check-in</p>
</div>""",
            unsafe_allow_html=True,
        )
        return

    on_track     = entry["health_status"] == "On Track"
    cls          = "pcard-on" if on_track else "pcard-off"
    icon         = "🟢" if on_track else "🔴"
    status_color = "#22C55E" if on_track else "#EF4444"

    note_html = ""
    if entry.get("note_type") and entry.get("note_text"):
        n_icon    = NOTE_ICONS.get(entry["note_type"], "📝")
        note_type = _html.escape(entry["note_type"])
        note_text = _html.escape(entry["note_text"])
        note_html = (
            f'<p class="pcard-note">{n_icon} <strong>{note_type}:</strong> {note_text}</p>'
        )

    st.markdown(
        f"""<div class="pcard {cls}">
  <p class="pcard-title">{icon} {name}</p>
  <p class="pcard-pm">PM: {pm}</p>
  <p class="pcard-status" style="color:{status_color};">{_html.escape(entry['health_status'])}</p>
  {note_html}
</div>""",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("# 📊 Operational Health")
    st.markdown("---")

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

    st.markdown('<p class="oh-section">Project Status</p>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, project in enumerate(projects):
        with cols[i % 3]:
            _project_card(project, entry_by_project.get(project["id"]))

    st.markdown('<p class="oh-section">Summary</p>', unsafe_allow_html=True)

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
