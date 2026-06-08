"""
systems/arkscore/weekly_checkin.py
PM input form — submit or update weekly project health check-ins.
"""

from __future__ import annotations

from datetime import date as _date, timedelta

import streamlit as st

from systems.arkscore.utils.entry_store import (
    get_entry,
    upsert_entry,
    week_label_from_date,
)
from systems.arkscore.utils.project_store import get_active_projects

STATUS_OPTIONS = ["On Track", "Off Track"]
NOTE_TYPES     = ["Note", "Red Flag", "Success Story"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important}

.ci-section{
    font-size:.75rem;font-weight:700;color:#94A3B8;
    margin:28px 0 14px;padding-bottom:8px;
    border-bottom:1px solid #334155;
    text-transform:uppercase;letter-spacing:.1em;
}
.ci-proj-title{font-size:1rem;font-weight:700;color:#F1F5F9;margin:0 0 2px;}
.ci-proj-pm   {font-size:.8rem;color:#94A3B8;margin:0;}
</style>
"""


def _init_for_week(projects: list[dict], week_label: str) -> None:
    if st.session_state.get("ci_week") == week_label:
        return
    for k in list(st.session_state.keys()):
        if k.startswith("ci_") and k != "ci_week":
            del st.session_state[k]
    st.session_state["ci_week"] = week_label
    for p in projects:
        pid      = p["id"]
        existing = get_entry(pid, week_label)
        if existing:
            st.session_state[f"ci_status_{pid}"]    = existing["health_status"]
            st.session_state[f"ci_has_note_{pid}"]  = existing.get("note_type") is not None
            st.session_state[f"ci_note_type_{pid}"] = existing.get("note_type") or NOTE_TYPES[0]
            st.session_state[f"ci_note_text_{pid}"] = existing.get("note_text") or ""
        else:
            st.session_state.setdefault(f"ci_has_note_{pid}",  False)
            st.session_state.setdefault(f"ci_note_type_{pid}", NOTE_TYPES[0])
            st.session_state.setdefault(f"ci_note_text_{pid}", "")


def _save_one(pid: str, week_label: str) -> str | None:
    status    = st.session_state.get(f"ci_status_{pid}")
    has_note  = st.session_state.get(f"ci_has_note_{pid}", False)
    note_type = st.session_state.get(f"ci_note_type_{pid}") if has_note else None
    note_text = (
        (st.session_state.get(f"ci_note_text_{pid}") or "").strip() if has_note else None
    )
    if not status:
        return "Health Status is required."
    if has_note and not note_text:
        return "Note text is required when a note type is selected."
    upsert_entry(pid, week_label, status, note_type or None, note_text or None)
    return None


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("# ✍️ Weekly Check-in")
    st.markdown("---")

    projects = get_active_projects()
    if not projects:
        st.warning(
            "No active projects found. "
            "Add projects in **Project Management** first."
        )
        return

    col_wk, col_lbl, _ = st.columns([2, 4, 2])
    with col_wk:
        last_week = _date.today() - timedelta(days=7)
        picked = st.date_input(
            "Pick any day in the week",
            value=last_week,
            help="Select any day — the full Sun–Thu week will be used.",
        )
    week_label = week_label_from_date(picked)
    with col_lbl:
        st.markdown(
            f"<div style='padding-top:28px;font-size:.9rem;font-weight:600;"
            f"color:#94A3B8;'>{week_label}</div>",
            unsafe_allow_html=True,
        )
    _init_for_week(projects, week_label)

    st.markdown(
        f'<p class="ci-section">Check-ins for {week_label}</p>',
        unsafe_allow_html=True,
    )

    for p in projects:
        pid       = p["id"]
        has_entry = get_entry(pid, week_label) is not None
        badge     = "  ✅ Submitted" if has_entry else ""

        with st.container(border=True):
            hdr_l, _ = st.columns([5, 1])
            with hdr_l:
                st.markdown(
                    f'<p class="ci-proj-title">{p["name"]}{badge}</p>'
                    f'<p class="ci-proj-pm">PM: {p["pm"]}</p>',
                    unsafe_allow_html=True,
                )

            current = st.session_state.get(f"ci_status_{pid}")
            idx = STATUS_OPTIONS.index(current) if current in STATUS_OPTIONS else None
            st.radio(
                "Health Status *",
                STATUS_OPTIONS,
                index=idx,
                horizontal=True,
                key=f"ci_status_{pid}",
            )

            st.checkbox("Add a note?", key=f"ci_has_note_{pid}")

            if st.session_state.get(f"ci_has_note_{pid}"):
                nc1, nc2 = st.columns([1.5, 4])
                with nc1:
                    st.selectbox("Note Type", NOTE_TYPES, key=f"ci_note_type_{pid}")
                with nc2:
                    st.text_area(
                        "Note Text *",
                        key=f"ci_note_text_{pid}",
                        max_chars=500,
                        placeholder="Enter note… (max 500 characters)",
                    )

            _, btn_col = st.columns([6, 1])
            with btn_col:
                if st.button("Save", key=f"ci_save_{pid}", type="primary"):
                    err = _save_one(pid, week_label)
                    if err:
                        st.error(err)
                    else:
                        st.success("Saved ✅")
                        st.rerun()

    st.markdown('<p class="ci-section">Save All</p>', unsafe_allow_html=True)
    if st.button("💾 Save All Entries", type="primary"):
        errors: list[str] = []
        saved = 0
        for p in projects:
            err = _save_one(p["id"], week_label)
            if err:
                errors.append(f"**{p['name']}**: {err}")
            else:
                saved += 1
        for e in errors:
            st.error(e)
        if saved:
            st.success(
                f"✅ {saved} entr{'y' if saved == 1 else 'ies'} saved for {week_label}."
            )
            st.rerun()


main()
