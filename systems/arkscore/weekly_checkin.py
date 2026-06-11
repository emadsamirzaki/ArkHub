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

STATUS_OPTIONS = ["—", "On Track", "Off Track"]
NOTE_OPTIONS   = ["—", "Note", "Red Flag", "Success Story"]

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
.ci-th{
    font-size:.7rem;font-weight:700;color:#64748B;
    text-transform:uppercase;letter-spacing:.08em;
    padding-bottom:4px;
}
.ci-proj-name{font-size:.9rem;font-weight:600;color:#F1F5F9;line-height:1.8;}
.ci-proj-pm  {font-size:.75rem;color:#64748B;padding-top:10px;}
.ci-submitted{font-size:.9rem;color:#22C55E;padding-top:8px;}
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
            saved_status = existing["health_status"]
            st.session_state[f"ci_status_{pid}"]    = saved_status if saved_status in STATUS_OPTIONS else "—"
            nt = existing.get("note_type")
            st.session_state[f"ci_note_type_{pid}"] = nt if nt else "—"
            st.session_state[f"ci_note_text_{pid}"] = existing.get("note_text") or ""
        else:
            st.session_state.setdefault(f"ci_status_{pid}",    "—")
            st.session_state.setdefault(f"ci_note_type_{pid}", "—")
            st.session_state.setdefault(f"ci_note_text_{pid}", "")


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
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("# ✍️ Projects Weekly Check-in")
    st.markdown("---")

    projects = get_active_projects()
    if not projects:
        st.warning(
            "No active projects found. "
            "Add projects in **Project Management** first."
        )
        return

    # ── Week picker ───────────────────────────────────────────────────────────
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

    # ── Check-in table ────────────────────────────────────────────────────────
    st.markdown(
        f'<p class="ci-section">Check-ins for {week_label}</p>',
        unsafe_allow_html=True,
    )

    th1, th2, th3, th4, th5, th6 = st.columns([2.5, 1.5, 2, 2, 3.5, 0.5])
    th1.markdown('<div class="ci-th">Project</div>',   unsafe_allow_html=True)
    th2.markdown('<div class="ci-th">PM</div>',        unsafe_allow_html=True)
    th3.markdown('<div class="ci-th">Status</div>',    unsafe_allow_html=True)
    th4.markdown('<div class="ci-th">Note Type</div>', unsafe_allow_html=True)
    th5.markdown('<div class="ci-th">Note</div>',      unsafe_allow_html=True)
    th6.markdown("")
    st.markdown(
        "<hr style='margin:2px 0 10px 0;border-color:#334155'>",
        unsafe_allow_html=True,
    )

    for p in projects:
        pid       = p["id"]
        has_entry = get_entry(pid, week_label) is not None

        c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1.5, 2, 2, 3.5, 0.5])

        c1.markdown(
            f'<div class="ci-proj-name">{p["name"]}</div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<div class="ci-proj-pm">{p["pm"]}</div>',
            unsafe_allow_html=True,
        )

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
            c6.markdown(
                '<div class="ci-submitted">✅</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
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
    st.markdown('<p class="ci-section">Saved Weeks</p>', unsafe_allow_html=True)

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
    st.markdown(
        "<hr style='margin:4px 0 8px 0;border-color:#334155'>",
        unsafe_allow_html=True,
    )

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
