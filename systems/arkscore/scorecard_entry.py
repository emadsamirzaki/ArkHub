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
from systems.arkscore.utils.scorecard_store import delete_entry, get_all_weeks, get_entry, upsert_entry
from systems.arkscore.utils.utilization_store import get_report
from systems.utils import ui

st.title("📝 L10 Weekly Scorecard Entry")
st.caption("Enter weekly metrics for the L10 leadership meeting")
st.divider()

# ── Week picker ────────────────────────────────────────────────────────────────
today = datetime.date.today()
last_week = today - datetime.timedelta(days=7)
week_label = current_week_label()

st.markdown("📅 **Select Week**")
col_wk, col_spacer = st.columns([2, 3])
with col_wk:
    picked_date = st.date_input("Pick any day in the week", value=last_week, label_visibility="collapsed")
    week_label = week_label_from_date(picked_date)
    st.markdown(f"📌 **{week_label}**")

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
        st.markdown("**#4 · Client Health % Green**　:blue-badge[Auto]")

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
        st.markdown("**#9 · Team Utilization & Billable**　:blue-badge[Auto]")

        # Calculate both metrics from utilization report (raw Clockify data)
        team_util = None
        total_bill = None
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
                    team_util = round(sum(utilizations) / len(utilizations), 1)
                if billables:
                    total_bill = round(sum(billables) / len(billables), 1)

        # Team Utilization input
        default_team_util = team_util
        if default_team_util is None and "team_utilization_pct" in d:
            default_team_util = float(d.get("team_utilization_pct", 0) or 0)
        elif default_team_util is None:
            default_team_util = 0.0

        col_util, col_bill = st.columns(2)
        with col_util:
            st.markdown("**Team Utilization %**")
            team_util_input = st.number_input(
                "Team Utilization %",
                min_value=0.0,
                max_value=200.0,
                step=0.1,
                value=default_team_util,
                label_visibility="collapsed"
            )

        # Total Billable input
        default_total_bill = total_bill
        if default_total_bill is None and "total_billable_pct" in d:
            default_total_bill = float(d.get("total_billable_pct", 0) or 0)
        elif default_total_bill is None:
            default_total_bill = 0.0

        with col_bill:
            st.markdown("**Total Billable %**")
            total_bill_input = st.number_input(
                "Total Billable %",
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                value=default_total_bill,
                label_visibility="collapsed"
            )

        if team_util is not None or total_bill is not None:
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
    st.markdown("")
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
        "team_utilization_pct": team_util_input,
        "total_billable_pct":   total_bill_input,
        "ai_adoption_pct":    ai_adoption_pct,
        "ai_adoption_hint":   ai_adoption_hint.strip() or None,
    }
    upsert_entry(week_label, payload)
    st.success(f"Saved scorecard for **{week_label}**")

# ── Saved Weeks ───────────────────────────────────────────────────────────────
ui.section("Saved Weeks")

saved_weeks = get_all_weeks()
if not saved_weeks:
    st.info("No scorecard entries saved yet.")
else:
    sh1, sh2, sh3 = st.columns([4, 3, 1])
    sh1.markdown("**Week**")
    sh2.markdown("**Submitted At**")
    sh3.markdown("")
    st.divider()

    for wk in saved_weeks:
        sc_entry = get_entry(wk)
        submitted_at_fmt = ""
        if sc_entry:
            try:
                submitted_at_fmt = datetime.datetime.fromisoformat(
                    sc_entry["submitted_at"]
                ).strftime("%d %b %Y %H:%M")
            except Exception:
                submitted_at_fmt = sc_entry.get("submitted_at", "")

        wc1, wc2, wc3 = st.columns([4, 3, 1])
        wc1.markdown(wk)
        wc2.markdown(submitted_at_fmt)
        if wc3.button("Delete", key=f"del_sc_{wk}", use_container_width=True):
            st.session_state[f"confirm_del_sc_{wk}"] = True

        if st.session_state.get(f"confirm_del_sc_{wk}"):
            st.warning(f"Delete scorecard entry for **{wk}**? This cannot be undone.")
            ok_col, cancel_col, _ = st.columns([1, 1, 4])
            if ok_col.button("Yes, delete", key=f"yes_del_sc_{wk}", type="primary"):
                delete_entry(wk)
                st.session_state.pop(f"confirm_del_sc_{wk}", None)
                st.success(f"Deleted scorecard for {wk}.")
                st.rerun()
            if cancel_col.button("Cancel", key=f"cancel_del_sc_{wk}"):
                st.session_state.pop(f"confirm_del_sc_{wk}", None)
                st.rerun()
