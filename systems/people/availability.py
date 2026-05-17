"""
systems/people/availability.py
Live availability dashboard — who is working now, from where, and today's timeline.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import streamlit as st

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

from systems.people.utils.employee_store import get_active_employees
from systems.people.utils.pattern_store import (
    DAYS,
    format_slots,
    get_next_transition,
    get_pattern,
    get_status_now,
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

TZ = ZoneInfo("Africa/Cairo")

STATUS_META = {
    "home":    {"label": "🏠 Working from Home",   "bg": "#14532D", "color": "#86EFAC"},
    "office":  {"label": "🏢 In the Office",        "bg": "#1E3A5F", "color": "#93C5FD"},
    "away":    {"label": "☕ Away / Break",          "bg": "#78350F", "color": "#FCD34D"},
    "off":     {"label": "⚫ Not Working",           "bg": "#1E293B", "color": "#64748B"},
}

# Timeline display range
TIMELINE_START_H = 7
TIMELINE_END_H   = 20

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
.now-card {
    border-radius: 12px; padding: 16px 20px; margin-bottom: 10px;
    border: 1px solid #334155;
}
.now-card-name  { font-weight: 700; font-size: 1rem; color: #F1F5F9; }
.now-card-role  { font-size: 0.8rem; color: #94A3B8; margin-top: 2px; }
.now-card-status{ font-size: 0.85rem; font-weight: 600; margin-top: 10px; }
.next-row { background:#1E293B; border-radius:8px; padding:10px 14px; margin-bottom:6px; font-size:0.88rem; color:#CBD5E1; }
.next-time { color:#60A5FA; font-weight:700; }
.tl-wrap  { margin-bottom: 6px; }
.tl-label { font-size: 0.78rem; color: #94A3B8; width: 140px; display: inline-block; vertical-align: middle; }
.tl-bar   { display: inline-block; vertical-align: middle; position: relative;
            height: 20px; background: #1E293B; border-radius: 4px; overflow: hidden;
            width: calc(100% - 150px); }
.tl-now-marker { position: absolute; top: 0; bottom: 0; width: 2px; background: #F472B6; z-index: 10; }
</style>
"""


def _now() -> datetime:
    return datetime.now(TZ)


def _time_str(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def _weekday_name(dt: datetime) -> str:
    names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    return names[dt.weekday()]


def _pct(time_str: str) -> float:
    h, m = map(int, time_str.split(":"))
    minutes = h * 60 + m
    start_m = TIMELINE_START_H * 60
    end_m   = TIMELINE_END_H   * 60
    return max(0.0, min(100.0, (minutes - start_m) / (end_m - start_m) * 100))


LOC_COLORS = {"home": "#14532D", "office": "#1E3A5F", "away": "#78350F"}


def _timeline_html(slots: list[dict], now_pct: float | None) -> str:
    bar_blocks = ""
    for s in slots:
        left  = _pct(s["start"])
        right = _pct(s["end"])
        width = right - left
        if width <= 0:
            continue
        color = LOC_COLORS.get(s["location"], "#334155")
        bar_blocks += (
            f'<div style="position:absolute;left:{left:.2f}%;width:{width:.2f}%;'
            f'top:0;bottom:0;background:{color};"></div>'
        )
    marker = ""
    if now_pct is not None and 0 <= now_pct <= 100:
        marker = f'<div class="tl-now-marker" style="left:{now_pct:.2f}%"></div>'

    return (
        f'<div class="tl-bar">'
        f'{bar_blocks}{marker}'
        f'</div>'
    )


def _section_now(employees: list[dict], day: str, time_str: str) -> None:
    st.markdown('<p class="section-heading">Right Now</p>', unsafe_allow_html=True)

    cols = st.columns(4)
    for i, emp in enumerate(employees):
        status = get_status_now(emp["id"], day, time_str)
        meta   = STATUS_META[status]
        with cols[i % 4]:
            st.markdown(
                f'<div class="now-card" style="background:{meta["bg"]};">'
                f'<div class="now-card-name">{emp["name"]}</div>'
                f'<div class="now-card-role">{emp["role"]}</div>'
                f'<div class="now-card-status" style="color:{meta["color"]};">'
                f'{meta["label"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _section_next_hour(employees: list[dict], day: str, now: datetime) -> None:
    time_str     = _time_str(now)
    future_str   = _time_str(now + timedelta(hours=1))
    changes      = []

    for emp in employees:
        trans = get_next_transition(emp["id"], day, time_str)
        if trans and trans[0] <= future_str:
            at_time, new_status = trans
            current = get_status_now(emp["id"], day, time_str)
            if current == "off" and new_status != "off":
                verb = "Starting"
            elif current != "off" and new_status == "off":
                verb = "Finishing"
            else:
                verb = "Switching to"
            changes.append((at_time, emp["name"], verb, new_status))

    if not changes:
        return

    changes.sort()
    st.markdown('<p class="section-heading">Changes in the Next Hour</p>', unsafe_allow_html=True)
    for at_time, name, verb, new_status in changes:
        meta  = STATUS_META[new_status]
        label = meta["label"]
        st.markdown(
            f'<div class="next-row">'
            f'<b>{name}</b> — {verb} <span style="color:{meta["color"]};">{label}</span> '
            f'at <span class="next-time">{to_12h(at_time)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _section_timeline(employees: list[dict], day: str, now: datetime) -> None:
    st.markdown('<p class="section-heading">Today\'s Timeline</p>', unsafe_allow_html=True)

    now_pct = _pct(_time_str(now))
    hour_labels = "  ".join(
        to_12h(f"{h:02d}:00") for h in range(TIMELINE_START_H, TIMELINE_END_H + 1, 2)
    )
    st.caption(f"← {hour_labels} →   (pink line = now)")

    for emp in employees:
        pat   = get_pattern(emp["id"])
        slots = pat["patterns"].get(day, []) if pat else []
        tl    = _timeline_html(slots, now_pct)
        st.markdown(
            f'<div class="tl-wrap">'
            f'<span class="tl-label">{emp["name"]}</span>'
            f'{tl}'
            f'</div>',
            unsafe_allow_html=True,
        )


def _section_employee_details(employees: list[dict]) -> None:
    st.markdown('<p class="section-heading">Employee Schedules</p>', unsafe_allow_html=True)
    for emp in employees:
        pat = get_pattern(emp["id"])
        with st.expander(f"{emp['name']} — {emp['role']}"):
            if not pat:
                st.caption("No working pattern set yet.")
            else:
                for day in DAYS:
                    slots = pat["patterns"].get(day, [])
                    st.markdown(f"**{DAY_LABELS[day]}:** {format_slots(slots)}")


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

    now     = _now()
    day     = _weekday_name(now)
    time_str = _time_str(now)
    is_workday = day in DAYS

    st.markdown("# 📍 Availability Now")
    day_display = DAY_LABELS.get(day, day.capitalize())
    st.markdown(
        f"**{day_display}** · {now.strftime('%d %b %Y')} · "
        f"<span style='color:#60A5FA;font-weight:700;'>{to_12h(time_str)}</span> Cairo time",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    employees = get_active_employees()
    if not employees:
        st.info("No active employees. Add employees via the Employees page.")
        return

    if not is_workday:
        st.warning(f"Today is {day_display} — outside the work week (Sun–Thu). Showing schedules below.")
        _section_employee_details(employees)
        return

    _section_now(employees, day, time_str)
    st.markdown("")
    _section_next_hour(employees, day, now)
    st.markdown("")
    _section_timeline(employees, day, now)
    st.markdown("")
    _section_employee_details(employees)


main()
