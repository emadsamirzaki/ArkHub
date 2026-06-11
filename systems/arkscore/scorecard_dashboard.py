"""
systems/arkscore/scorecard_dashboard.py
L10 weekly scorecard dashboard.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from systems.arkscore.utils.entry_store import (
    current_week_label,
    get_entries_for_week,
    get_all_weeks as get_entry_weeks,
)
from systems.arkscore.utils.project_store import load_projects
from systems.arkscore.utils.scorecard_store import get_entry, get_all_weeks
from systems.arkscore.utils.utilization_store import get_report, get_all_week_labels
from systems.arkscore.utils.constants import (
    COLOR_BG, COLOR_CARD, COLOR_BORDER, COLOR_TEXT, COLOR_MUTED,
)

COLOR_GREEN  = "#22C55E"
COLOR_RED    = "#EF4444"
COLOR_AMBER  = "#F59E0B"
COLOR_BLUE   = "#60A5FA"

# Dark mode colors
BG = "#0F172A"
CARD_BG = "#1A2332"
TEXT = "#E2E8F0"
MUTED = "#94A3B8"
HEADER = "linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%)"
HEADER_BORDER = "#3B82F6"
HEADER_TEXT = "#93C5FD"
HOVER = "rgba(59, 130, 246, 0.05)"
SECTION_BD = "#3B82F6"
SECTION_HEALTH = "#10B981"
SECTION_FIN = "#F59E0B"
SECTION_PEOPLE = "#EC4899"
SECTION_OPS = "#06B6D4"
SECTION_AI = "#8B5CF6"

st.markdown(f"""
<style>
.stApp {{ background-color: {BG}; }}

.sc-table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
}}

.sc-table th {{
    font-size: 0.7rem;
    font-weight: 700;
    color: {HEADER_TEXT};
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 14px 12px;
    background: {HEADER};
    border-bottom: 2px solid {HEADER_BORDER};
    text-align: left;
}}

.sc-table td {{
    font-size: 0.9rem;
    color: {TEXT};
    padding: 14px 12px;
    border-bottom: 1px solid #334155;
    vertical-align: middle;
}}

.sc-table tbody tr:hover {{
    background-color: {HOVER};
}}

.sc-table tr:last-child td {{ border-bottom: none; }}

.sc-section-row {{
    background-color: transparent !important;
}}

.sc-section-row td {{
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    padding: 14px 12px;
    border: 1px solid;
    border-left: 6px solid #3B82F6;
    margin: 8px 0;
    border-radius: 6px;
}}

.sc-section-bd td {{
    background: rgba(59, 130, 246, 0.1);
    border-left-color: {SECTION_BD} !important;
    border-color: {SECTION_BD};
    color: {SECTION_BD};
}}

.sc-section-health td {{
    background: rgba(16, 185, 129, 0.1);
    border-left-color: {SECTION_HEALTH} !important;
    border-color: {SECTION_HEALTH};
    color: {SECTION_HEALTH};
}}

.sc-section-fin td {{
    background: rgba(245, 158, 11, 0.1);
    border-left-color: {SECTION_FIN} !important;
    border-color: {SECTION_FIN};
    color: {SECTION_FIN};
}}

.sc-section-people td {{
    background: rgba(236, 72, 153, 0.1);
    border-left-color: {SECTION_PEOPLE} !important;
    border-color: {SECTION_PEOPLE};
    color: {SECTION_PEOPLE};
}}

.sc-section-ops td {{
    background: rgba(6, 182, 212, 0.1);
    border-left-color: {SECTION_OPS} !important;
    border-color: {SECTION_OPS};
    color: {SECTION_OPS};
}}

.sc-section-ai td {{
    background: rgba(139, 92, 246, 0.1);
    border-left-color: {SECTION_AI} !important;
    border-color: {SECTION_AI};
    color: {SECTION_AI};
}}

.sc-num {{
    font-weight: 700;
    color: #3B82F6;
    font-size: 1.1rem;
}}

.sc-area {{
    font-size: 0.75rem;
    color: {MUTED};
    font-weight: 600;
}}

.sc-metric-name {{
    font-weight: 700;
    color: {TEXT};
    font-size: 0.95rem;
}}

.sc-metric-desc {{
    font-size: 0.8rem;
    color: {MUTED};
    margin-top: 3px;
}}

.sc-value {{
    font-weight: 700;
    font-size: 1.15rem;
    color: #3B82F6;
    line-height: 1.5;
}}

.sc-target {{
    font-size: 0.85rem;
    color: {MUTED};
    font-weight: 600;
}}

.badge-green  {{
    color: #10B981;
    font-weight: 700;
    font-size: 0.95rem;
}}

.badge-red    {{
    color: #EF4444;
    font-weight: 700;
    font-size: 0.95rem;
}}

.badge-grey   {{
    color: {MUTED};
    font-weight: 600;
    font-size: 0.95rem;
}}

.badge-auto   {{
    display: inline-block;
    background: {HEADER};
    color: {HEADER_TEXT};
    font-size: 0.65rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 99px;
    vertical-align: middle;
    margin-left: 6px;
    border: 1px solid {HEADER_BORDER};
}}

.sc-owner {{
    font-size: 0.85rem;
    color: {HEADER_TEXT};
    font-weight: 600;
    background: {HEADER};
    padding: 6px 10px;
    border-radius: 6px;
    display: inline-block;
    border: 1px solid {HEADER_BORDER};
}}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="background: {HEADER}; padding: 28px; border-radius: 12px; margin-bottom: 24px; border: 2px solid {HEADER_BORDER}; box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);">
    <h1 style="color: {HEADER_TEXT}; margin: 0 0 8px 0; font-size: 2.2rem; font-weight: 800;">🏆 L10 Scorecard</h1>
    <p style="color: {HEADER_TEXT}; margin: 0; font-size: 1rem; opacity: 0.9;">Weekly leadership dashboard · Arkdev</p>
</div>
""", unsafe_allow_html=True)

# ── Week selector ──────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
.week-selector-label {{
    color: #60A5FA;
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
    display: block;
}}
.week-selector-container {{
    background: #1E3A5F;
    padding: 16px 20px;
    border-radius: 10px;
    border: 1px solid #3B82F6;
    margin-bottom: 20px;
}}
</style>
<div class="week-selector-container">
    <div class="week-selector-label">📅 Select Week to Review</div>
</div>
""", unsafe_allow_html=True)

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

def _status(met: bool | None) -> str:
    if met is True:
        return '<span class="badge-green">● On Track</span>'
    if met is False:
        return '<span class="badge-red">● Off Track</span>'
    return '<span class="badge-grey">– No data</span>'

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

# ── Scorecard table ────────────────────────────────────────────────────────────

def row(num, area, name, desc, value_html, target_html, owner, met: bool | None, hint: str = None, current_val = None, prev_val = None) -> str:
    status_content = _status(met)
    target_display = target_html

    # For week-over-week comparison (like metric #10)
    if current_val is not None and prev_val is not None:
        if current_val > prev_val:
            target_display = "↑"
            status_content = '<span class="badge-green">● On Track</span>'
        elif current_val < prev_val:
            target_display = "↓"
            status_content = '<span class="badge-red">● Off Track</span>'
        else:
            target_display = "→"
            status_content = '<span class="badge-grey">– Same</span>'

    value_with_hint = value_html
    if hint:
        value_with_hint = f'{value_html}<div style="font-size: 0.75rem; color: #94A3B8; margin-top: 6px; font-weight: 500;">{hint}</div>'

    return f"""
    <tr>
      <td><span class="sc-num">{num}</span></td>
      <td><span class="sc-area">{area}</span></td>
      <td>
        <div class="sc-metric-name">{name}</div>
        <div class="sc-metric-desc">{desc}</div>
      </td>
      <td><span class="sc-owner">{owner}</span></td>
      <td><span class="sc-value">{value_with_hint}</span></td>
      <td><span class="sc-target">{target_display}</span></td>
      <td>{status_content}</td>
    </tr>
    """

def section_row(label: str, section_class: str = "") -> str:
    return f'<tr class="sc-section-row {section_class}"><td colspan="7">{label}</td></tr>'

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

table_html = f"""
<style>
.sc-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
.sc-table th {{
    font-size: 0.7rem;
    font-weight: 700;
    color: {HEADER_TEXT};
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 14px 12px;
    background: {HEADER};
    border-bottom: 2px solid {HEADER_BORDER};
    text-align: left;
}}
.sc-table td {{
    font-size: 0.9rem;
    color: {TEXT};
    padding: 14px 12px;
    border-bottom: 1px solid #334155;
    vertical-align: middle;
}}
.sc-table tbody tr:hover {{ background-color: {HOVER}; }}
.sc-table tr:last-child td {{ border-bottom: none; }}
.sc-section-row td {{
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    padding: 14px 12px;
    border: 1px solid;
    border-left: 6px solid #3B82F6;
    margin: 8px 0;
    border-radius: 6px;
}}
.sc-section-bd td {{
    background: rgba(59, 130, 246, 0.1);
    border-left-color: {SECTION_BD} !important;
    border-color: {SECTION_BD};
    color: {SECTION_BD};
}}
.sc-section-health td {{
    background: rgba(16, 185, 129, 0.1);
    border-left-color: {SECTION_HEALTH} !important;
    border-color: {SECTION_HEALTH};
    color: {SECTION_HEALTH};
}}
.sc-section-fin td {{
    background: rgba(245, 158, 11, 0.1);
    border-left-color: {SECTION_FIN} !important;
    border-color: {SECTION_FIN};
    color: {SECTION_FIN};
}}
.sc-section-people td {{
    background: rgba(236, 72, 153, 0.1);
    border-left-color: {SECTION_PEOPLE} !important;
    border-color: {SECTION_PEOPLE};
    color: {SECTION_PEOPLE};
}}
.sc-section-ops td {{
    background: rgba(6, 182, 212, 0.1);
    border-left-color: {SECTION_OPS} !important;
    border-color: {SECTION_OPS};
    color: {SECTION_OPS};
}}
.sc-section-ai td {{
    background: rgba(139, 92, 246, 0.1);
    border-left-color: {SECTION_AI} !important;
    border-color: {SECTION_AI};
    color: {SECTION_AI};
}}
.sc-num {{ font-weight: 700; color: #3B82F6; font-size: 1.1rem; }}
.sc-area {{ font-size: 0.75rem; color: {MUTED}; font-weight: 600; }}
.sc-metric-name {{ font-weight: 700; color: {TEXT}; font-size: 0.95rem; }}
.sc-metric-desc {{ font-size: 0.8rem; color: {MUTED}; margin-top: 3px; }}
.sc-owner {{ font-size: 0.85rem; color: {HEADER_TEXT}; font-weight: 600; background: {HEADER}; padding: 6px 10px; border-radius: 6px; display: inline-block; border: 1px solid {HEADER_BORDER}; }}
.sc-value {{ font-weight: 700; font-size: 1.15rem; color: #3B82F6; }}
.sc-target {{ font-size: 0.85rem; color: {MUTED}; font-weight: 600; }}
.badge-green {{ color: #10B981; font-weight: 700; font-size: 0.95rem; }}
.badge-red {{ color: #EF4444; font-weight: 700; font-size: 0.95rem; }}
.badge-grey {{ color: {MUTED}; font-weight: 600; font-size: 0.95rem; }}
.badge-auto {{
    display: inline-block;
    background: {HEADER};
    color: {HEADER_TEXT};
    font-size: 0.65rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 99px;
    vertical-align: middle;
    margin-left: 6px;
    border: 1px solid {HEADER_BORDER};
}}
</style>
<div style="background:{CARD_BG};border:2px solid {HEADER_BORDER};border-radius:12px;overflow:hidden;box-shadow:0 8px 24px rgba(59, 130, 246, 0.15);padding:0;">
<table class="sc-table">
  <thead>
    <tr>
      <th style="width: 5%">#</th><th style="width: 12%">Area</th><th style="width: 28%">Metric</th><th style="width: 12%">Owner</th><th style="width: 13%">Value</th><th style="width: 15%">Target</th><th style="width: 15%">Status</th>
    </tr>
  </thead>
  <tbody>
    {section_row("🔵 BD &amp; Pipeline", "sc-section-bd")}
    {row(1, "BD &amp; Pipeline",
         "Active Pipeline Opportunities",
         "Count / Total Value / AI%",
         m1_val,
         "&gt;5 / &gt;$500K / AI&gt;75%",
         METRIC_OWNERS[1],
         m1_met)}
    {row(2, "BD &amp; Pipeline",
         "Conversations with New Qualified Leads",
         "Meaningful conversations with pre-qualified prospects",
         _fmt(_val_or_none("qualified_leads")),
         "&gt;3 / week",
         METRIC_OWNERS[2],
         _met_gt("qualified_leads", 3))}
    {row(3, "BD &amp; Pipeline",
         "Closed-Won Opportunities — Rolling 8 Weeks",
         "BD New / Team Upselling",
         m3_val,
         "&gt;1 / &gt;1",
         METRIC_OWNERS[3],
         m3_met)}
    {section_row("🟢 Client Health", "sc-section-health")}
    {row(4, "Client Health",
         'Client Health % Green <span class="badge-auto">Auto</span>',
         "PM Assessment — On Track projects this week",
         _fmt(client_health_pct, suffix="%"),
         "&gt;80%",
         METRIC_OWNERS[4],
         _auto_met(client_health_pct, ">", 80))}
    {section_row("💰 Financial", "sc-section-fin")}
    {row(5, "Financial",
         "Rolling 12-Week Collection",
         "Cash collected vs. quarterly target",
         _fmt(_val_or_none("collection_pct"), suffix="%"),
         "&gt;100%",
         METRIC_OWNERS[5],
         _met_gt("collection_pct", 100))}
    {row(6, "Financial",
         "GV Financial Dependency — Rolling 12 Weeks",
         "GV share of total income",
         _fmt(_val_or_none("gv_dependency_pct"), suffix="%"),
         "&lt;70%",
         METRIC_OWNERS[6],
         _met_lt("gv_dependency_pct", 70))}
    {section_row("👥 People", "sc-section-people")}
    {row(7, "People",
         'Employee Red Flags <a href="https://docs.google.com/spreadsheets/d/1G3T7Wf2KZpwTgLE4fbv19IFii7ZPJe3hNGqjy-JaoZo/edit?resourcekey=&gid=543241089#gid=543241089" target="_blank" style="color:#60A5FA; text-decoration:none; margin-left:6px;">📋</a>',
         "#6s / #5s / #4-or-less satisfaction scores",
         m7_val,
         "≤2 / ≤1 / 0",
         METRIC_OWNERS[7],
         m7_met)}
    {row(8, "People",
         "Process Violations — Rolling 4 Weeks",
         "People with &gt;4 missed commitments",
         _fmt(_val_or_none("process_violations")),
         "&lt;5 people",
         METRIC_OWNERS[8],
         _met_lt("process_violations", 5))}
    {section_row("⚙️ Operations", "sc-section-ops")}
    {row(9, "Operations",
         'Team Utilization & Billable <span class="badge-auto">Auto</span>',
         "Team Utilization % and Billable % (from Clockify)",
         f'● Team Util: {_fmt(team_utilization_pct, suffix="%")}<br/>● Billable: {_fmt(total_billable_pct, suffix="%")}',
         "≥65%",
         METRIC_OWNERS[9],
         _auto_met(total_billable_pct, ">=", 65))}
    {section_row("🤖 AI &amp; Delivery", "sc-section-ai")}
    {row(10, "AI &amp; Delivery",
         "AI Transformation — Projects Adoption",
         "% of projects using Claude &amp; building AI skills",
         _fmt(_val_or_none("ai_adoption_pct"), suffix="%"),
         "↑ Week",
         METRIC_OWNERS[10],
         None,
         hint=d.get("ai_adoption_hint"),
         current_val=_val_or_none("ai_adoption_pct"),
         prev_val=prev_data.get("ai_adoption_pct") if prev_data else None)}
  </tbody>
</table>

<div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid #334155; text-align: right;">
  <a href="/scorecard_entry" style="color: #60A5FA; text-decoration: none; font-weight: 600; font-size: 0.95rem; transition: all 0.2s ease;">
    ✏️ Edit this week →
  </a>
</div>
</div>
"""

st.markdown('<div style="margin: 16px 0;"></div>', unsafe_allow_html=True)
components.html(table_html, height=1100)

# ── Footer ─────────────────────────────────────────────────────────────────────
footer_bg = "linear-gradient(135deg, #1E3A5F 0%, #0F2A4A 100%)"
footer_text = "#94A3B8"
footer_link = "#60A5FA"
footer_border = "#334155"

footer_html = f"""
<style>
.footer-badge {{
    display: inline-block;
    background: {HEADER};
    color: {HEADER_TEXT};
    font-size: 0.65rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 99px;
    margin-right: 12px;
    border: 1px solid {HEADER_BORDER};
}}
</style>
<div style="padding: 16px 20px; background: {footer_bg}; border-radius: 8px; border: 1px solid {footer_border}; text-align: right; font-size: 0.8rem;">
  <span class="footer-badge">Auto</span>
  <span style="color: {footer_text};">Metrics pull live from Utilization Check-in &amp; Projects Weekly Check-in</span>
  <br/>
  <a href="/scorecard_entry" style="color: {footer_link}; text-decoration: none; font-weight: 600; margin-top: 8px; display: inline-block;">✏️  Edit this week →</a>
</div>
"""
components.html(footer_html, height=100)
