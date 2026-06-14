"""
systems/arkscore/utilization_checkin.py
Utilization % Weekly Check-in — fetch a week's data from Clockify API.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from systems.arkscore.utils.entry_store import week_bounds, week_label_from_date
from systems.arkscore.utils.parse_clockify import calculate_utilization, parse_clockify_api
from systems.arkscore.utils.utilization_store import (
    delete_report,
    get_all_reports,
    report_exists,
    upsert_report,
)
from systems.project_hours.utils.clockify import (
    ClockifyError,
    fetch_detailed_entries,
    get_active_workspace_id,
    is_configured,
)
from systems.utils import ui


# ── Main ──────────────────────────────────────────────────────────────────────

def _save_df(df: pd.DataFrame, week_label: str, sunday, thursday) -> None:
    w_start = sunday.isoformat()
    w_end   = thursday.isoformat()
    df = df.drop(columns=[c for c in df.columns if c.startswith("_")], errors="ignore")
    for col in df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]", "datetimetz"]).columns:
        df[col] = df[col].astype(str)
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(lambda v: str(v) if hasattr(v, "isoformat") else v)
    raw_rows = df.to_dict(orient="records")
    upsert_report(week_label, w_start, w_end, raw_rows)


def main() -> None:
    st.title("📤 Utilization Weekly Check-in")
    st.markdown("Fetch this week's time entries directly from Clockify to save utilization data.")
    st.divider()

    ui.section("Fetch from Clockify")

    col_wk, col_lbl = st.columns([2, 4], vertical_alignment="bottom")
    with col_wk:
        last_week = date.today() - timedelta(days=7)
        picked = st.date_input(
            "Pick any day in the week",
            value=last_week,
            help="Select any day — the full Sun–Thu week will be used.",
        )
    week_label = week_label_from_date(picked)
    sunday, thursday = week_bounds(picked)
    with col_lbl:
        st.markdown(f"**{week_label}**")

    # ── Clockify API fetch ────────────────────────────────────────────────────
    if not is_configured():
        st.error("⚠️ Clockify API key not configured. Add `CLOCKIFY_API_KEY` to `.streamlit/secrets.toml`.")
        return

    fetch_key = f"util_fetched_{week_label}"

    if st.button("🔄 Fetch from Clockify", type="primary"):
        try:
            with st.spinner("Fetching entries from Clockify…"):
                wid        = get_active_workspace_id()
                start_iso  = f"{sunday.strftime('%Y-%m-%d')}T00:00:00.000Z"
                end_iso    = f"{thursday.strftime('%Y-%m-%d')}T23:59:59.999Z"
                entries    = fetch_detailed_entries(wid, start_iso, end_iso)
                df_fetched = parse_clockify_api(entries)
            st.session_state[fetch_key] = df_fetched.to_dict(orient="records")
        except ClockifyError as exc:
            st.error(f"❌ Clockify error: {exc}")
            st.session_state.pop(fetch_key, None)

    # ── Preview + save (shown after a successful fetch) ───────────────────────
    if fetch_key in st.session_state:
        df = pd.DataFrame(st.session_state[fetch_key])
        df["Duration (decimal)"] = pd.to_numeric(df["Duration (decimal)"], errors="coerce").fillna(0.0)

        if df.empty or "User" not in df.columns:
            st.warning("No time entries found for this week in Clockify.")
        else:
            util_preview = calculate_utilization(df)
            total_hrs    = float(df["Duration (decimal)"].sum())
            n_members    = len(util_preview)

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Team Members", n_members)
            col_b.metric("Total Hours", f"{total_hrs:.1f} h")
            col_c.metric("Avg Utilization", f"{util_preview['Utilization %'].mean():.1f}%")

            already_saved = report_exists(week_label)
            save_clicked = False
            if already_saved:
                st.warning(
                    "⚠️ A report for this week already exists. "
                    "Saving will **replace** the saved data."
                )
                col_ok, col_cancel, _ = st.columns([1, 1, 4])
                if col_ok.button("✅ Confirm & Replace", type="primary"):
                    save_clicked = True
                if col_cancel.button("✖ Cancel"):
                    st.session_state.pop(fetch_key, None)
                    st.info("Cancelled.")
            else:
                if st.button("💾 Save Report", type="primary"):
                    save_clicked = True

            if save_clicked:
                _save_df(df, week_label, sunday, thursday)
                st.session_state.pop(fetch_key, None)
                st.success(f"✅ Report saved for **{week_label}**.")
                st.session_state["util_selected_week"] = week_label
                st.switch_page("systems/arkscore/utilization_dashboard.py")

    # ── Saved weeks table ──────────────────────────────────────────────────────
    ui.section("Saved Weeks")

    all_reports = get_all_reports()
    if not all_reports:
        st.info("No reports saved yet.")
        return

    h1, h2, h3, h4, h5, h6 = st.columns([3, 2, 1, 1, 1, 1])
    h1.markdown("**Week**")
    h2.markdown("**Uploaded**")
    h3.markdown("**Members**")
    h4.markdown("**Hours**")
    h5.markdown("")
    h6.markdown("")
    st.divider()

    for rep in all_reports:
        label   = rep["week_label"]
        up_at   = rep.get("uploaded_at", "")
        try:
            up_at_fmt = datetime.fromisoformat(up_at).strftime("%d %b %Y %H:%M")
        except Exception:
            up_at_fmt = up_at

        raw_df = pd.DataFrame(rep.get("raw_rows", []))
        if not raw_df.empty and "Duration (decimal)" in raw_df.columns:
            raw_df["Duration (decimal)"] = pd.to_numeric(
                raw_df["Duration (decimal)"], errors="coerce"
            ).fillna(0.0)
            n_members = raw_df["User"].nunique() if "User" in raw_df.columns else "—"
            total_h_s = f"{raw_df['Duration (decimal)'].sum():.1f} h"
        else:
            n_members = "—"
            total_h_s = "—"

        c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1, 1, 1, 1])
        c1.markdown(label)
        c2.markdown(up_at_fmt)
        c3.markdown(str(n_members))
        c4.markdown(total_h_s)
        if c5.button("View", key=f"view_{label}", use_container_width=True):
            st.session_state["util_selected_week"] = label
            st.switch_page("systems/arkscore/utilization_dashboard.py")
        if c6.button("Delete", key=f"del_{label}", use_container_width=True):
            st.session_state[f"confirm_delete_{label}"] = True

        if st.session_state.get(f"confirm_delete_{label}"):
            st.warning(f"Delete report for **{label}**? This cannot be undone.")
            ok, cancel = st.columns(2)
            if ok.button("Yes, delete", key=f"yes_del_{label}", type="primary"):
                delete_report(label)
                st.session_state.pop(f"confirm_delete_{label}", None)
                st.success(f"Deleted report for {label}.")
                st.rerun()
            if cancel.button("Cancel", key=f"cancel_del_{label}"):
                st.session_state.pop(f"confirm_delete_{label}", None)
                st.rerun()


main()
