"""
systems/arkscore/utilization_dashboard.py
Utilization % Dashboard — week selector + WoW comparison.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from systems.arkscore.utils.constants import (
    COLOR_CRITICAL,
    COLOR_ON_TARGET,
    COLOR_WATCH,
    ON_TARGET_THRESHOLD,
    STATUS_CRITICAL,
    TARGET_HOURS,
    WATCH_THRESHOLD,
)
from systems.arkscore.utils.parse_clockify import calculate_utilization, get_project_breakdown
from systems.arkscore.utils.utilization_store import get_all_reports, get_all_week_labels, get_report
from systems.people.utils.employee_store import get_active_employees
from systems.utils import ui


# ── Helpers ───────────────────────────────────────────────────────────────────

def _status_label(util_pct: float) -> str:
    if util_pct >= ON_TARGET_THRESHOLD:
        return "On Target"
    if util_pct >= WATCH_THRESHOLD:
        return "Watch"
    return "Critical"


def _utilization_chart(util_df: pd.DataFrame) -> go.Figure:
    df_s = util_df.sort_values("Utilization %", ascending=True)
    bar_colors = [
        COLOR_ON_TARGET if v >= ON_TARGET_THRESHOLD
        else (COLOR_WATCH if v >= WATCH_THRESHOLD else COLOR_CRITICAL)
        for v in df_s["Utilization %"]
    ]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_s["Utilization %"],
        y=df_s["Name"],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v:.1f}%" for v in df_s["Utilization %"]],
        textposition="outside",
        cliponaxis=False,
    ))
    # Neutral mid-gray reads on both the dark and light themes.
    fig.add_vline(
        x=80, line_dash="dash", line_color="#94A3B8", line_width=1.5,
        annotation_text="Target (80%)", annotation_position="top",
        annotation_font_color="#94A3B8", annotation_font_size=11,
    )
    # Transparent backgrounds + theme="streamlit" let the chart inherit the
    # active theme's colours, so it flips with light/dark.
    fig.update_layout(
        xaxis=dict(range=[0, 130], title="Utilization %", ticksuffix="%", zeroline=False),
        yaxis=dict(title=""),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=90, t=30, b=40),
        height=max(320, len(df_s) * 52 + 90),
        showlegend=False,
    )
    return fig


def _df_from_store(report: dict) -> pd.DataFrame:
    df = pd.DataFrame(report["raw_rows"])
    df["Duration (decimal)"] = pd.to_numeric(df["Duration (decimal)"], errors="coerce").fillna(0.0)
    df["Billable"] = df["Billable"].astype(str).str.strip()
    return df


def _wow_table(util_now: pd.DataFrame, report_prev: dict, name_map: dict) -> None:
    df_prev   = _df_from_store(report_prev)
    util_prev = calculate_utilization(df_prev)
    util_prev["Name"] = util_prev["Name"].map(lambda n: name_map.get(n, n))
    prev_map  = {r["Name"]: r["Utilization %"] for _, r in util_prev.iterrows()}

    rows = []
    for _, row in util_now.iterrows():
        name = row["Name"]
        if name not in prev_map:
            continue
        this_w = row["Utilization %"]
        last_w = prev_map[name]
        delta  = this_w - last_w
        arrow  = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
        rows.append({
            "Name": name,
            "This Week": this_w,
            "Last Week": last_w,
            "Change": f"{arrow} {delta:+.1f}%" if delta else "—",
            "_delta": delta,
        })

    if not rows:
        st.info("No team members in common with last week.")
        return

    rows.sort(key=lambda r: -r["_delta"])
    wow_df = pd.DataFrame(rows).drop(columns="_delta")
    st.dataframe(
        wow_df,
        column_config={
            "This Week": st.column_config.NumberColumn("This Week", format="%.1f%%"),
            "Last Week": st.column_config.NumberColumn("Last Week", format="%.1f%%"),
            "Change":    st.column_config.TextColumn("Change"),
        },
        use_container_width=True,
        hide_index=True,
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.title("📊 Utilization Dashboard")
    st.divider()

    week_labels = get_all_week_labels()
    all_reports = get_all_reports()

    if not week_labels:
        st.info(
            "No data yet. Go to **ArkScore → Utilization Check-in** to upload a Clockify report."
        )
        return

    # ── Week selector ─────────────────────────────────────────────────────────
    col_sel, _ = st.columns([2, 3])
    with col_sel:
        default_week = st.session_state.pop("util_selected_week", week_labels[0])
        if default_week not in week_labels:
            default_week = week_labels[0]
        sel_idx    = week_labels.index(default_week)
        week_label = st.selectbox("Select Week", week_labels, index=sel_idx)

    report = get_report(week_label)
    if not report:
        st.error(f"Report for **{week_label}** not found.")
        return

    # ── Build DataFrames ──────────────────────────────────────────────────────
    df        = _df_from_store(report)
    util_df   = calculate_utilization(df)
    breakdown = get_project_breakdown(df)

    if len(util_df) == 0:
        st.warning("No team members found in this report.")
        return

    # ── Employee name mapping + zero-hour injection ───────────────────────────
    active_employees = get_active_employees()
    name_map = {
        (emp.get("clockify_name") or "").strip() or emp["name"]: emp["name"]
        for emp in active_employees
    }

    # Capture orphan Clockify names before renaming
    original_clockify_names = set(util_df["Name"].tolist())
    orphan_clockify = original_clockify_names - set(name_map.keys())

    # Rename Clockify names to canonical employee names
    util_df["Name"] = util_df["Name"].map(lambda n: name_map.get(n, n))

    # Inject zero rows for active employees absent from Clockify this week
    matched_names = set(util_df["Name"].tolist())
    zero_rows = [
        {
            "Name":           emp["name"],
            "Total Hrs":      0.0,
            "Billable Hrs":   0.0,
            "Non-Bill Hrs":   0.0,
            "Utilization %":  0.0,
            "Billable %":     0.0,
            "Non-Billable %": 0.0,
            "Status":         STATUS_CRITICAL,
        }
        for emp in active_employees
        if emp["name"] not in matched_names
    ]
    if zero_rows:
        util_df = (
            pd.concat([util_df.drop(columns=["Rank"]), pd.DataFrame(zero_rows)], ignore_index=True)
            .sort_values("Utilization %", ascending=False)
            .reset_index(drop=True)
        )
        util_df.insert(0, "Rank", range(1, len(util_df) + 1))

    # Warn about Clockify users not matched to any employee
    if orphan_clockify:
        st.warning(
            f"⚠️ {len(orphan_clockify)} Clockify user(s) not matched to any employee: "
            + ", ".join(f"**{n}**" for n in sorted(orphan_clockify))
            + " — go to **People → Employees** and set their Clockify Name."
        )

    # ── Aggregates ────────────────────────────────────────────────────────────
    total_hrs    = float(df["Duration (decimal)"].sum())
    bill_hrs     = float(df[df["Billable"] == "Yes"]["Duration (decimal)"].sum())
    non_bill_hrs = float(df[df["Billable"] == "No"]["Duration (decimal)"].sum())
    team_util    = float(util_df["Utilization %"].mean())
    bill_pct     = (bill_hrs / total_hrs * 100) if total_hrs else 0.0
    non_bill_pct = (non_bill_hrs / total_hrs * 100) if total_hrs else 0.0

    # ── Section 1: Summary cards ──────────────────────────────────────────────
    ui.section("Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Team Utilization", f"{team_util:.1f}%",
                  help=f"{len(util_df)} members · target {int(TARGET_HOURS)} h", border=True)
        st.markdown(ui.status_badge(_status_label(team_util)))
    with c2:
        st.metric("Total Billable", f"{bill_pct:.1f}%", help=f"{bill_hrs:.1f} hrs", border=True)
    with c3:
        st.metric("Total Non-Billable", f"{non_bill_pct:.1f}%", help=f"{non_bill_hrs:.1f} hrs", border=True)
    with c4:
        st.metric("Total Hours Logged", f"{total_hrs:.1f}", help="hours this week", border=True)

    # ── Section 2: Chart ──────────────────────────────────────────────────────
    ui.section("Team Utilization Chart")
    st.markdown(
        ":green-badge[● On Target ≥ 80%]　:orange-badge[● Watch 60–79%]　"
        ":red-badge[● Critical < 60%]　·　Target = 35 hrs / week"
    )
    st.plotly_chart(_utilization_chart(util_df), use_container_width=True, theme="streamlit")

    # ── Section 3: Detail table ───────────────────────────────────────────────
    ui.section("Team Details")
    table_cols = ["Rank", "Name", "Total Hrs", "Billable Hrs",
                  "Non-Bill Hrs", "Billable %", "Utilization %", "Status"]
    st.dataframe(
        util_df[table_cols],
        column_config={
            "Rank":          st.column_config.NumberColumn("#",             width="small"),
            "Name":          st.column_config.TextColumn("Name",           width="medium"),
            "Total Hrs":     st.column_config.NumberColumn("Total Hrs",    format="%.2f h"),
            "Billable Hrs":  st.column_config.NumberColumn("Billable Hrs", format="%.2f h"),
            "Non-Bill Hrs":  st.column_config.NumberColumn("Non-Bill Hrs", format="%.2f h"),
            "Billable %":    st.column_config.NumberColumn("Billable %",   format="%.1f%%"),
            "Utilization %": st.column_config.ProgressColumn(
                "Util %", min_value=0, max_value=120, format="%.1f%%"),
            "Status":        st.column_config.TextColumn("Status"),
        },
        use_container_width=True,
        hide_index=True,
    )

    # ── Section 4: Per-person breakdown ──────────────────────────────────────
    ui.section("Per-Person Breakdown")
    for _, row in util_df.iterrows():
        name      = row["Name"]
        util_pct  = row["Utilization %"]
        status    = row["Status"]
        total     = row["Total Hrs"]
        with st.expander(
            f"{status}  **{name}** — {util_pct:.1f}% utilisation · {total:.2f} hrs logged"
        ):
            user_data = breakdown.get(name)
            if not user_data:
                st.markdown("_No entries found._")
                continue
            for proj_name, proj_info in sorted(
                user_data.items(), key=lambda kv: -kv[1]["total_hours"]
            ):
                st.markdown(f"**📁 {proj_name}** &nbsp; `{proj_info['total_hours']:.2f} hrs`")
                task_rows = [
                    {"": "💰" if t["billable"] else "⬜",
                     "Description": t["description"],
                     "Hours": t["hours"],
                     "Billable": "Yes" if t["billable"] else "No"}
                    for t in proj_info["tasks"]
                ]
                if task_rows:
                    st.dataframe(
                        pd.DataFrame(task_rows),
                        column_config={
                            "":      st.column_config.TextColumn("", width="small"),
                            "Hours": st.column_config.NumberColumn("Hours", format="%.2f h"),
                        },
                        use_container_width=True,
                        hide_index=True,
                    )
                st.markdown("")

    # ── Section 5: Week-over-week comparison ─────────────────────────────────
    if len(all_reports) >= 2:
        current_start = report.get("week_start", "")
        prev_reports  = [r for r in all_reports if r.get("week_start", "") < current_start]
        if prev_reports:
            prev_report = prev_reports[0]
            ui.section("Week-over-Week Comparison")
            st.caption(f"vs {prev_report['week_label']}")
            _wow_table(util_df, prev_report, name_map)


main()
