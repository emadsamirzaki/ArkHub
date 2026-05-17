"""
parse_clockify.py
CSV parsing and utilisation-metric calculations.
Works with Clockify "Detailed Report" CSV exports.
"""

from __future__ import annotations

import pandas as pd

from .constants import (
    ON_TARGET_THRESHOLD,
    REQUIRED_COLUMNS,
    STATUS_CRITICAL,
    STATUS_ON_TARGET,
    STATUS_WATCH,
    TARGET_HOURS,
    WATCH_THRESHOLD,
)


def parse_clockify_csv(file) -> pd.DataFrame:
    df = pd.read_csv(file)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "The uploaded file is missing required columns:\n"
            + ", ".join(missing)
            + "\n\nPlease upload a Clockify Detailed Report export."
        )

    df["Start Date"] = pd.to_datetime(df["Start Date"], format="%m/%d/%Y", errors="coerce")

    if df["Duration (decimal)"].dtype == object:
        df["Duration (decimal)"] = (
            df["Duration (decimal)"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
    df["Duration (decimal)"] = pd.to_numeric(
        df["Duration (decimal)"], errors="coerce"
    ).fillna(0.0)

    df["Billable"] = df["Billable"].astype(str).str.strip()
    df = df[df["User"].notna() & (df["User"].astype(str).str.strip() != "")].copy()
    return df


def get_week_label(df: pd.DataFrame) -> str:
    if "Start Date" not in df.columns or df["Start Date"].isna().all():
        return "Week of Unknown"
    earliest = df["Start Date"].min()
    latest   = df["Start Date"].max()
    start_str = f"{earliest.strftime('%b')} {earliest.day}"
    end_str   = f"{latest.strftime('%b')} {latest.day}, {latest.year}"
    return f"Week of {start_str} – {end_str}"


def calculate_utilization(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for user, grp in df.groupby("User"):
        total_hrs    = float(grp["Duration (decimal)"].sum())
        bill_hrs     = float(grp[grp["Billable"] == "Yes"]["Duration (decimal)"].sum())
        non_bill_hrs = float(grp[grp["Billable"] == "No"]["Duration (decimal)"].sum())

        util_pct     = (total_hrs    / TARGET_HOURS * 100) if TARGET_HOURS else 0.0
        bill_pct     = (bill_hrs     / total_hrs    * 100) if total_hrs    else 0.0
        non_bill_pct = (non_bill_hrs / total_hrs    * 100) if total_hrs    else 0.0

        if util_pct >= ON_TARGET_THRESHOLD:
            status = STATUS_ON_TARGET
        elif util_pct >= WATCH_THRESHOLD:
            status = STATUS_WATCH
        else:
            status = STATUS_CRITICAL

        rows.append({
            "Name":           str(user),
            "Total Hrs":      round(total_hrs,    2),
            "Billable Hrs":   round(bill_hrs,     2),
            "Non-Bill Hrs":   round(non_bill_hrs, 2),
            "Utilization %":  round(util_pct,     1),
            "Billable %":     round(bill_pct,     1),
            "Non-Billable %": round(non_bill_pct, 1),
            "Status":         status,
        })

    result = (
        pd.DataFrame(rows)
        .sort_values("Utilization %", ascending=False)
        .reset_index(drop=True)
    )
    result.insert(0, "Rank", range(1, len(result) + 1))
    return result


def get_project_breakdown(df: pd.DataFrame) -> dict[str, dict]:
    breakdown: dict[str, dict] = {}
    for user, u_grp in df.groupby("User"):
        u_grp = u_grp.copy()
        u_grp["Project"]     = u_grp["Project"].fillna("(No Project)").replace("", "(No Project)")
        u_grp["Description"] = u_grp["Description"].fillna("(No Description)").replace("", "(No Description)")

        projects: dict = {}
        for project, p_grp in u_grp.groupby("Project"):
            tasks = [
                {
                    "description": str(row["Description"]),
                    "hours":       round(float(row["Duration (decimal)"]), 2),
                    "billable":    str(row["Billable"]) == "Yes",
                }
                for _, row in p_grp.iterrows()
            ]
            projects[str(project)] = {
                "tasks":       tasks,
                "total_hours": round(float(p_grp["Duration (decimal)"].sum()), 2),
            }
        breakdown[str(user)] = projects
    return breakdown
