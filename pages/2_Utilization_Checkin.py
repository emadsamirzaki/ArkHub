"""
pages/2_Utilization_Checkin.py
--------------------------------
Utilization % Weekly Check-in — upload a Clockify CSV to save a week's data.
Also shows the history of saved weeks with View / Delete actions.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.constants import REQUIRED_COLUMNS
from utils.entry_store import current_week_label, week_bounds, week_label_from_date
from utils.parse_clockify import calculate_utilization, parse_clockify_csv
from utils.utilization_store import (
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
.saved-row {
    background: #1E293B; border: 1px solid #334155;
    border-radius: 10px; padding: 14px 18px; margin-bottom: 10px;
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

    # ── Auto-detect current week ──────────────────────────────────────────────
    auto_week  = current_week_label()
    from datetime import date
    from utils.entry_store import week_bounds
    sunday, thursday = week_bounds(date.today())

    # ── Upload form ───────────────────────────────────────────────────────────
    st.markdown('<p class="section-heading">Upload Report</p>', unsafe_allow_html=True)

    # Week label input (editable, defaults to current week)
    week_label = st.text_input(
        "Week Label",
        value=auto_week,
        help="Auto-detected from today's Sun–Thu week. Edit to upload a different week.",
    )

    uploaded = st.file_uploader(
        "Clockify Detailed Report (.csv)",
        type=["csv"],
        label_visibility="visible",
    )

    if uploaded is not None:
        # ── Parse & validate ──────────────────────────────────────────────────
        try:
            df = parse_clockify_csv(uploaded)
        except ValueError as exc:
            st.error(f"❌ {exc}")
            return
        except Exception as exc:
            st.error(f"❌ Failed to read file: {exc}")
            return

        # Preview
        util_preview = calculate_utilization(df)
        total_hrs    = float(df["Duration (decimal)"].sum())
        n_members    = len(util_preview)

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Team Members", n_members)
        col_b.metric("Total Hours", f"{total_hrs:.1f} h")
        col_c.metric("Avg Utilization", f"{util_preview['Utilization %'].mean():.1f}%")

        # ── Duplicate warning ──────────────────────────────────────────────────
        already_saved = report_exists(week_label)
        if already_saved:
            st.warning(
                "⚠️ A report for this week already exists. "
                "Uploading will **replace** the saved data."
            )
            col_ok, col_cancel, _ = st.columns([1, 1, 4])
            confirm  = col_ok.button("✅ Confirm & Replace", type="primary")
            cancel   = col_cancel.button("✖ Cancel")
            if cancel:
                st.info("Upload cancelled.")
                return
            if not confirm:
                return
        else:
            if not st.button("💾 Save Report", type="primary"):
                return

        # ── Save ──────────────────────────────────────────────────────────────
        # Use Thursday of selected week for week_start / week_end anchors.
        # Determine bounds from the text_input week_label via today if it matches,
        # otherwise fall back to parsing the label date range.
        # Simplest reliable approach: use today's computed bounds if the label
        # matches auto_week, otherwise attempt to extract from the CSV dates.
        if week_label == auto_week:
            w_start = sunday.isoformat()
            w_end   = thursday.isoformat()
        else:
            # Try to derive bounds from the CSV's earliest Start Date
            try:
                df["_start_dt"] = pd.to_datetime(df["Start Date"], dayfirst=False, errors="coerce")
                min_dt = df["_start_dt"].dropna().min()
                if pd.notna(min_dt):
                    anchor_date = min_dt.date()
                    csv_sun, csv_thu = week_bounds(anchor_date)
                    w_start = csv_sun.isoformat()
                    w_end   = csv_thu.isoformat()
                else:
                    w_start = w_end = ""
            except Exception:
                w_start = w_end = ""

        # Drop any temporary helper columns and convert Timestamps to strings
        # so the data is JSON-serialisable.
        df = df.drop(columns=[c for c in df.columns if c.startswith("_")], errors="ignore")
        for col in df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]", "datetimetz"]).columns:
            df[col] = df[col].astype(str)
        # Also handle object columns that may contain Timestamp instances
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].apply(lambda v: str(v) if hasattr(v, "isoformat") else v)
        raw_rows = df.to_dict(orient="records")
        upsert_report(week_label, w_start, w_end, raw_rows)

        st.success(f"✅ Report saved for **{week_label}**.")

        # Auto-navigate to dashboard for this week
        st.session_state["util_selected_week"] = week_label
        st.rerun()

    else:
        # Show expected format hint
        st.markdown("---")
        st.markdown("**Expected CSV format — key columns:**")
        sample = pd.DataFrame({
            "Project":            ["Website Redesign", "Internal Meeting", "API Development"],
            "Client":             ["Acme Corp", "",          "TechCorp"],
            "Description":        ["Homepage layout", "Weekly sync", "Auth endpoint"],
            "User":               ["Alice", "Bob",    "Alice"],
            "Billable":           ["Yes",   "No",     "Yes"],
            "Start Date":         ["04/28/2026", "04/28/2026", "04/29/2026"],
            "Duration (decimal)": [2.50, 1.00, 3.25],
        })
        st.dataframe(sample, use_container_width=True, hide_index=True)
        st.caption(
            "The full Clockify export includes additional columns. "
            "Only the above columns are used for utilization calculations."
        )

    # ── Saved weeks table ──────────────────────────────────────────────────────
    st.markdown('<p class="section-heading">Saved Weeks</p>', unsafe_allow_html=True)

    all_reports = get_all_reports()
    if not all_reports:
        st.info("No reports saved yet.")
        return

    # Headers
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

        raw_df  = pd.DataFrame(rep.get("raw_rows", []))
        if not raw_df.empty and "Duration (decimal)" in raw_df.columns:
            raw_df["Duration (decimal)"] = pd.to_numeric(
                raw_df["Duration (decimal)"], errors="coerce"
            ).fillna(0.0)
            n_members = raw_df["User"].nunique() if "User" in raw_df.columns else "—"
            total_h   = raw_df["Duration (decimal)"].sum()
            total_h_s = f"{total_h:.1f} h"
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
            st.switch_page("pages/1_Utilization_Dashboard.py")
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
