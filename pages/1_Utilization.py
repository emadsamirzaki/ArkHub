"""
pages/1_Utilization.py
-----------------------
Module 1 — Utilization %
Full upload + dashboard view for the ArkScore L10 Scorecard.
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Ensure project root is on sys.path so `utils` is importable when Streamlit
# runs page files directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.constants import (  # noqa: E402
    COLOR_BORDER,
    COLOR_CARD,
    COLOR_CRITICAL,
    COLOR_MUTED,
    COLOR_ON_TARGET,
    COLOR_WATCH,
    ON_TARGET_THRESHOLD,
    STATUS_CRITICAL,
    STATUS_ON_TARGET,
    STATUS_WATCH,
    TARGET_HOURS,
    WATCH_THRESHOLD,
)
from utils.parse_clockify import (  # noqa: E402
    calculate_utilization,
    get_project_breakdown,
    get_week_label,
    parse_clockify_csv,
)


# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* ── Metric cards ──────────────────────────── */
.metric-card {
    background: #1E293B;
    border-radius: 14px;
    padding: 22px 18px;
    text-align: center;
    border: 1px solid #334155;
    min-height: 116px;
}
.metric-label {
    color: #94A3B8;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
    margin: 0 0 10px 0;
}
.metric-value {
    font-size: 2.15rem;
    font-weight: 700;
    margin: 0;
    line-height: 1.1;
}
.metric-sub {
    color: #64748B;
    font-size: 0.76rem;
    margin: 6px 0 0 0;
}

/* ── Section headings ──────────────────────── */
.section-heading {
    font-size: 0.8rem;
    font-weight: 700;
    color: #94A3B8;
    margin: 32px 0 14px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #334155;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* ── Week badge ────────────────────────────── */
.week-badge {
    display: inline-block;
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 5px 12px;
    color: #94A3B8;
    font-size: 0.85rem;
    font-weight: 500;
    margin-bottom: 4px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Sidebar module status ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown("**Module Status**")
    st.markdown("✅ Utilization % — **Active**")
    for m in [
        "Operational Health",
        "Client Health",
        "Process Compliance",
        "Revenue per Head",
        "BD Conversations",
        "Rock Completion",
    ]:
        st.markdown(f"🔒 {m}")


# ── Helper: status colour ─────────────────────────────────────────────────────
def _status_color(util_pct: float) -> str:
    if util_pct >= ON_TARGET_THRESHOLD:
        return COLOR_ON_TARGET
    if util_pct >= WATCH_THRESHOLD:
        return COLOR_WATCH
    return COLOR_CRITICAL


# ── Helper: render a single metric card ──────────────────────────────────────
def _metric_card(
    title: str, value: str, subtitle: str = "", color: str = "#F8FAFC"
) -> None:
    sub_html = f'<p class="metric-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
<div class="metric-card">
  <p class="metric-label">{title}</p>
  <p class="metric-value" style="color:{color};">{value}</p>
  {sub_html}
</div>""",
        unsafe_allow_html=True,
    )


# ── Helper: build Plotly horizontal bar chart ─────────────────────────────────
def _utilization_chart(util_df: pd.DataFrame) -> go.Figure:
    df_s = util_df.sort_values("Utilization %", ascending=True)

    bar_colors = [
        (
            COLOR_ON_TARGET
            if v >= ON_TARGET_THRESHOLD
            else (COLOR_WATCH if v >= WATCH_THRESHOLD else COLOR_CRITICAL)
        )
        for v in df_s["Utilization %"]
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_s["Utilization %"],
            y=df_s["Name"],
            orientation="h",
            marker_color=bar_colors,
            text=[f"{v:.1f}%" for v in df_s["Utilization %"]],
            textposition="outside",
            cliponaxis=False,
        )
    )
    fig.add_vline(
        x=80,
        line_dash="dash",
        line_color="#94A3B8",
        line_width=1.5,
        annotation_text="Target (80%)",
        annotation_position="top",
        annotation_font_color="#94A3B8",
        annotation_font_size=11,
    )
    fig.update_layout(
        xaxis=dict(
            range=[0, 130],
            title="Utilization %",
            color="#94A3B8",
            gridcolor="#334155",
            ticksuffix="%",
            zeroline=False,
        ),
        yaxis=dict(title="", color="#CBD5E1"),
        plot_bgcolor="#1E293B",
        paper_bgcolor="#1E293B",
        font=dict(color="#F8FAFC", family="Inter, sans-serif", size=13),
        margin=dict(l=20, r=90, t=30, b=40),
        height=max(320, len(df_s) * 52 + 90),
        showlegend=False,
    )
    return fig


# ── Upload view ───────────────────────────────────────────────────────────────
def _render_upload_view() -> None:
    st.markdown("## Upload Clockify Report")
    st.markdown(
        "Export a **Detailed Report** from Clockify "
        "(Reports → Detailed → Export as CSV), then upload it below."
    )

    uploaded = st.file_uploader(
        "Clockify Detailed Report (.csv)",
        type=["csv"],
        label_visibility="collapsed",
    )

    if uploaded is not None:
        with st.spinner("Parsing report…"):
            try:
                df = parse_clockify_csv(uploaded)
            except ValueError as exc:
                st.error(f"❌ {exc}")
                return
            except Exception as exc:
                st.error(f"❌ Failed to read file: {exc}")
                return

        auto_label = get_week_label(df)
        week_label = st.text_input(
            "Week Label",
            value=auto_label,
            help="Auto-detected from the earliest Start Date. Edit as needed.",
        )

        col_btn, _ = st.columns([2, 5])
        with col_btn:
            if st.button("Load Dashboard →", type="primary", use_container_width=True):
                st.session_state["ark_df"]        = df
                st.session_state["ark_week"]      = week_label
                st.session_state["ark_util"]      = calculate_utilization(df)
                st.session_state["ark_breakdown"] = get_project_breakdown(df)
                st.rerun()

    else:
        st.markdown("---")
        st.markdown("**Expected CSV format — key columns shown:**")
        sample = pd.DataFrame(
            {
                "Project":            ["Website Redesign", "Internal Meeting", "API Development"],
                "Client":             ["Acme Corp", "",          "TechCorp"],
                "Description":        ["Homepage layout", "Weekly sync", "Auth endpoint"],
                "User":               ["Alice", "Bob",    "Alice"],
                "Billable":           ["Yes",   "No",     "Yes"],
                "Start Date":         ["04/28/2026", "04/28/2026", "04/29/2026"],
                "Duration (decimal)": [2.50, 1.00, 3.25],
            }
        )
        st.dataframe(sample, use_container_width=True, hide_index=True)
        st.caption(
            "The full Clockify export includes additional columns. "
            "The above shows the ones used for utilisation calculations."
        )


# ── Dashboard view ────────────────────────────────────────────────────────────
def _render_dashboard_view() -> None:
    df: pd.DataFrame        = st.session_state["ark_df"]
    util_df: pd.DataFrame   = st.session_state["ark_util"]
    breakdown: dict         = st.session_state["ark_breakdown"]
    week_label: str         = st.session_state.get("ark_week", "")

    # ── Page header ───────────────────────────────────────────────────────────
    hdr_l, hdr_r = st.columns([5, 1])
    with hdr_l:
        st.markdown(
            f"<span class='week-badge'>📅 {week_label}</span>",
            unsafe_allow_html=True,
        )
        st.markdown("# Utilization Dashboard")
    with hdr_r:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("⬆ New Upload", use_container_width=True):
            for k in ("ark_df", "ark_week", "ark_util", "ark_breakdown"):
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("---")

    # ── Aggregate metrics ─────────────────────────────────────────────────────
    total_hrs    = float(df["Duration (decimal)"].sum())
    bill_hrs     = float(df[df["Billable"] == "Yes"]["Duration (decimal)"].sum())
    non_bill_hrs = float(df[df["Billable"] == "No"]["Duration (decimal)"].sum())
    team_util    = float(util_df["Utilization %"].mean()) if len(util_df) else 0.0

    bill_pct     = (bill_hrs     / total_hrs * 100) if total_hrs else 0.0
    non_bill_pct = (non_bill_hrs / total_hrs * 100) if total_hrs else 0.0

    # Guard: empty dataset
    if len(util_df) == 0:
        st.warning("No team members found in this file. Please check the CSV and try again.")
        return

    # ── Section 1: Summary cards ──────────────────────────────────────────────
    st.markdown(
        '<p class="section-heading">Summary</p>', unsafe_allow_html=True
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _metric_card(
            "Team Utilization",
            f"{team_util:.1f}%",
            f"{len(util_df)} members · target {int(TARGET_HOURS)} h",
            _status_color(team_util),
        )
    with c2:
        _metric_card(
            "Total Billable",
            f"{bill_pct:.1f}%",
            f"{bill_hrs:.1f} hrs",
        )
    with c3:
        _metric_card(
            "Total Non-Billable",
            f"{non_bill_pct:.1f}%",
            f"{non_bill_hrs:.1f} hrs",
        )
    with c4:
        _metric_card(
            "Total Hours Logged",
            f"{total_hrs:.1f}",
            "hours this week",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 2: Team utilisation chart ─────────────────────────────────────
    st.markdown(
        '<p class="section-heading">Team Utilization Chart</p>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(_utilization_chart(util_df), use_container_width=True)

    # ── Section 3: Detail table ───────────────────────────────────────────────
    st.markdown(
        '<p class="section-heading">Team Details</p>', unsafe_allow_html=True
    )
    table_cols = [
        "Rank", "Name", "Total Hrs", "Billable Hrs",
        "Non-Bill Hrs", "Billable %", "Utilization %", "Status",
    ]
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
                "Util %", min_value=0, max_value=120, format="%.1f%%"
            ),
            "Status":        st.column_config.TextColumn("Status"),
        },
        use_container_width=True,
        hide_index=True,
    )

    # ── Section 4: Per-person expandable breakdown ────────────────────────────
    st.markdown(
        '<p class="section-heading">Per-Person Breakdown</p>',
        unsafe_allow_html=True,
    )
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
                proj_total = proj_info["total_hours"]
                st.markdown(f"**📁 {proj_name}** &nbsp; `{proj_total:.2f} hrs`")

                task_rows = [
                    {
                        "":            "💰" if t["billable"] else "⬜",
                        "Description": t["description"],
                        "Hours":       t["hours"],
                        "Billable":    "Yes" if t["billable"] else "No",
                    }
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


# ── Entry point ───────────────────────────────────────────────────────────────
if st.session_state.get("ark_df") is None:
    _render_upload_view()
else:
    _render_dashboard_view()
