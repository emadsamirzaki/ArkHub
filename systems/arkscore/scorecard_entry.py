"""
systems/arkscore/scorecard_entry.py
Weekly L10 scorecard data-entry form.
"""
from __future__ import annotations

import streamlit as st
import datetime

from systems.arkscore.utils.entry_store import (
    current_week_label,
    get_entries_for_week,
    week_label_from_date,
)
from systems.arkscore.utils.project_store import load_projects
from systems.arkscore.utils.scorecard_store import get_entry, upsert_entry
from systems.arkscore.utils.utilization_store import get_report
from systems.arkscore.utils.constants import (
    COLOR_BG, COLOR_CARD, COLOR_BORDER, COLOR_TEXT, COLOR_MUTED,
)

st.markdown(f"""
<style>
.stApp {{ background-color: {COLOR_BG}; }}

/* Expander styling */
.streamlit-expanderHeader {{
    background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
    border-radius: 12px !important;
    border: 1px solid #334155 !important;
    padding: 16px !important;
    margin-bottom: 12px !important;
}}

.streamlit-expanderHeader:hover {{
    background: linear-gradient(135deg, #334155 0%, #1E293B 100%) !important;
    border-color: #64748B !important;
}}

.stExpanderHeader {{
    color: {COLOR_TEXT} !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
}}

/* Content inside expanders */
.streamlit-expander {{
    background: {COLOR_CARD} !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
}}

/* Input field styling */
.stNumberInput > div > div > input,
.stTextArea textarea {{
    background-color: #0F172A !important;
    color: #E2E8F0 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    padding: 10px 12px !important;
    font-size: 0.95rem !important;
}}

.stNumberInput > div > div > input:focus,
.stTextArea textarea:focus {{
    background-color: #1E293B !important;
    border-color: #60A5FA !important;
    box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.1) !important;
}}

/* Labels styling */
.stNumberInput label,
.stTextArea label {{
    color: #E2E8F0 !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    margin-bottom: 6px !important;
}}

/* Section header styling inside expanders */
.sc-metric-label {{
    font-size: 0.9rem;
    font-weight: 700;
    color: #60A5FA;
    margin-bottom: 12px;
    display: block;
    padding-bottom: 8px;
    border-bottom: 2px solid #1E3A5F;
}}

.sc-auto-badge {{
    display: inline-block;
    background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%);
    color: #60A5FA;
    font-size: 0.65rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 99px;
    margin-left: 8px;
    vertical-align: middle;
    border: 1px solid #3B82F6;
}}

.sc-auto-src {{
    font-size: 0.75rem;
    color: #94A3B8;
    margin-top: 6px;
    display: block;
    padding: 8px 12px;
    background: rgba(96, 165, 250, 0.05);
    border-left: 3px solid #60A5FA;
    border-radius: 4px;
}}

/* Section title colors with gradient effect */
.section-bd {{ color: #3B82F6; font-weight: 700; }}
.section-health {{ color: #10B981; font-weight: 700; }}
.section-financial {{ color: #F59E0B; font-weight: 700; }}
.section-people {{ color: #EC4899; font-weight: 700; }}
.section-ops {{ color: #06B6D4; font-weight: 700; }}
.section-ai {{ color: #8B5CF6; font-weight: 700; }}

/* Button styling */
.stFormSubmitButton > button {{
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 12px 24px !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
}}

.stFormSubmitButton > button:hover {{
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3) !important;
}}

/* Column styling */
.stColumn {{
    gap: 12px;
}}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style="background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%); padding: 24px; border-radius: 12px; margin-bottom: 24px; border: 1px solid #3B82F6;">
    <h1 style="color: #60A5FA; margin: 0 0 8px 0; font-size: 2rem;">📝 L10 Weekly Scorecard Entry</h1>
    <p style="color: #93C5FD; margin: 0; font-size: 0.95rem;">Enter weekly metrics for the L10 leadership meeting</p>
</div>
""", unsafe_allow_html=True)

# ── Week picker ────────────────────────────────────────────────────────────────
today = datetime.date.today()
last_week = today - datetime.timedelta(days=7)
week_label = current_week_label()

st.markdown("""
<style>
.week-picker-container {
    background: linear-gradient(135deg, #1E3A5F 0%, #0F2A4A 100%);
    padding: 16px 20px;
    border-radius: 10px;
    border: 1px solid #3B82F6;
    margin-bottom: 20px;
}
.week-label {
    color: #60A5FA;
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}
.week-value {
    color: #E2E8F0;
    font-size: 1.2rem;
    font-weight: 700;
}
</style>
<div class="week-picker-container">
    <div class="week-label">📅 Select Week</div>
</div>
""", unsafe_allow_html=True)

col_wk, col_spacer = st.columns([2, 3])
with col_wk:
    picked_date = st.date_input("Pick any day in the week", value=last_week, label_visibility="collapsed")
    week_label = week_label_from_date(picked_date)
    st.markdown(f'<div class="week-value">📌 {week_label}</div>', unsafe_allow_html=True)

# Load existing saved data for this week (pre-fill form)
existing = get_entry(week_label)
d = existing["data"] if existing else {}

# ── Auto-computed: Client Health (#4) ─────────────────────────────────────────
entries = get_entries_for_week(week_label)
active_projects = [p for p in load_projects() if p["status"] == "Active"]
entry_map = {e["project_id"]: e for e in entries}
checked = [p for p in active_projects if p["id"] in entry_map]
on_track = sum(1 for p in checked if entry_map[p["id"]]["health_status"] == "On Track")
client_health_pct = round(on_track / len(checked) * 100, 1) if checked else None

# ── Auto-computed: Utilization (#9) ───────────────────────────────────────────
report = get_report(week_label)
utilization_pct = None
if report:
    per_user: dict[str, float] = {}
    for row in report["raw_rows"]:
        name = row.get("User", "")
        per_user[name] = per_user.get(name, 0) + float(row.get("Duration (decimal)", 0))
    if per_user:
        utilization_pct = round(sum(h / 35.0 * 100 for h in per_user.values()) / len(per_user), 1)

# ── Form ───────────────────────────────────────────────────────────────────────
with st.form("scorecard_entry_form"):
    st.markdown('<div style="margin: 8px 0;"></div>', unsafe_allow_html=True)

    # BD & Pipeline ─────────────────────────────────────────────────────────────
    with st.expander("🔵 BD & Pipeline", expanded=False):
        st.markdown("**#1 · Active Pipeline Opportunities**")
        c1, c2, c3 = st.columns(3)
        pipeline_count    = c1.number_input("Count (#)", min_value=0, step=1,  value=int(d.get("pipeline_count", 0) or 0))
        pipeline_value    = c2.number_input("Total Value ($K)", min_value=0.0, step=10.0, value=float(d.get("pipeline_value", 0.0) or 0.0))
        pipeline_ai_pct   = c3.number_input("AI %", min_value=0.0, max_value=100.0, step=1.0, value=float(d.get("pipeline_ai_pct", 0.0) or 0.0))

        st.markdown("**#2 · Conversations with New Qualified Leads**")
        qualified_leads   = st.number_input("Conversations this week", min_value=0, step=1, value=int(d.get("qualified_leads", 0) or 0))

        st.markdown("**#3 · Closed-Won Opportunities (Rolling 8 Weeks)**")
        c4, c5 = st.columns(2)
        closed_won_bd     = c4.number_input("BD New", min_value=0, step=1, value=int(d.get("closed_won_bd", 0) or 0))
        closed_won_upsell = c5.number_input("Team Upselling", min_value=0, step=1, value=int(d.get("closed_won_upsell", 0) or 0))

    # Client Health (auto, but editable) ────────────────────────────────────────
    with st.expander("🟢 Client Health", expanded=False):
        st.markdown(f'**#4 · Client Health % Green** <span class="sc-auto-badge">Auto</span>', unsafe_allow_html=True)

        default_health = client_health_pct
        if default_health is None and "client_health_pct" in d:
            default_health = float(d.get("client_health_pct", 0) or 0)
        elif default_health is None:
            default_health = 0.0

        client_health_pct_input = st.number_input(
            "Client Health %",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            value=default_health,
            label_visibility="collapsed"
        )

        if client_health_pct is not None:
            st.caption(f"📊 From Projects Weekly Check-in: {on_track} of {len(checked)} projects On Track")
        else:
            st.caption(f"⚠️  No check-in entries found — auto-calculate by submitting data via Projects Weekly Check-in first")

    # Financial ─────────────────────────────────────────────────────────────────
    with st.expander("💰 Financial", expanded=False):
        st.markdown("**#5 · Rolling 12-Week Collection (% from target)**")
        collection_pct    = st.number_input("Collection %", min_value=0.0, step=1.0, value=float(d.get("collection_pct", 0.0) or 0.0))

        st.markdown("**#6 · GV Financial Dependency (Rolling 12-Week %)**")
        gv_dependency_pct = st.number_input("GV Dependency %", min_value=0.0, max_value=100.0, step=1.0, value=float(d.get("gv_dependency_pct", 0.0) or 0.0))

    # People ────────────────────────────────────────────────────────────────────
    with st.expander("👥 People", expanded=False):
        st.markdown("**#7 · Employee Red Flags**")
        c6, c7, c8 = st.columns(3)
        red_flags_6 = c6.number_input("#6s (low risk)",   min_value=0, step=1, value=int(d.get("red_flags_6", 0) or 0))
        red_flags_5 = c7.number_input("#5s (medium)",     min_value=0, step=1, value=int(d.get("red_flags_5", 0) or 0))
        red_flags_4 = c8.number_input("#4 or less (high)", min_value=0, step=1, value=int(d.get("red_flags_4", 0) or 0))

        st.markdown("**#8 · Process Violations (Rolling 4 Weeks)**")
        process_violations = st.number_input("People with >4 violations", min_value=0, step=1, value=int(d.get("process_violations", 0) or 0))

    # Operations (auto, but editable) ───────────────────────────────────────────
    with st.expander("⚙️ Operations", expanded=False):
        st.markdown(f'**#9 · Utilization %** <span class="sc-auto-badge">Auto</span>', unsafe_allow_html=True)

        default_util = utilization_pct
        if default_util is None and "utilization_pct" in d:
            default_util = float(d.get("utilization_pct", 0) or 0)
        elif default_util is None:
            default_util = 0.0

        utilization_pct_input = st.number_input(
            "Utilization %",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            value=default_util,
            label_visibility="collapsed"
        )

        if utilization_pct is not None:
            st.caption(f"📊 From Clockify data for this week")
        else:
            st.caption(f"⚠️  No utilization report for this week — auto-calculate by uploading via Utilization Check-in first")

    # AI & Delivery ─────────────────────────────────────────────────────────────
    with st.expander("🤖 AI & Delivery", expanded=False):
        st.markdown("**#10 · Arkdev AI Transformation — Projects Adoption**")

        # AI Adoption % and Hint side by side
        col_ai_pct, col_ai_hint = st.columns([1.5, 2.5])

        with col_ai_pct:
            st.markdown("**AI Adoption %**")
            ai_adoption_pct = st.number_input(
                "AI Adoption %",
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                value=float(d.get("ai_adoption_pct", 0.0) or 0.0),
                label_visibility="collapsed"
            )
            st.caption("% of projects using Claude")

        with col_ai_hint:
            st.markdown("**Details / Context**")
            ai_adoption_hint = st.text_area(
                "Add hint for this metric",
                value=d.get("ai_adoption_hint", "") or "",
                height=80,
                placeholder="e.g. 3-5 projects now using Claude, team upskilled in prompt engineering...",
                label_visibility="collapsed"
            )

    # Save ──────────────────────────────────────────────────────────────────────
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    submitted = st.form_submit_button("💾  Save Scorecard Entry", use_container_width=True, type="primary")

if submitted:
    payload = {
        "pipeline_count":     pipeline_count,
        "pipeline_value":     pipeline_value,
        "pipeline_ai_pct":    pipeline_ai_pct,
        "qualified_leads":    qualified_leads,
        "closed_won_bd":      closed_won_bd,
        "closed_won_upsell":  closed_won_upsell,
        "client_health_pct":  client_health_pct_input,
        "collection_pct":     collection_pct,
        "gv_dependency_pct":  gv_dependency_pct,
        "red_flags_6":        red_flags_6,
        "red_flags_5":        red_flags_5,
        "red_flags_4":        red_flags_4,
        "process_violations": process_violations,
        "utilization_pct":    utilization_pct_input,
        "ai_adoption_pct":    ai_adoption_pct,
        "ai_adoption_hint":   ai_adoption_hint.strip() or None,
    }
    upsert_entry(week_label, payload)
    st.success(f"Saved scorecard for **{week_label}**")
