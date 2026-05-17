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
    TARGET_HOURS,
    WATCH_THRESHOLD,
)
from systems.arkscore.utils.parse_clockify import calculate_utilization, get_project_breakdown
from systems.arkscore.utils.utilization_store import get_all_reports, get_all_week_labels, get_report

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.metric-card {
    background: #1E293B; border-radius: 14px; padding: 22px 18px;
    text-align: center; border: 1px solid #334155; min-height: 116px;
}
.metric-label {
    color: #94A3B8; font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 0.1em; font-weight: 600; margin: 0 0 10px 0;
}
.metric-value { font-size: 2.15rem; font-weight: 700; margin: 0; line-height: 1.1; }
.metric-sub   { color: #64748B; font-size: 0.76rem; margin: 6px 0 0 0; }
.section-heading {
    font-size: 0.8rem; font-weight: 700; color: #94A3B8;
    margin: 32px 0 14px 0; padding-bottom: 8px;
    border-bottom: 1px solid #334155;
    text-transform: uppercase; letter-spacing: 0.1em;
}
.week-badge {
    display: inline-block; background: #1E293B; border: 1px solid #334155;
    border-radius: 8px; padding: 5px 12px; color: #94A3B8;
    font-size: 0.85rem; font-weight: 500; margin-bottom: 4px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _status_color(util_pct: float) -> str:
    if util_pct >= ON_TARGET_THRESHOLD:
        return COLOR_ON_TARGET
    if util_pct >= WATCH_THRESHOLD:
        return COLOR_WATCH
    return COLOR_CRITICAL


def _metric_card(title: str, value: str, subtitle: str = "", color: str = "#F8FAFC") -> None:
    sub_html = f'<p class="metric-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""<div class="metric-card">
  <p class="metric-label">{title}</p>
  <p class="metric-value" style="color:{color};">{value}</p>
  {sub_html}
</div>""",
        unsafe_allow_html=True,
    )


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
    fig.add_vline(
        x=80, line_dash="dash", line_color="#94A3B8", line_width=1.5,
        annotation_text="Target (80%)", annotation_position="top",
        annotation_font_color="#94A3B8", annotation_font_size=11,
    )
    fig.update_layout(
        xaxis=dict(range=[0, 130], title="Utilization %", color="#94A3B8",
                   gridcolor="#334155", ticksuffix="%", zeroline=False),
        yaxis=dict(title="", color="#CBD5E1"),
        plot_bgcolor="#1E293B", paper_bgcolor="#1E293B",
        font=dict(color="#F8FAFC", family="Inter, sans-serif", size=13),
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


def _wow_table(util_now: pd.DataFrame, report_prev: dict) -> None:
    df_prev   = _df_from_store(report_prev)
    util_prev = calculate_utilization(df_prev)
    prev_map  = {r["Name"]: r["Utilization %"] for _, r in util_prev.iterrows()}

    rows = []
    for _, row in util_now.iterrows():
        name = row["Name"]
        if name not in prev_map:
            continue
        this_w = row["Utilization %"]
        last_w = prev_map[name]
        delta  = this_w - last_w
        if delta > 0:
            arrow, color = f"▲ +{delta:.1f}%", COLOR_ON_TARGET
        elif delta < 0:
            arrow, color = f"▼ {delta:.1f}%", COLOR_CRITICAL
        else:
            arrow, color = "—", "#94A3B8"
        rows.append({"Name": name, "This Week": f"{this_w:.1f}%",
                     "Last Week": f"{last_w:.1f}%",
                     "_delta": delta, "_arrow": arrow, "_color": color})

    if not rows:
        st.info("No team members in common with last week.")
        return

    rows.sort(key=lambda r: -r["_delta"])
    html_rows = "".join(
        f"<tr>"
        f"<td style='padding:6px 12px'>{r['Name']}</td>"
        f"<td style='padding:6px 12px;text-align:center'>{r['This Week']}</td>"
        f"<td style='padding:6px 12px;text-align:center'>{r['Last Week']}</td>"
        f"<td style='padding:6px 12px;text-align:center;color:{r['_color']};font-weight:600'>"
        f"{r['_arrow']}</td></tr>"
        for r in rows
    )
    st.markdown(
        f"""<table style='width:100%;border-collapse:collapse;font-size:.88rem;
                          font-family:Inter,sans-serif;color:#E2E8F0;'>
  <thead><tr style='border-bottom:1px solid #334155;color:#94A3B8;font-size:.75rem;
                    text-transform:uppercase;letter-spacing:.05em;'>
    <th style='padding:6px 12px;text-align:left'>Name</th>
    <th style='padding:6px 12px;text-align:center'>This Week</th>
    <th style='padding:6px 12px;text-align:center'>Last Week</th>
    <th style='padding:6px 12px;text-align:center'>Change</th>
  </tr></thead>
  <tbody>{html_rows}</tbody>
</table>""",
        unsafe_allow_html=True,
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.markdown("# 📊 Utilization Dashboard")
    st.markdown("---")

    week_labels = get_all_week_labels()
    all_reports = get_all_reports()

    if not week_labels:
        st.info(
            "No data yet. Go to **ArkScore → Utilization Check-in** to upload a Clockify report."
        )
        return

    # ── Week selector ─────────────────────────────────────────────────────────
    col_sel, col_badge, _ = st.columns([2, 3, 2])
    with col_sel:
        default_week = st.session_state.pop("util_selected_week", week_labels[0])
        if default_week not in week_labels:
            default_week = week_labels[0]
        sel_idx    = week_labels.index(default_week)
        week_label = st.selectbox("Select Week", week_labels, index=sel_idx)
    with col_badge:
        st.markdown(
            f"<div style='padding-top:28px'>"
            f"<span class='week-badge'>📅 {week_label}</span></div>",
            unsafe_allow_html=True,
        )

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

    # ── Aggregates ────────────────────────────────────────────────────────────
    total_hrs    = float(df["Duration (decimal)"].sum())
    bill_hrs     = float(df[df["Billable"] == "Yes"]["Duration (decimal)"].sum())
    non_bill_hrs = float(df[df["Billable"] == "No"]["Duration (decimal)"].sum())
    team_util    = float(util_df["Utilization %"].mean())
    bill_pct     = (bill_hrs / total_hrs * 100) if total_hrs else 0.0
    non_bill_pct = (non_bill_hrs / total_hrs * 100) if total_hrs else 0.0

    # ── Section 1: Summary cards ──────────────────────────────────────────────
    st.markdown('<p class="section-heading">Summary</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _metric_card("Team Utilization", f"{team_util:.1f}%",
                     f"{len(util_df)} members · target {int(TARGET_HOURS)} h",
                     _status_color(team_util))
    with c2:
        _metric_card("Total Billable", f"{bill_pct:.1f}%", f"{bill_hrs:.1f} hrs")
    with c3:
        _metric_card("Total Non-Billable", f"{non_bill_pct:.1f}%", f"{non_bill_hrs:.1f} hrs")
    with c4:
        _metric_card("Total Hours Logged", f"{total_hrs:.1f}", "hours this week")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 2: Chart ──────────────────────────────────────────────────────
    st.markdown('<p class="section-heading">Team Utilization Chart</p>',
                unsafe_allow_html=True)
    st.markdown(
        """<div style='display:flex;gap:20px;align-items:center;margin-bottom:10px;
                       font-size:0.78rem;font-family:Inter,sans-serif;color:#94A3B8;'>
  <span><span style='color:#22C55E;font-size:1rem;'>●</span>&nbsp;<b style='color:#CBD5E1;'>On Target</b>&nbsp;≥ 80%</span>
  <span><span style='color:#F59E0B;font-size:1rem;'>●</span>&nbsp;<b style='color:#CBD5E1;'>Watch</b>&nbsp;60 – 79%</span>
  <span><span style='color:#EF4444;font-size:1rem;'>●</span>&nbsp;<b style='color:#CBD5E1;'>Critical</b>&nbsp;&lt; 60%</span>
  <span style='margin-left:6px;'>· Target = 35 hrs / week</span>
</div>""",
        unsafe_allow_html=True,
    )
    st.plotly_chart(_utilization_chart(util_df), use_container_width=True)

    # ── Section 3: Detail table ───────────────────────────────────────────────
    st.markdown('<p class="section-heading">Team Details</p>', unsafe_allow_html=True)
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
    st.markdown('<p class="section-heading">Per-Person Breakdown</p>',
                unsafe_allow_html=True)
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
            st.markdown(
                f'<p class="section-heading">Week-over-Week Comparison '
                f'<span style="font-weight:400;color:#64748B;text-transform:none;'
                f'font-size:.75rem;">vs {prev_report["week_label"]}</span></p>',
                unsafe_allow_html=True,
            )
            _wow_table(util_df, prev_report)


main()
