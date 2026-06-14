"""
systems/arkscore/scorecard_dashboard.py
L10 weekly scorecard dashboard.
"""
from __future__ import annotations

import streamlit as st

from systems.arkscore.utils.entry_store import (
    current_week_label,
    get_entries_for_week,
    get_all_weeks as get_entry_weeks,
)
from systems.arkscore.utils.project_store import load_projects
from systems.arkscore.utils.scorecard_store import get_entry, get_all_weeks
from systems.arkscore.utils.utilization_store import get_report, get_all_week_labels
from systems.utils import ui

st.title("🏆 L10 Scorecard")
st.caption("Weekly leadership dashboard · Arkdev")
st.divider()

# ── Week selector ──────────────────────────────────────────────────────────────
col_week, _ = st.columns([2, 4])
with col_week:
    st.markdown("📅 **Select Week to Review**")

all_weeks = get_all_weeks()  # only weeks with saved scorecard entries, sorted DESC

if not all_weeks:
    st.info("No scorecard entries saved yet. Use **L10 Scorecard Entry** to add the first week.")
    st.stop()

selected_week = st.selectbox("Week", all_weeks, index=0, label_visibility="collapsed")

# ── Load data for selected week ────────────────────────────────────────────────
entry = get_entry(selected_week)
d = entry["data"] if entry else {}

# Load previous week data for comparison
prev_week = None
prev_data = {}
if all_weeks and selected_week in all_weeks:
    idx = all_weeks.index(selected_week)
    if idx + 1 < len(all_weeks):
        prev_week = all_weeks[idx + 1]
        prev_entry = get_entry(prev_week)
        prev_data = prev_entry["data"] if prev_entry else {}

# Auto: Client Health (#4)
health_entries = get_entries_for_week(selected_week)
active_projects = [p for p in load_projects() if p["status"] == "Active"]
entry_map = {e["project_id"]: e for e in health_entries}
checked = [p for p in active_projects if p["id"] in entry_map]
on_track = sum(1 for p in checked if entry_map[p["id"]]["health_status"] == "On Track")
client_health_pct = round(on_track / len(checked) * 100, 1) if checked else None

# Use manually entered value if auto calculation is unavailable
if client_health_pct is None and "client_health_pct" in d:
    client_health_pct = d.get("client_health_pct")

# Auto: Utilization (#9)
report = get_report(selected_week)
team_utilization_pct = None
total_billable_pct = None
if report and report.get("raw_rows"):
    per_user = {}
    for row in report["raw_rows"]:
        user = row.get("User", "")
        duration = float(row.get("Duration (decimal)", 0))
        billable = row.get("Billable", "").strip().lower() == "yes"

        if user not in per_user:
            per_user[user] = {"total": 0, "billable": 0}
        per_user[user]["total"] += duration
        if billable:
            per_user[user]["billable"] += duration

    if per_user:
        utilizations = []
        billables = []
        for data in per_user.values():
            total = data["total"]
            bill = data["billable"]
            util_pct = (total / 35.0 * 100) if total > 0 else 0
            bill_pct = (bill / total * 100) if total > 0 else 0
            utilizations.append(util_pct)
            billables.append(bill_pct)

        if utilizations:
            team_utilization_pct = round(sum(utilizations) / len(utilizations), 1)
        if billables:
            total_billable_pct = round(sum(billables) / len(billables), 1)

# Use manually entered values if auto calculation is unavailable
if team_utilization_pct is None and "team_utilization_pct" in d:
    team_utilization_pct = d.get("team_utilization_pct")
if total_billable_pct is None and "total_billable_pct" in d:
    total_billable_pct = d.get("total_billable_pct")

# ── Metric owners ──────────────────────────────────────────────────────────────
METRIC_OWNERS = {
    1: "Amgad",
    2: "Amgad",
    3: "Amgad",
    4: "Emad",
    5: "Amgad",
    6: "Amgad",
    7: "Emad",
    8: "Emad",
    9: "Emad",
    10: "John",
}

# ── Helper functions ───────────────────────────────────────────────────────────

def _fmt(val, suffix="", prefix="") -> str:
    if val is None:
        return "—"
    if isinstance(val, float):
        return f"{prefix}{val:,.1f}{suffix}"
    return f"{prefix}{val}{suffix}"

def _status_badge(met: bool | None) -> str:
    if met is True:
        return ":green-badge[● On Track]"
    if met is False:
        return ":red-badge[● Off Track]"
    return ":gray-badge[– No data]"

def _val_or_none(key: str):
    v = d.get(key)
    return None if v is None else v


def _met_gt(key: str, threshold) -> bool | None:
    v = _val_or_none(key)
    if v is None:
        return None
    return v > threshold


def _met_lt(key: str, threshold) -> bool | None:
    v = _val_or_none(key)
    if v is None:
        return None
    return v < threshold


def _met_lte(key: str, threshold) -> bool | None:
    v = _val_or_none(key)
    if v is None:
        return None
    return v <= threshold


def _auto_met(val, operator: str, threshold) -> bool | None:
    if val is None:
        return None
    if operator == ">":
        return val > threshold
    if operator == ">=":
        return val >= threshold
    if operator == "<":
        return val < threshold
    return None

# ── Scorecard table (rendered natively so it re-themes with light/dark) ─────────

_COLS = [0.5, 3.0, 1.1, 2.0, 1.5, 1.7]


def _header_row() -> None:
    c = st.columns(_COLS)
    for col, label in zip(c, ["#", "Metric", "Owner", "Value", "Target", "Status"]):
        col.markdown(f"**{label}**")


def metric_row(num, name, desc, value_md, target, owner, met,
               *, auto: bool = False, link: str | None = None, hint: str | None = None,
               current_val=None, prev_val=None) -> None:
    status_md = _status_badge(met)
    target_md = target

    # Week-over-week comparison (e.g. metric #10)
    if current_val is not None and prev_val is not None:
        if current_val > prev_val:
            target_md, status_md = "▲ vs last week", ":green-badge[● On Track]"
        elif current_val < prev_val:
            target_md, status_md = "▼ vs last week", ":red-badge[● Off Track]"
        else:
            target_md, status_md = "→ same", ":gray-badge[– Same]"

    # Escape comparison operators so a leading '>' isn't read as a blockquote.
    target_md = target_md.replace("<", "\\<").replace(">", "\\>")

    c = st.columns(_COLS, vertical_alignment="center")
    c[0].markdown(f"**{num}**")
    with c[1]:
        title = f"**{name}**"
        if link:
            title += f"　[📋]({link})"
        if auto:
            title += "　:blue-badge[Auto]"
        st.markdown(title)
        st.caption(desc)
    c[2].markdown(f":blue-badge[{owner}]")
    with c[3]:
        st.markdown(value_md)
        if hint:
            st.caption(hint)
    c[4].markdown(target_md)
    c[5].markdown(status_md)

# Build pipeline metric #1 value and status
pc   = _val_or_none("pipeline_count")
pv   = _val_or_none("pipeline_value")
pai  = _val_or_none("pipeline_ai_pct")
m1_val = "—"
m1_met = None
if pc is not None or pv is not None or pai is not None:
    parts = []
    if pc  is not None: parts.append(f"{int(pc)}")
    if pv  is not None: parts.append(f"${pv:,.0f}K")
    if pai is not None: parts.append(f"AI {pai:.0f}%")
    m1_val = " / ".join(parts)
    # On Track if all three targets met (or entered)
    checks = []
    if pc  is not None: checks.append(pc  > 5)
    if pv  is not None: checks.append(pv  > 500)
    if pai is not None: checks.append(pai > 75)
    m1_met = all(checks) if checks else None

# Red flags #7
rf6 = _val_or_none("red_flags_6")
rf5 = _val_or_none("red_flags_5")
rf4 = _val_or_none("red_flags_4")
m7_val = "—"
m7_met = None
if rf6 is not None or rf5 is not None or rf4 is not None:
    m7_val = f"{rf6 or 0} / {rf5 or 0} / {rf4 or 0}"
    checks = []
    if rf6 is not None: checks.append(rf6 <= 2)
    if rf5 is not None: checks.append(rf5 <= 1)
    if rf4 is not None: checks.append(rf4 == 0)
    m7_met = all(checks) if checks else None

# Closed-won #3
cob = _val_or_none("closed_won_bd")
cou = _val_or_none("closed_won_upsell")
m3_val = "—"
m3_met = None
if cob is not None or cou is not None:
    m3_val = f"{cob or 0} / {cou or 0}"
    checks = []
    if cob is not None: checks.append(cob > 1)
    if cou is not None: checks.append(cou > 1)
    m3_met = all(checks) if checks else None

_RED_FLAGS_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1G3T7Wf2KZpwTgLE4fbv19IFii7ZPJe3hNGqjy-JaoZo/edit"
    "?resourcekey=&gid=543241089#gid=543241089"
)

with st.container(border=True):
    _header_row()

    ui.section("🔵 BD & Pipeline")
    metric_row(1, "Active Pipeline Opportunities", "Count / Total Value / AI%",
               m1_val, ">5 / >$500K / AI>75%", METRIC_OWNERS[1], m1_met)
    metric_row(2, "Conversations with New Qualified Leads",
               "Meaningful conversations with pre-qualified prospects",
               _fmt(_val_or_none("qualified_leads")), ">3 / week",
               METRIC_OWNERS[2], _met_gt("qualified_leads", 3))
    metric_row(3, "Closed-Won Opportunities — Rolling 8 Weeks", "BD New / Team Upselling",
               m3_val, ">1 / >1", METRIC_OWNERS[3], m3_met)

    ui.section("🟢 Client Health")
    metric_row(4, "Client Health % Green", "PM Assessment — On Track projects this week",
               _fmt(client_health_pct, suffix="%"), ">80%", METRIC_OWNERS[4],
               _auto_met(client_health_pct, ">", 80), auto=True)

    ui.section("💰 Financial")
    metric_row(5, "Rolling 12-Week Collection", "Cash collected vs. quarterly target",
               _fmt(_val_or_none("collection_pct"), suffix="%"), ">100%",
               METRIC_OWNERS[5], _met_gt("collection_pct", 100))
    metric_row(6, "GV Financial Dependency — Rolling 12 Weeks", "GV share of total income",
               _fmt(_val_or_none("gv_dependency_pct"), suffix="%"), "<70%",
               METRIC_OWNERS[6], _met_lt("gv_dependency_pct", 70))

    ui.section("👥 People")
    metric_row(7, "Employee Red Flags", "#6s / #5s / #4-or-less satisfaction scores",
               m7_val, "≤2 / ≤1 / 0", METRIC_OWNERS[7], m7_met, link=_RED_FLAGS_URL)
    metric_row(8, "Process Violations — Rolling 4 Weeks", "People with >4 missed commitments",
               _fmt(_val_or_none("process_violations")), "<5 people",
               METRIC_OWNERS[8], _met_lt("process_violations", 5))

    ui.section("⚙️ Operations")
    metric_row(9, "Team Utilization & Billable", "Team Utilization % and Billable % (from Clockify)",
               f'● Team Util: {_fmt(team_utilization_pct, suffix="%")}  \n'
               f'● Billable: {_fmt(total_billable_pct, suffix="%")}',
               "≥65%", METRIC_OWNERS[9], _auto_met(total_billable_pct, ">=", 65), auto=True)

    ui.section("🤖 AI & Delivery")
    metric_row(10, "AI Transformation — Projects Adoption",
               "% of projects using Claude & building AI skills",
               _fmt(_val_or_none("ai_adoption_pct"), suffix="%"), "↑ vs last week",
               METRIC_OWNERS[10], None,
               hint=d.get("ai_adoption_hint"),
               current_val=_val_or_none("ai_adoption_pct"),
               prev_val=prev_data.get("ai_adoption_pct") if prev_data else None)

st.markdown("")
col_note, col_edit = st.columns([3, 1], vertical_alignment="center")
with col_note:
    st.caption("📡 Metrics marked **Auto** pull live from Utilization Check-in & Projects Weekly Check-in.")
with col_edit:
    st.page_link("systems/arkscore/scorecard_entry.py", label="Edit this week", icon="✏️")
