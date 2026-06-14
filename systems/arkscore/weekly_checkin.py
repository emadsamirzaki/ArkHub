"""
systems/arkscore/weekly_checkin.py
PM input form — compact table format with saved weeks history.
"""

from __future__ import annotations

from datetime import date as _date, datetime, timedelta

import streamlit as st

from systems.arkscore.utils.entry_store import (
    delete_week_entries,
    get_all_weeks,
    get_entries_for_week,
    get_entry,
    upsert_entry,
    week_label_from_date,
)
from systems.arkscore.utils.project_store import get_active_projects
from systems.utils import ui

STATUS_OPTIONS = ["—", "On Track", "Off Track"]
NOTE_OPTIONS   = ["—", "Note", "Red Flag", "Success Story"]


def _init_for_week(projects: list[dict], week_label: str) -> None:
    # When the week changes, drop the previous week's field state so it doesn't
    # leak across weeks.
    if st.session_state.get("ci_week") != week_label:
        for k in list(st.session_state.keys()):
            if k.startswith(("ci_status_", "ci_note_type_", "ci_note_text_")):
                del st.session_state[k]
        st.session_state["ci_week"] = week_label

    # Populate any field whose widget state is missing from the saved entry.
    # This covers a fresh load, a week switch, AND returning to the page after
    # navigating away (Streamlit garbage-collects widget keys for pages that
    # aren't rendered, while the plain `ci_week` key survives — so we can't rely
    # on the week alone to decide whether the fields need (re)loading). Fields
    # already present are left untouched so in-progress edits survive reruns.
    for p in projects:
        pid = p["id"]
        if f"ci_status_{pid}" in st.session_state:
            continue
        existing = get_entry(pid, week_label)
        if existing:
            saved_status = existing["health_status"]
            st.session_state[f"ci_status_{pid}"]    = saved_status if saved_status in STATUS_OPTIONS else "—"
            st.session_state[f"ci_note_type_{pid}"] = existing.get("note_type") or "—"
            st.session_state[f"ci_note_text_{pid}"] = existing.get("note_text") or ""
        else:
            st.session_state[f"ci_status_{pid}"]    = "—"
            st.session_state[f"ci_note_type_{pid}"] = "—"
            st.session_state[f"ci_note_text_{pid}"] = ""


_SKIPPED = object()  # sentinel: status not set, skip silently

def _save_one(pid: str, week_label: str):
    """Return None on success, _SKIPPED if status is blank, or an error string."""
    status    = st.session_state.get(f"ci_status_{pid}", "—")
    if status == "—":
        return _SKIPPED
    note_type = st.session_state.get(f"ci_note_type_{pid}", "—")
    note_type = note_type if note_type != "—" else None
    note_text = (
        (st.session_state.get(f"ci_note_text_{pid}") or "").strip()
        if note_type else None
    )
    if note_type and not note_text:
        return "Note text required when a note type is selected."
    upsert_entry(pid, week_label, status, note_type or None, note_text or None)
    return None


def main() -> None:
    st.title("✍️ Projects Weekly Check-in")
    st.divider()

    projects = get_active_projects()
    if not projects:
        st.warning(
            "No active projects found. "
            "Add projects in **Project Management** first."
        )
        return

    # ── Week picker ───────────────────────────────────────────────────────────
    col_wk, col_lbl = st.columns([2, 4], vertical_alignment="bottom")
    with col_wk:
        last_week = _date.today() - timedelta(days=7)
        picked = st.date_input(
            "Pick any day in the week",
            value=last_week,
            help="Select any day — the full Sun–Thu week will be used.",
        )
    week_label = week_label_from_date(picked)
    with col_lbl:
        st.markdown(f"**{week_label}**")
    _init_for_week(projects, week_label)

    # ── Check-in table ────────────────────────────────────────────────────────
    ui.section(f"Check-ins for {week_label}")

    th1, th2, th3, th4, th5, th6 = st.columns([2.5, 1.5, 2, 2, 3.5, 0.5])
    th1.markdown("**Project**")
    th2.markdown("**PM**")
    th3.markdown("**Status**")
    th4.markdown("**Note Type**")
    th5.markdown("**Note**")
    th6.markdown("")
    st.divider()

    for p in projects:
        pid       = p["id"]
        has_entry = get_entry(pid, week_label) is not None

        c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1.5, 2, 2, 3.5, 0.5],
                                            vertical_alignment="center")

        c1.markdown(f"**{p['name']}**")
        c2.caption(p["pm"])

        c3.selectbox(
            "status", STATUS_OPTIONS,
            key=f"ci_status_{pid}",
            label_visibility="collapsed",
        )

        c4.selectbox(
            "note type", NOTE_OPTIONS,
            key=f"ci_note_type_{pid}",
            label_visibility="collapsed",
        )

        if st.session_state.get(f"ci_note_type_{pid}", "—") != "—":
            c5.text_input(
                "note",
                key=f"ci_note_text_{pid}",
                max_chars=500,
                label_visibility="collapsed",
                placeholder="Enter note…",
            )

        if has_entry:
            c6.markdown("✅")

    st.markdown("")
    if st.button("💾 Save All", type="primary"):
        errors: list[str] = []
        saved = 0
        for p in projects:
            result = _save_one(p["id"], week_label)
            if result is _SKIPPED:
                pass
            elif result is None:
                saved += 1
            else:
                errors.append(f"**{p['name']}**: {result}")
        for e in errors:
            st.error(e)
        if saved:
            st.success(
                f"✅ {saved} entr{'y' if saved == 1 else 'ies'} saved for {week_label}."
            )
            st.rerun()
        elif not errors:
            st.info("No statuses set — select On Track or Off Track for at least one project.")

    # ── Saved Weeks ───────────────────────────────────────────────────────────
    ui.section("Saved Weeks")

    all_weeks = get_all_weeks()
    if not all_weeks:
        st.info("No check-ins saved yet.")
        return

    n_projects = len(projects)
    sh1, sh2, sh3, sh4 = st.columns([4, 2, 2, 1])
    sh1.markdown("**Week**")
    sh2.markdown("**Last Updated**")
    sh3.markdown("**Entries**")
    sh4.markdown("")
    st.divider()

    for wk in all_weeks:
        entries   = get_entries_for_week(wk)
        n_entries = len(entries)
        latest_at = ""
        if entries:
            latest_raw = max(e.get("submitted_at", "") for e in entries)
            try:
                latest_at = datetime.fromisoformat(latest_raw).strftime("%d %b %Y %H:%M")
            except Exception:
                latest_at = latest_raw

        wc1, wc2, wc3, wc4 = st.columns([4, 2, 2, 1])
        wc1.markdown(wk)
        wc2.markdown(latest_at)
        wc3.markdown(f"{n_entries} / {n_projects} projects")
        if wc4.button("Delete", key=f"del_wk_{wk}", use_container_width=True):
            st.session_state[f"confirm_del_wk_{wk}"] = True

        if st.session_state.get(f"confirm_del_wk_{wk}"):
            st.warning(f"Delete all check-ins for **{wk}**? This cannot be undone.")
            ok_col, cancel_col = st.columns(2)
            if ok_col.button("Yes, delete", key=f"yes_del_wk_{wk}", type="primary"):
                delete_week_entries(wk)
                st.session_state.pop(f"confirm_del_wk_{wk}", None)
                st.success(f"Deleted check-ins for {wk}.")
                st.rerun()
            if cancel_col.button("Cancel", key=f"cancel_del_wk_{wk}"):
                st.session_state.pop(f"confirm_del_wk_{wk}", None)
                st.rerun()


main()
