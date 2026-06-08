"""
systems/arkscore/utilization_checkin.py
Utilization % Weekly Check-in — upload a Clockify CSV to save a week's data.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from systems.arkscore.utils.constants import REQUIRED_COLUMNS
from systems.arkscore.utils.entry_store import week_bounds, week_label_from_date
from systems.arkscore.utils.parse_clockify import calculate_utilization, parse_clockify_csv
from systems.arkscore.utils.utilization_store import (
    delete_report,
    get_all_reports,
    report_exists,
    upsert_report,
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.section-heading {
    font-size: 0.8rem; font-weight: 700; color: #94A3B8;
    margin: 32px 0 14px 0; padding-bottom: 8px;
    border-bottom: 1px solid #334155;
    text-transform: uppercase; letter-spacing: 0.1em;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.markdown("# 📤 Utilization Weekly Check-in")
    st.markdown("Upload a Clockify **Detailed Report** to save this week's utilization data.")
    st.markdown("---")

    st.markdown('<p class="section-heading">Upload Report</p>', unsafe_allow_html=True)

    col_wk, col_lbl, _ = st.columns([2, 4, 2])
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
        st.markdown(
            f"<div style='padding-top:28px;font-size:.9rem;font-weight:600;"
            f"color:#94A3B8;'>{week_label}</div>",
            unsafe_allow_html=True,
        )

    uploaded = st.file_uploader(
        "Clockify Detailed Report (.csv)",
        type=["csv"],
        label_visibility="visible",
    )

    if uploaded is not None:
        try:
            df = parse_clockify_csv(uploaded)
        except ValueError as exc:
            st.error(f"❌ {exc}")
            return
        except Exception as exc:
            st.error(f"❌ Failed to read file: {exc}")
            return

        util_preview = calculate_utilization(df)
        total_hrs    = float(df["Duration (decimal)"].sum())
        n_members    = len(util_preview)

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Team Members", n_members)
        col_b.metric("Total Hours", f"{total_hrs:.1f} h")
        col_c.metric("Avg Utilization", f"{util_preview['Utilization %'].mean():.1f}%")

        already_saved = report_exists(week_label)
        if already_saved:
            st.warning(
                "⚠️ A report for this week already exists. "
                "Uploading will **replace** the saved data."
            )
            col_ok, col_cancel, _ = st.columns([1, 1, 4])
            confirm = col_ok.button("✅ Confirm & Replace", type="primary")
            cancel  = col_cancel.button("✖ Cancel")
            if cancel:
                st.info("Upload cancelled.")
                return
            if not confirm:
                return
        else:
            if not st.button("💾 Save Report", type="primary"):
                return

        w_start = sunday.isoformat()
        w_end   = thursday.isoformat()

        df = df.drop(columns=[c for c in df.columns if c.startswith("_")], errors="ignore")
        for col in df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]", "datetimetz"]).columns:
            df[col] = df[col].astype(str)
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].apply(lambda v: str(v) if hasattr(v, "isoformat") else v)
        raw_rows = df.to_dict(orient="records")
        upsert_report(week_label, w_start, w_end, raw_rows)

        st.success(f"✅ Report saved for **{week_label}**.")
        st.session_state["util_selected_week"] = week_label
        st.switch_page("systems/arkscore/utilization_dashboard.py")

    # ── Saved weeks table ──────────────────────────────────────────────────────
    st.markdown('<p class="section-heading">Saved Weeks</p>', unsafe_allow_html=True)

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
    st.markdown("<hr style='margin:4px 0 8px 0;border-color:#334155'>", unsafe_allow_html=True)

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
