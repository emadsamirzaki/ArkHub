"""
systems/project_hours/utils/calc.py
Month helpers + pace / variance maths for retainer hours tracking.

The core entry point is `summarize(contract)`, which turns a stored contract
({from_date, to_date, total_hours, monthly_hours}) into all the derived figures
the dashboard needs.
"""
from __future__ import annotations

from datetime import date

from systems.project_hours.utils.constants import (
    STATUS_ABOVE,
    STATUS_BELOW,
    STATUS_IN_RANGE,
    STATUS_UPCOMING,
    TOLERANCE,
)

_MONTH_ABBR = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _parse(d) -> date:
    """Accept a date or an ISO 'YYYY-MM-DD' string."""
    if isinstance(d, date):
        return d
    return date.fromisoformat(str(d)[:10])


def month_keys(from_date, to_date) -> list[str]:
    """Inclusive list of 'YYYY-MM' keys from the from-month to the to-month."""
    start = _parse(from_date)
    end   = _parse(to_date)
    keys: list[str] = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        keys.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return keys


def month_label(key: str) -> str:
    """'2025-01' -> 'Jan 2025'."""
    y, m = key.split("-")
    return f"{_MONTH_ABBR[int(m)]} {y}"


def _classify(actual: float, expected: float) -> str:
    """Classify actual vs expected within the ±TOLERANCE band."""
    if expected <= 0:
        return STATUS_ABOVE if actual > 0 else STATUS_IN_RANGE
    if actual < expected * (1 - TOLERANCE):
        return STATUS_BELOW
    if actual > expected * (1 + TOLERANCE):
        return STATUS_ABOVE
    return STATUS_IN_RANGE


def summarize(contract: dict, today: date | None = None) -> dict:
    """
    Compute pace metrics for a contract.

    Expectation is based on *completed* months only (the current month is treated
    as in-progress), so a project burning on pace mid-month isn't flagged behind.
    """
    today = today or date.today()

    keys         = month_keys(contract["from_date"], contract["to_date"])
    total_months = len(keys)
    total_hours  = float(contract.get("total_hours", 0) or 0)
    monthly      = contract.get("monthly_hours", {}) or {}

    avg_monthly    = total_hours / total_months if total_months else 0.0
    burned_to_date = float(sum(float(v or 0) for v in monthly.values()))

    today_key        = f"{today.year:04d}-{today.month:02d}"
    months_completed = min(sum(1 for k in keys if k < today_key), total_months)

    expected_to_date = avg_monthly * months_completed
    variance         = burned_to_date - expected_to_date
    pace_status      = _classify(burned_to_date, expected_to_date)

    remaining_hours  = total_hours - burned_to_date
    remaining_months = total_months - months_completed
    projected_monthly_needed = (
        remaining_hours / remaining_months if remaining_months > 0 else 0.0
    )

    per_month = []
    for k in keys:
        burned = float(monthly.get(k, 0) or 0)
        # A month that hasn't been reached yet (and has nothing logged) is neutral,
        # not "below" — otherwise every future month of a long contract shows red.
        if k >= today_key and burned == 0:
            status = STATUS_UPCOMING
        else:
            status = _classify(burned, avg_monthly)
        per_month.append({
            "key":         k,
            "label":       month_label(k),
            "burned":      burned,
            "avg_monthly": avg_monthly,
            "status":      status,
        })

    return {
        "total_hours":              total_hours,
        "total_months":             total_months,
        "avg_monthly":              avg_monthly,
        "burned_to_date":           burned_to_date,
        "months_completed":         months_completed,
        "expected_to_date":         expected_to_date,
        "variance":                 variance,
        "pace_status":              pace_status,
        "remaining_hours":          remaining_hours,
        "remaining_months":         remaining_months,
        "projected_monthly_needed": projected_monthly_needed,
        "per_month":                per_month,
    }
