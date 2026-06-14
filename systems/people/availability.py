"""
systems/people/availability.py
Live availability dashboard — Google Calendar-style day view + right-now status.
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
from systems.utils import ui


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

# Each status maps to a Streamlit semantic badge colour (flips with the theme).
STATUS_META = {
    "home":   {"label": "🏠 Working from Home", "badge": "green"},
    "office": {"label": "🏢 In the Office",      "badge": "blue"},
    "away":   {"label": "☕ Away / Break",        "badge": "orange"},
    "off":    {"label": "⚫ Not Working",         "badge": "gray"},
}

# Calendar display range
CAL_START_H = 6
CAL_END_H   = 23

HOUR_H  = 60    # px per hour
GUTTER  = 56    # px — time-label column
COL_W   = 150   # px — per employee column

# Event-chip colours (self-contained bg+fg blocks — legible on light and dark).
_LOC = {
    "home":   ("🏠 Home",   "#15803D", "#22C55E", "#ECFDF5"),
    "office": ("🏢 Office", "#1D4ED8", "#3B82F6", "#EFF6FF"),
    "away":   ("☕ Away",   "#B45309", "#F59E0B", "#FFFBEB"),
}

# Theme-neutral chrome for the custom calendar: transparent surfaces + translucent
# gridlines so the panel adopts whichever background (light/dark) is active.
CAL_BORDER = "rgba(128,128,128,0.28)"
GRID_HOUR  = "rgba(128,128,128,0.22)"
GRID_HALF  = "rgba(128,128,128,0.11)"
HOUR_LABEL = "#6B7280"
ROLE_LABEL = "#6B7280"
NOW_COLOR  = "#EF4444"


def _now() -> datetime:
    return datetime.now(TZ)


def _time_str(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def _weekday_name(dt: datetime) -> str:
    names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    return names[dt.weekday()]


def _to_min(t: str) -> int:
    h, m = map(int, t.split(":"))
    return h * 60 + m


# ── Working-pattern dialog ────────────────────────────────────────────────────

@st.dialog("Working Pattern")
def _pattern_dialog(emp: dict) -> None:
    pat = get_pattern(emp["id"])
    st.markdown(f"**{emp['name']}** — {emp['role']}")
    parts = []
    if emp.get("email"):
        parts.append(f'✉️ {emp["email"]}')
    if emp.get("mobile"):
        parts.append(f'📱 {emp["mobile"]}')
    if parts:
        st.caption("　|　".join(parts))
    st.divider()
    if not pat:
        st.info("No working pattern set yet.")
        return
    for d in DAYS:
        slots = pat["patterns"].get(d, [])
        st.markdown(f"**{DAY_LABELS[d]}:** {format_slots(slots) if slots else '*Off*'}")


# ── Google Calendar-style day view ────────────────────────────────────────────

def _section_calendar_day(employees: list[dict], day: str, now: datetime) -> None:
    cal_s  = CAL_START_H * 60
    cal_e  = CAL_END_H   * 60
    n_h    = CAL_END_H - CAL_START_H
    body_h = n_h * HOUR_H

    now_min = now.hour * 60 + now.minute
    now_top: float | None = (
        (now_min - cal_s) / 60 * HOUR_H if cal_s <= now_min <= cal_e else None
    )

    # ── Column headers (name colour omitted → inherits theme text, so it flips) ─
    col_heads = "".join(
        f'<div style="width:{COL_W}px;flex-shrink:0;padding:10px 6px 8px;'
        f'text-align:center;border-right:1px solid {CAL_BORDER};box-sizing:border-box;">'
        f'<div style="font-size:0.82rem;font-weight:700;'
        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{emp["name"]}</div>'
        f'<div style="font-size:0.7rem;color:{ROLE_LABEL};margin-top:1px;">{emp["role"]}</div>'
        f'</div>'
        for emp in employees
    )
    header = (
        f'<div style="display:flex;border-bottom:2px solid {CAL_BORDER};'
        f'position:sticky;top:0;z-index:10;backdrop-filter:blur(2px);">'
        f'<div style="width:{GUTTER}px;flex-shrink:0;border-right:1px solid {CAL_BORDER};"></div>'
        f'{col_heads}'
        f'</div>'
    )

    # ── Time-label gutter ─────────────────────────────────────────────────────
    hour_labels = "".join(
        f'<div style="position:absolute;top:{i * HOUR_H}px;right:6px;'
        f'transform:translateY(-50%);font-size:0.72rem;color:{HOUR_LABEL};white-space:nowrap;">'
        f'{to_12h(f"{CAL_START_H + i:02d}:00")}</div>'
        for i in range(n_h + 1)
    )
    gutter_html = (
        f'<div style="width:{GUTTER}px;flex-shrink:0;position:relative;'
        f'border-right:1px solid {CAL_BORDER};">{hour_labels}</div>'
    )

    # ── Hour + half-hour gridlines ────────────────────────────────────────────
    gridlines = ""
    for i in range(n_h):
        top  = i * HOUR_H
        half = top + HOUR_H // 2
        gridlines += (
            f'<div style="position:absolute;left:0;right:0;top:{top}px;'
            f'height:1px;background:{GRID_HOUR};z-index:1;"></div>'
            f'<div style="position:absolute;left:0;right:0;top:{half}px;'
            f'height:1px;background:{GRID_HALF};z-index:1;"></div>'
        )
    gridlines += (
        f'<div style="position:absolute;left:0;right:0;top:{n_h * HOUR_H}px;'
        f'height:1px;background:{GRID_HOUR};z-index:1;"></div>'
    )

    # ── "Now" indicator line + dot ────────────────────────────────────────────
    now_line = ""
    if now_top is not None:
        now_line = (
            f'<div style="position:absolute;left:0;right:0;top:{now_top:.1f}px;'
            f'height:2px;background:{NOW_COLOR};z-index:12;pointer-events:none;">'
            f'<div style="position:absolute;left:-5px;top:-4px;width:10px;height:10px;'
            f'border-radius:50%;background:{NOW_COLOR};"></div>'
            f'</div>'
        )

    # ── Employee event columns ────────────────────────────────────────────────
    emp_cols = ""
    for emp in employees:
        pat   = get_pattern(emp["id"])
        slots = pat["patterns"].get(day, []) if pat else []

        events = ""
        for slot in slots:
            s_m = max(_to_min(slot["start"]), cal_s)
            e_m = min(_to_min(slot["end"]),   cal_e)
            if e_m <= s_m:
                continue

            top_px = (s_m - cal_s) / 60 * HOUR_H
            h_px   = max((e_m - s_m) / 60 * HOUR_H - 3, 4)
            loc    = slot.get("location", "home")
            lbl, bg, border_c, fg = _LOC.get(loc, ("", "#475569", "#64748B", "#F8FAFC"))

            label_html = lbl if h_px >= 18 else ""
            time_html  = (
                f'<div style="font-size:0.66rem;opacity:0.85;margin-top:1px;">'
                f'{to_12h(slot["start"])} – {to_12h(slot["end"])}</div>'
                if h_px >= 34 else ""
            )

            events += (
                f'<div style="position:absolute;top:{top_px:.1f}px;height:{h_px:.1f}px;'
                f'left:4px;right:4px;background:{bg};border-left:3px solid {border_c};'
                f'border-radius:5px;padding:3px 6px;font-size:0.74rem;font-weight:600;'
                f'color:{fg};overflow:hidden;z-index:5;box-sizing:border-box;">'
                f'{label_html}{time_html}'
                f'</div>'
            )

        emp_cols += (
            f'<div style="width:{COL_W}px;flex-shrink:0;position:relative;'
            f'border-right:1px solid {CAL_BORDER};z-index:2;">{events}</div>'
        )

    min_w = GUTTER + COL_W * len(employees)

    html = (
        f'<div style="border:1px solid {CAL_BORDER};border-radius:12px;overflow:hidden;'
        f'font-family:Inter,sans-serif;">'
        f'<div style="overflow-x:auto;overflow-y:auto;max-height:640px;">'
        f'<div style="min-width:{min_w}px;">'
        f'{header}'
        f'<div style="display:flex;height:{body_h}px;">'
        f'{gutter_html}'
        f'<div style="position:relative;flex:1;display:flex;">'
        f'{gridlines}{now_line}{emp_cols}'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ── Right-now status cards (native — accessible and theme-aware) ───────────────

def _section_now(employees: list[dict], day: str, time_str: str) -> None:
    ui.section("Right Now")
    st.markdown(
        ":green-badge[🏠 Home]　:blue-badge[🏢 Office]　"
        ":orange-badge[☕ Away]　:gray-badge[⚫ Not Working]"
    )
    st.markdown("")

    cols = st.columns(4)
    for i, emp in enumerate(employees):
        status = get_status_now(emp["id"], day, time_str)
        meta   = STATUS_META[status]
        if status == "off":
            nxt   = get_next_transition(emp["id"], day, time_str)
            label = f"Starting at {to_12h(nxt[0])}" if nxt else meta["label"]
        else:
            label = meta["label"]
        with cols[i % 4]:
            with st.container(border=True):
                st.markdown(f"**{emp['name']}**")
                st.caption(emp["role"])
                st.markdown(f":{meta['badge']}-badge[{label}]")
                if st.button("View schedule", key=f"now_btn_{emp['id']}", use_container_width=True):
                    _pattern_dialog(emp)


# ── Upcoming transitions within the next hour ─────────────────────────────────

def _section_next_hour(employees: list[dict], day: str, now: datetime) -> None:
    time_str   = _time_str(now)
    future_str = _time_str(now + timedelta(hours=1))
    changes: list[tuple] = []

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

    changes.sort()
    ui.section("Changes in the Next Hour")
    if not changes:
        st.caption("No changes expected in the next hour.")
        return
    for at_time, name, verb, new_status in changes:
        meta = STATUS_META[new_status]
        st.markdown(
            f"**{name}** — {verb} :{meta['badge']}-badge[{meta['label']}] "
            f"at **{to_12h(at_time)}**"
        )


# ── Full schedule expandable ──────────────────────────────────────────────────

def _section_employee_details(employees: list[dict]) -> None:
    ui.section("Employee Schedules")
    for emp in employees:
        pat = get_pattern(emp["id"])
        with st.expander(f"{emp['name']} — {emp['role']}"):
            if not pat:
                st.caption("No working pattern set yet.")
            else:
                for day in DAYS:
                    slots = pat["patterns"].get(day, [])
                    st.markdown(f"**{DAY_LABELS[day]}:** {format_slots(slots)}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    now        = _now()
    day        = _weekday_name(now)
    time_str   = _time_str(now)
    is_workday = day in DAYS

    st.title("📍 Availability Now")
    day_display = DAY_LABELS.get(day, day.capitalize())
    st.markdown(
        f"**{day_display}** · {now.strftime('%d %b %Y')} · "
        f":blue[**{to_12h(time_str)}**] Cairo time"
    )
    st.divider()

    employees = get_active_employees()
    if not employees:
        st.info("No active employees. Add employees via the Employees page.")
        return

    # ── Name filter ───────────────────────────────────────────────────────────
    all_names = sorted(e["name"] for e in employees)
    selected  = st.multiselect(
        "Filter employees",
        options=all_names,
        placeholder="All employees — select to filter",
        label_visibility="collapsed",
    )
    filtered = [e for e in employees if e["name"] in selected] if selected else employees

    # Sort: active statuses (home/office) first, then away, then off; alphabetical within group
    _STATUS_ORDER = {"home": 0, "office": 0, "away": 1, "off": 2}
    filtered = sorted(
        filtered,
        key=lambda e: (_STATUS_ORDER.get(get_status_now(e["id"], day, time_str), 2), e["name"]),
    )

    if not is_workday:
        st.warning(
            f"Today is {day_display} — outside the work week (Sun–Thu). Showing schedules below."
        )
        _section_employee_details(filtered)
        return

    _section_now(filtered, day, time_str)

    st.markdown("")
    _section_next_hour(filtered, day, now)

    st.markdown("")
    ui.section("Day Calendar")
    _section_calendar_day(filtered, day, now)

    st.markdown("")
    _section_employee_details(filtered)


main()
