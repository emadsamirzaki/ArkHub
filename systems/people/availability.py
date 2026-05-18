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
    "home":   {"label": "🏠 Working from Home", "bg": "#14532D", "color": "#86EFAC"},
    "office": {"label": "🏢 In the Office",      "bg": "#1E3A5F", "color": "#93C5FD"},
    "away":   {"label": "☕ Away / Break",        "bg": "#78350F", "color": "#FCD34D"},
    "off":    {"label": "⚫ Not Working",         "bg": "#1E293B", "color": "#64748B"},
}

# Calendar display range
CAL_START_H = 7
CAL_END_H   = 22

HOUR_H  = 60    # px per hour
GUTTER  = 56    # px — time-label column
COL_W   = 150   # px — per employee column

_LOC = {
    "home":   ("🏠 Home",   "#14532D", "#22C55E", "#86EFAC"),
    "office": ("🏢 Office", "#1E3A5F", "#3B82F6", "#93C5FD"),
    "away":   ("☕ Away",   "#78350F", "#F59E0B", "#FCD34D"),
}

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

/* ── Now-cards ──
 * The st.button IS the entire card.
 * Role and status are injected via CSS ::after pseudo-elements so they
 * appear inside the button with their own colours — no extra DOM elements.
 */

.next-row  { background:#1E293B; border-radius:8px; padding:10px 14px; margin-bottom:6px; font-size:0.88rem; color:#CBD5E1; }
.next-time { color:#60A5FA; font-weight:700; }
</style>
"""


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

    # ── Column headers ────────────────────────────────────────────────────────
    col_heads = "".join(
        f'<div style="width:{COL_W}px;flex-shrink:0;padding:10px 6px 8px;'
        f'text-align:center;border-right:1px solid #1E293B;box-sizing:border-box;">'
        f'<div style="font-size:0.8rem;font-weight:700;color:#F1F5F9;'
        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{emp["name"]}</div>'
        f'<div style="font-size:0.65rem;color:#64748B;margin-top:1px;">{emp["role"]}</div>'
        f'</div>'
        for emp in employees
    )
    header = (
        f'<div style="display:flex;background:#0F172A;border-bottom:2px solid #334155;'
        f'position:sticky;top:0;z-index:10;">'
        f'<div style="width:{GUTTER}px;flex-shrink:0;border-right:1px solid #1E293B;'
        f'background:#0F172A;"></div>'
        f'{col_heads}'
        f'</div>'
    )

    # ── Time-label gutter ─────────────────────────────────────────────────────
    hour_labels = "".join(
        f'<div style="position:absolute;top:{i * HOUR_H}px;right:6px;'
        f'transform:translateY(-50%);font-size:0.65rem;color:#475569;white-space:nowrap;">'
        f'{to_12h(f"{CAL_START_H + i:02d}:00")}</div>'
        for i in range(n_h + 1)
    )
    gutter_html = (
        f'<div style="width:{GUTTER}px;flex-shrink:0;position:relative;'
        f'border-right:1px solid #1E293B;">{hour_labels}</div>'
    )

    # ── Hour + half-hour gridlines ────────────────────────────────────────────
    gridlines = ""
    for i in range(n_h):
        top  = i * HOUR_H
        half = top + HOUR_H // 2
        gridlines += (
            f'<div style="position:absolute;left:0;right:0;top:{top}px;'
            f'height:1px;background:#1E293B;z-index:1;"></div>'
            f'<div style="position:absolute;left:0;right:0;top:{half}px;'
            f'height:1px;background:#0F2030;z-index:1;"></div>'
        )
    gridlines += (
        f'<div style="position:absolute;left:0;right:0;top:{n_h * HOUR_H}px;'
        f'height:1px;background:#1E293B;z-index:1;"></div>'
    )

    # ── "Now" indicator line + dot ────────────────────────────────────────────
    now_line = ""
    if now_top is not None:
        now_line = (
            f'<div style="position:absolute;left:0;right:0;top:{now_top:.1f}px;'
            f'height:2px;background:#F472B6;z-index:12;pointer-events:none;">'
            f'<div style="position:absolute;left:-5px;top:-4px;width:10px;height:10px;'
            f'border-radius:50%;background:#F472B6;"></div>'
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
            lbl, bg, border_c, fg = _LOC.get(loc, ("", "#1E293B", "#475569", "#94A3B8"))

            label_html = lbl if h_px >= 18 else ""
            time_html  = (
                f'<div style="font-size:0.62rem;opacity:0.75;margin-top:1px;">'
                f'{to_12h(slot["start"])} – {to_12h(slot["end"])}</div>'
                if h_px >= 34 else ""
            )

            events += (
                f'<div style="position:absolute;top:{top_px:.1f}px;height:{h_px:.1f}px;'
                f'left:4px;right:4px;background:{bg};border-left:3px solid {border_c};'
                f'border-radius:5px;padding:3px 6px;font-size:0.73rem;font-weight:600;'
                f'color:{fg};overflow:hidden;z-index:5;box-sizing:border-box;">'
                f'{label_html}{time_html}'
                f'</div>'
            )

        emp_cols += (
            f'<div style="width:{COL_W}px;flex-shrink:0;position:relative;'
            f'border-right:1px solid #1E293B;z-index:2;">{events}</div>'
        )

    min_w = GUTTER + COL_W * len(employees)

    html = (
        f'<div style="border:1px solid #1E293B;border-radius:12px;overflow:hidden;'
        f'background:#0F172A;font-family:Inter,sans-serif;">'
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


# ── Right-now status cards ────────────────────────────────────────────────────

def _section_now(employees: list[dict], day: str, time_str: str) -> None:
    st.markdown('<p class="section-heading">Right Now</p>', unsafe_allow_html=True)
    cols = st.columns(4)
    for i, emp in enumerate(employees):
        status = get_status_now(emp["id"], day, time_str)
        meta   = STATUS_META[status]
        cid    = emp["id"]
        bg     = meta["bg"]
        fg     = meta["color"]
        # Escape quotes so they're safe inside CSS string values
        role   = emp["role"].replace('"', '\\"')
        label  = meta["label"].replace('"', '\\"')
        with cols[i % 4]:
            st.markdown(
                f'<div class="now-m-{cid}"></div>'
                f'<style>'
                # Button container
                f'[data-testid="element-container"]:has(.now-m-{cid})'
                f' + [data-testid="element-container"]'
                f'{{position:relative;z-index:2;}}'
                # Button = full card: coloured background, border, rounded corners
                f'[data-testid="element-container"]:has(.now-m-{cid})'
                f' + [data-testid="element-container"] button'
                f'{{background:{bg}!important;border:1px solid #334155!important;'
                f'border-radius:12px!important;min-height:96px!important;'
                f'width:100%!important;text-align:left!important;'
                f'padding:16px 20px 16px!important;color:#F1F5F9!important;'
                f'font-weight:700!important;font-size:1rem!important;'
                f'box-shadow:none!important;cursor:pointer!important;'
                f'display:flex!important;flex-direction:column!important;'
                f'align-items:flex-start!important;}}'
                # Role — injected after the name <p> inside the button
                f'[data-testid="element-container"]:has(.now-m-{cid})'
                f' + [data-testid="element-container"] button p::after'
                f'{{content:"{role}";display:block;'
                f'font-size:0.8rem;font-weight:400;color:#94A3B8;margin-top:4px;}}'
                # Status — injected as button ::after flex item
                f'[data-testid="element-container"]:has(.now-m-{cid})'
                f' + [data-testid="element-container"] button::after'
                f'{{content:"{label}";display:block;'
                f'font-size:0.85rem;font-weight:600;color:{fg};margin-top:10px;}}'
                # Hover
                f'[data-testid="element-container"]:has(.now-m-{cid})'
                f' + [data-testid="element-container"] button:hover'
                f'{{opacity:0.85!important;border-color:#60A5FA!important;}}'
                f'</style>',
                unsafe_allow_html=True,
            )
            if st.button(emp["name"], key=f"now_btn_{cid}", use_container_width=True):
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

    if not changes:
        return

    changes.sort()
    st.markdown('<p class="section-heading">Changes in the Next Hour</p>', unsafe_allow_html=True)
    for at_time, name, verb, new_status in changes:
        meta = STATUS_META[new_status]
        st.markdown(
            f'<div class="next-row">'
            f'<b>{name}</b> — {verb} '
            f'<span style="color:{meta["color"]};">{meta["label"]}</span> '
            f'at <span class="next-time">{to_12h(at_time)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Full schedule expandable ──────────────────────────────────────────────────

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


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

    now        = _now()
    day        = _weekday_name(now)
    time_str   = _time_str(now)
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

    # ── Name filter ───────────────────────────────────────────────────────────
    all_names = sorted(e["name"] for e in employees)
    selected  = st.multiselect(
        "Filter employees",
        options=all_names,
        placeholder="All employees — select to filter",
        label_visibility="collapsed",
    )
    filtered = [e for e in employees if e["name"] in selected] if selected else employees

    if not is_workday:
        st.warning(
            f"Today is {day_display} — outside the work week (Sun–Thu). Showing schedules below."
        )
        _section_employee_details(filtered)
        return

    # Right Now first, then calendar
    _section_now(filtered, day, time_str)

    st.markdown("")
    st.markdown('<p class="section-heading">Day Calendar</p>', unsafe_allow_html=True)
    _section_calendar_day(filtered, day, now)

    st.markdown("")
    _section_next_hour(filtered, day, now)

    st.markdown("")
    _section_employee_details(filtered)


main()
