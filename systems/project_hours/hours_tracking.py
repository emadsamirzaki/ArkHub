"""
systems/project_hours/hours_tracking.py
Detail & entry — set a project's retainer contract, log monthly burned hours,
and see the full burn-down breakdown (pace, variance, projected need).
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from systems.arkscore.utils.project_store import get_retainer_projects
from systems.project_hours.utils import clockify
from systems.project_hours.utils.calc import month_keys, month_label, summarize
from systems.project_hours.utils.constants import (
    STATUS_ABOVE,
    STATUS_COLOR_NAMES,
    STATUS_ICONS,
    STATUS_IN_RANGE,
    TOLERANCE,
)
from systems.project_hours.utils.contract_store import (
    delete_contract,
    get_contract,
    upsert_contract,
)
from systems.utils import ui

PER_ROW = 6


def _fmt(n: float) -> str:
    return f"{n:,.0f}" if abs(n - round(n)) < 0.05 else f"{n:,.1f}"


def _pace_hero(s: dict) -> None:
    status = s["pace_status"]
    color  = STATUS_COLOR_NAMES.get(status, "gray")
    icon   = STATUS_ICONS.get(status, "")
    var    = s["variance"]
    with st.container(border=True):
        st.caption("BURN PACE")
        st.markdown(f"### :{color}[{icon} {status}]")
        if status == STATUS_IN_RANGE:
            detail = (
                f"{_fmt(s['burned_to_date'])} h burned　·　on pace through "
                f"month {s['months_started']} of {s['total_months']} "
                f"({_fmt(s['avg_monthly'])} h/mo allotment)"
            )
        elif status == STATUS_ABOVE:
            detail = (
                f"{_fmt(s['burned_to_date'])} h burned vs "
                f"{_fmt(s['expected_through_month'])} h allotted through "
                f"month {s['months_started']} of {s['total_months']}　·　"
                f":{color}[**+{_fmt(abs(var))} h**]"
            )
        else:  # Below pace
            detail = (
                f"{_fmt(s['burned_to_date'])} h burned vs "
                f"{_fmt(s['expected_to_date'])} h expected after "
                f"{s['months_completed']} of {s['total_months']} completed months　·　"
                f":{color}[**−{_fmt(abs(var))} h**]"
            )
        st.markdown(detail)


def _month_table(per_month: list[dict]) -> None:
    df = pd.DataFrame([
        {
            "Month":       m["label"],
            "Burned":      round(m["burned"], 1),
            "Avg / Month": round(m["avg_monthly"], 1),
            "Status":      f"{STATUS_ICONS.get(m['status'], '')} {m['status']}",
        }
        for m in per_month
    ])
    st.dataframe(
        df,
        column_config={
            "Burned":      st.column_config.NumberColumn("Burned", format="%.1f h"),
            "Avg / Month": st.column_config.NumberColumn("Avg / Month", format="%.1f h"),
        },
        use_container_width=True,
        hide_index=True,
    )


def _clockify_sync_section(project_id: str, project_name: str,
                           contract: dict, keys: list[str]) -> None:
    ui.section("Clockify Sync")

    if not clockify.is_configured():
        st.info(
            "Add **CLOCKIFY_API_KEY** to `.streamlit/secrets.toml` to pull **billable** "
            "hours automatically. Until then, enter hours manually below."
        )
        return

    try:
        wid       = clockify.get_active_workspace_id()
        cprojects = clockify.list_projects(wid)
    except clockify.ClockifyError as e:
        st.error(str(e))
        return

    if not cprojects:
        st.warning("No projects found in your Clockify workspace.")
        return

    names   = {p["id"]: p["name"] for p in cprojects}
    options = [p["id"] for p in cprojects]
    stored  = contract.get("clockify_project_ids") or []
    auto    = clockify.match_project(project_name, cprojects)
    default_ids = stored or ([auto] if auto else [])
    default_ids = [i for i in default_ids if i in names]

    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    with c1:
        sel_cids = st.multiselect(
            "Clockify projects", options, default=default_ids,
            format_func=lambda i: names[i], key=f"cf_proj_{project_id}",
        )
    with c2:
        do_sync = st.button("🔄 Sync from Clockify", type="primary", key=f"cf_sync_{project_id}")

    if stored:
        linked = ", ".join(f"**{names.get(i, i)}**" for i in stored)
        st.caption(f"Linked to Clockify project(s) {linked} · pulls combined billable hours.")
    elif auto:
        st.caption(f"Auto-matched by name → **{names[auto]}**. Sync to confirm & save the link.")
    else:
        st.caption("No name match — pick one or more Clockify projects above, then Sync.")

    if do_sync:
        if not sel_cids:
            st.error("Pick at least one Clockify project before syncing.")
            return
        today = date.today()
        cur_month = f"{today.year:04d}-{today.month:02d}"
        try:
            with st.spinner("Pulling billable hours from Clockify…"):
                pulled = clockify.monthly_billable_hours(
                    wid, sel_cids, keys, cur_month,
                    contract["from_date"], contract["to_date"],
                )
        except clockify.ClockifyError as e:
            st.error(str(e))
            return
        merged = dict(contract["monthly_hours"])
        merged.update(pulled)
        upsert_contract(
            project_id, contract["from_date"], contract["to_date"],
            contract["total_hours"], merged, clockify_project_ids=sel_cids,
        )
        st.success(
            f"✅ Synced {len(pulled)} month(s) — {sum(pulled.values()):,.1f} billable h total. "
            "Values appear below and can be overridden manually."
        )
        st.rerun()


def main() -> None:
    st.title("⏱️ Hours Tracking")
    st.divider()

    projects = get_retainer_projects()
    if not projects:
        st.info(
            "No retainer projects yet.\n\n"
            "Mark a project as **🔁 Retainer** in **ArkScore → Project Management** first."
        )
        return

    # ── Project selector ───────────────────────────────────────────────────────
    labels = {p["id"]: p["name"] for p in projects}
    sel_id = st.selectbox(
        "Project",
        options=[p["id"] for p in projects],
        format_func=lambda i: labels[i],
    )

    contract = get_contract(sel_id)

    # ── Contract setup ───────────────────────────────────────────────────────--
    ui.section("Contract")
    today = date.today()
    def_from = date.fromisoformat(contract["from_date"]) if contract else date(today.year, 1, 1)
    def_to   = date.fromisoformat(contract["to_date"])   if contract else date(today.year, 12, 31)
    def_total = float(contract["total_hours"]) if contract else 0.0

    with st.form("contract_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            from_date = st.date_input("From", value=def_from, format="YYYY-MM-DD")
        with c2:
            to_date = st.date_input("To", value=def_to, format="YYYY-MM-DD")
        with c3:
            total_hours = st.number_input(
                "Total contracted hours", min_value=0.0, step=10.0, value=def_total,
            )
        save_contract = st.form_submit_button("💾 Save Contract", type="primary")

    if save_contract:
        if to_date < from_date:
            st.error("'To' date must be on or after the 'From' date.")
        elif total_hours <= 0:
            st.error("Total contracted hours must be greater than zero.")
        else:
            existing_monthly = contract["monthly_hours"] if contract else {}
            upsert_contract(
                sel_id, from_date.isoformat(), to_date.isoformat(),
                total_hours, existing_monthly,
            )
            st.success("✅ Contract saved.")
            st.rerun()

    if not contract:
        st.info("Save the contract above to start logging monthly hours.")
        return

    keys = month_keys(contract["from_date"], contract["to_date"])
    if not keys:
        st.warning("Contract period is empty — check the From / To dates.")
        return

    monthly = dict(contract["monthly_hours"])

    # ── Clockify sync ──────────────────────────────────────────────────────────
    _clockify_sync_section(sel_id, labels[sel_id], contract, keys)

    # ── Monthly hours entry ──────────────────────────────────────────────────--
    ui.section("Monthly Burned Hours")
    st.caption("Synced from Clockify when available — edit any month to override.")
    # `updated_at` changes on every save/sync; folding it into the widget keys
    # forces the inputs to re-read freshly synced values instead of stale state.
    cver = contract.get("updated_at", "")
    with st.form("monthly_form"):
        new_vals: dict[str, float] = {}
        for yr in sorted({k[:4] for k in keys}):
            st.markdown(f"**{yr}**")
            yr_keys = [k for k in keys if k.startswith(yr)]
            for start in range(0, len(yr_keys), PER_ROW):
                chunk = yr_keys[start:start + PER_ROW]
                cols = st.columns(PER_ROW)
                for ci, k in enumerate(chunk):
                    with cols[ci]:
                        new_vals[k] = st.number_input(
                            month_label(k).split()[0],   # short month, e.g. "Jan"
                            min_value=0.0, step=1.0,
                            value=float(monthly.get(k, 0) or 0),
                            key=f"mh_{sel_id}_{k}_{cver}",
                        )
        save_monthly = st.form_submit_button("💾 Save Monthly Hours", type="primary")

    if save_monthly:
        merged = {k: v for k, v in new_vals.items() if v}
        upsert_contract(
            sel_id, contract["from_date"], contract["to_date"],
            contract["total_hours"], merged,
        )
        st.success("✅ Monthly hours saved.")
        st.rerun()

    # ── Breakdown ──────────────────────────────────────────────────────────────
    s = summarize(contract)

    ui.section("Burn-down")
    _pace_hero(s)
    st.markdown("")

    r1 = st.columns(3)
    r1[0].metric("Avg / Month Target", f"{_fmt(s['avg_monthly'])} h",
                 help=f"{_fmt(s['total_hours'])} h ÷ {s['total_months']} months", border=True)
    r1[1].metric("Burned to Date", f"{_fmt(s['burned_to_date'])} h",
                 help=f"of {_fmt(s['total_hours'])} h total", border=True)
    if s["pace_status"] == STATUS_IN_RANGE:
        var_display = "On pace"
        var_help = (f"within the pace band: {_fmt(s['expected_to_date'])}–"
                    f"{_fmt(s['expected_through_month'])} h through month "
                    f"{s['months_started']} of {s['total_months']}")
    else:
        var = s["variance"]
        ref = s["expected_through_month"] if var >= 0 else s["expected_to_date"]
        var_display = f"{'+' if var >= 0 else '−'}{_fmt(abs(var))} h"
        var_help = f"vs {_fmt(ref)} h allotted so far"
    r1[2].metric("Variance vs Expected", var_display, help=var_help, border=True)

    r2 = st.columns(3)
    r2[0].metric("Hours Remaining", f"{_fmt(s['remaining_hours'])} h",
                 help=f"{s['remaining_months']} months left", border=True)
    need = s["projected_monthly_needed"]
    r2[1].metric("Needed / Month", f"{_fmt(need)} h" if s["remaining_months"] > 0 else "—",
                 help="to finish on time" if s["remaining_months"] > 0 else "contract complete",
                 border=True)
    pct = (s["burned_to_date"] / s["total_hours"] * 100) if s["total_hours"] else 0.0
    r2[2].metric("Budget Used", f"{pct:.0f}%", help="of contracted hours", border=True)

    ui.section("Month-by-Month")
    st.caption(f"A month is *in range* within ±{int(TOLERANCE * 100)}% of the monthly average "
               f"({_fmt(s['avg_monthly'])} h). Future months show as ⚪ Upcoming.")
    _month_table(s["per_month"])

    # ── Danger zone ──────────────────────────────────────────────────────────--
    with st.expander("⚠️ Delete this contract"):
        st.caption("Removes the contract and all logged monthly hours for this project.")
        if st.button("Delete contract", type="secondary"):
            delete_contract(sel_id)
            st.success("Contract deleted.")
            st.rerun()


main()
