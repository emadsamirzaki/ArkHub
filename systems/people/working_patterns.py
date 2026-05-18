"""
systems/people/working_patterns.py
Management page — define weekly working patterns per employee.
"""

from __future__ import annotations

import streamlit as st

from systems.people.utils.employee_store import get_active_employees
from systems.people.utils.pattern_store import (
    DAYS,
    format_slots,
    get_pattern,
    total_hours,
    upsert_pattern,
)


def to_12h(t: str) -> str:
    h, m = map(int, t.split(":"))
    period = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {period}"

DAY_LABELS = {
    "sunday":    "Sunday",
    "monday":    "Monday",
    "tuesday":   "Tuesday",
    "wednesday": "Wednesday",
    "thursday":  "Thursday",
}

LOCATION_OPTIONS = ["home", "office", "away"]
LOCATION_LABELS  = {"home": "🏠 Home", "office": "🏢 Office", "away": "☕ Away / Break"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.section-heading {
    font-size: 0.75rem; font-weight: 700; color: #94A3B8;
    margin: 28px 0 14px 0; padding-bottom: 8px;
    border-bottom: 1px solid #334155;
    text-transform: uppercase; letter-spacing: 0.1em;
}
.day-hours {
    font-size: 0.8rem; color: #64748B; margin-top: 6px;
}
.hours-ok   { color: #86EFAC; }
.hours-warn { color: #FCD34D; }
</style>
"""


def _slot_key(emp_id: str, day: str) -> str:
    return f"wp_slots_{emp_id}_{day}"


def _load_slots_into_state(emp_id: str) -> None:
    """Populate session_state from the store (only if not already set)."""
    pat = get_pattern(emp_id)
    for day in DAYS:
        key = _slot_key(emp_id, day)
        if key not in st.session_state:
            stored = pat["patterns"].get(day, []) if pat else []
            st.session_state[key] = [dict(s) for s in stored]


def _blank_slot() -> dict:
    return {"start": "08:00", "end": "09:00", "location": "home"}


def _time_options() -> list[str]:
    times = []
    for h in range(6, 23):
        for m in (0, 30):
            times.append(f"{h:02d}:{m:02d}")
    times.append("23:00")
    return times


_TIMES = _time_options()


def _render_day_tab(emp_id: str, day: str) -> None:
    key = _slot_key(emp_id, day)
    slots: list[dict] = st.session_state[key]

    if not slots:
        st.caption("No slots yet — click ＋ Add Slot to begin.")

    to_remove = []
    for i, slot in enumerate(slots):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 0.5])

        start_idx = _TIMES.index(slot["start"]) if slot["start"] in _TIMES else 0
        end_idx   = _TIMES.index(slot["end"])   if slot["end"]   in _TIMES else 1

        new_start = c1.selectbox("Start", _TIMES, index=start_idx,
                                 format_func=to_12h,
                                 key=f"{key}_start_{i}", label_visibility="collapsed")
        new_end   = c2.selectbox("End",   _TIMES, index=end_idx,
                                 format_func=to_12h,
                                 key=f"{key}_end_{i}",   label_visibility="collapsed")
        new_loc   = c3.selectbox(
            "Location",
            LOCATION_OPTIONS,
            index=LOCATION_OPTIONS.index(slot["location"]),
            format_func=lambda x: LOCATION_LABELS[x],
            key=f"{key}_loc_{i}",
            label_visibility="collapsed",
        )
        if c4.button("🗑", key=f"{key}_del_{i}", help="Remove slot"):
            to_remove.append(i)
        else:
            slots[i] = {"start": new_start, "end": new_end, "location": new_loc}

    for i in reversed(to_remove):
        slots.pop(i)
    st.session_state[key] = slots

    if st.button("＋ Add Slot", key=f"{key}_add"):
        last_end = slots[-1]["end"] if slots else "08:00"
        # Advance start by 30 min
        idx = _TIMES.index(last_end) if last_end in _TIMES else 0
        new_start = _TIMES[min(idx, len(_TIMES) - 2)]
        new_end   = _TIMES[min(idx + 1, len(_TIMES) - 1)]
        slots.append({"start": new_start, "end": new_end, "location": "home"})
        st.session_state[key] = slots
        st.rerun()

    hrs = total_hours(slots)
    colour = "hours-ok" if hrs >= 7 else "hours-warn"
    st.markdown(
        f'<div class="day-hours">Total working hours: '
        f'<span class="{colour}"><b>{hrs:.1f} h</b></span></div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("# 🗓️ Working Patterns")
    st.markdown("Define each employee's weekly schedule — days, hours, and location per slot.")
    st.markdown("---")

    employees = get_active_employees()
    if not employees:
        st.info("No active employees found. Add employees first via the Employees page.")
        return

    emp_options = {e["name"]: e for e in employees}
    selected_name = st.selectbox("Select employee", list(emp_options.keys()), key="wp_emp_sel")
    emp = emp_options[selected_name]
    emp_id = emp["id"]

    # Reset slot state when employee switches
    if st.session_state.get("wp_last_emp") != emp_id:
        for day in DAYS:
            st.session_state.pop(_slot_key(emp_id, day), None)
        st.session_state["wp_last_emp"] = emp_id

    _load_slots_into_state(emp_id)

    st.markdown(
        f'<p class="section-heading">Weekly Schedule — {emp["name"]} ({emp["role"]})</p>',
        unsafe_allow_html=True,
    )

    tabs = st.tabs([DAY_LABELS[d] for d in DAYS])
    for tab, day in zip(tabs, DAYS):
        with tab:
            _render_day_tab(emp_id, day)

    st.markdown("")
    if st.button("💾  Save Pattern", type="primary", key="wp_save"):
        patterns = {
            day: st.session_state[_slot_key(emp_id, day)]
            for day in DAYS
        }
        upsert_pattern(emp_id, patterns)
        st.success(f"✅ Pattern saved for {emp['name']}.")

    # Preview summary
    with st.expander("📋  Preview saved pattern", expanded=False):
        pat = get_pattern(emp_id)
        if not pat:
            st.caption("No saved pattern yet.")
        else:
            for day in DAYS:
                slots = pat["patterns"].get(day, [])
                st.markdown(f"**{DAY_LABELS[day]}:** {format_slots(slots)}")


main()
