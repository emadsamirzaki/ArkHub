"""
systems/project_hours/hours_tracking.py
Detail & entry — set a project's retainer contract, log monthly burned hours,
and see the full burn-down breakdown (pace, variance, projected need).
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from systems.arkscore.utils.project_store import get_retainer_projects
from systems.project_hours.utils import clockify
from systems.project_hours.utils.calc import month_keys, month_label, summarize
from systems.project_hours.utils.constants import (
    STATUS_COLORS,
    STATUS_ICONS,
    TOLERANCE,
)
from systems.project_hours.utils.contract_store import (
    delete_contract,
    get_contract,
    upsert_contract,
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important}

.ph-section{
    font-size:.78rem;font-weight:700;color:#94A3B8;
    margin:30px 0 14px;padding-bottom:8px;
    border-bottom:1px solid #334155;
    text-transform:uppercase;letter-spacing:.1em;
}
.metric-card{
    background:#1E293B;border-radius:14px;padding:18px 16px;text-align:center;
    border:1px solid #334155;min-height:104px;margin-bottom:8px;
}
.metric-label{color:#94A3B8;font-size:.7rem;text-transform:uppercase;
    letter-spacing:.1em;font-weight:600;margin:0 0 8px;}
.metric-value{font-size:1.9rem;font-weight:700;margin:0;line-height:1.1;}
.metric-sub{color:#64748B;font-size:.74rem;margin:6px 0 0;}
</style>
"""

PER_ROW = 6


def _fmt(n: float) -> str:
    return f"{n:,.0f}" if abs(n - round(n)) < 0.05 else f"{n:,.1f}"


def _metric_card(label: str, value: str, sub: str = "", color: str = "#F8FAFC") -> None:
    sub_html = f'<p class="metric-sub">{sub}</p>' if sub else ""
    st.markdown(
        f"""<div class="metric-card">
  <p class="metric-label">{label}</p>
  <p class="metric-value" style="color:{color};">{value}</p>
  {sub_html}
</div>""",
        unsafe_allow_html=True,
    )


def _pace_hero(s: dict) -> None:
    status = s["pace_status"]
    color  = STATUS_COLORS.get(status, "#94A3B8")
    icon   = STATUS_ICONS.get(status, "")
    var    = s["variance"]
    sign   = "+" if var >= 0 else "−"
    st.markdown(
        f"""<div style="background:#1E293B;border:1px solid #334155;border-left:6px solid {color};
            border-radius:12px;padding:20px 24px;margin-bottom:8px;">
  <span style="font-size:.7rem;font-weight:700;color:#64748B;text-transform:uppercase;
               letter-spacing:.1em;">Burn Pace</span>
  <p style="font-size:1.8rem;font-weight:800;color:{color};margin:6px 0 2px;">{icon} {status}</p>
  <p style="font-size:.88rem;color:#CBD5E1;margin:0;">
    {_fmt(s['burned_to_date'])} h burned vs {_fmt(s['expected_to_date'])} h expected after
    {s['months_completed']} of {s['total_months']} months
    &nbsp;·&nbsp;<b style="color:{color};">{sign}{_fmt(abs(var))} h</b>
  </p>
</div>""",
        unsafe_allow_html=True,
    )


def _month_table(per_month: list[dict]) -> None:
    body = ""
    for m in per_month:
        color = STATUS_COLORS.get(m["status"], "#94A3B8")
        icon  = STATUS_ICONS.get(m["status"], "")
        body += (
            "<tr>"
            f"<td style='padding:6px 14px'>{m['label']}</td>"
            f"<td style='padding:6px 14px;text-align:right'>{_fmt(m['burned'])} h</td>"
            f"<td style='padding:6px 14px;text-align:right;color:#64748B'>{_fmt(m['avg_monthly'])} h</td>"
            f"<td style='padding:6px 14px;text-align:center;color:{color};font-weight:600'>"
            f"{icon} {m['status']}</td>"
            "</tr>"
        )
    st.markdown(
        f"""<table style='width:100%;border-collapse:collapse;font-size:.88rem;
                          font-family:Inter,sans-serif;color:#E2E8F0;'>
  <thead><tr style='border-bottom:1px solid #334155;color:#94A3B8;font-size:.72rem;
                    text-transform:uppercase;letter-spacing:.05em;'>
    <th style='padding:6px 14px;text-align:left'>Month</th>
    <th style='padding:6px 14px;text-align:right'>Burned</th>
    <th style='padding:6px 14px;text-align:right'>Avg / Month</th>
    <th style='padding:6px 14px;text-align:center'>Status</th>
  </tr></thead>
  <tbody>{body}</tbody>
</table>""",
        unsafe_allow_html=True,
    )


def _clockify_sync_section(project_id: str, project_name: str,
                           contract: dict, keys: list[str]) -> None:
    st.markdown('<p class="ph-section">Clockify Sync</p>', unsafe_allow_html=True)

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
    stored  = contract.get("clockify_project_id")
    auto    = clockify.match_project(project_name, cprojects)
    default_id = stored or auto
    idx = options.index(default_id) if default_id in options else 0

    c1, c2 = st.columns([3, 1])
    with c1:
        sel_cid = st.selectbox(
            "Clockify project", options, index=idx,
            format_func=lambda i: names[i], key=f"cf_proj_{project_id}",
        )
    with c2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        do_sync = st.button("🔄 Sync from Clockify", type="primary", key=f"cf_sync_{project_id}")

    if stored:
        st.caption(f"Linked to Clockify project **{names.get(stored, stored)}** · pulls billable hours.")
    elif auto:
        st.caption(f"Auto-matched by name → **{names[auto]}**. Sync to confirm & save the link.")
    else:
        st.caption("No name match — pick the Clockify project above, then Sync.")

    if do_sync:
        today = date.today()
        cur_month = f"{today.year:04d}-{today.month:02d}"
        try:
            with st.spinner("Pulling billable hours from Clockify…"):
                pulled = clockify.monthly_billable_hours(wid, sel_cid, keys, cur_month)
        except clockify.ClockifyError as e:
            st.error(str(e))
            return
        merged = dict(contract["monthly_hours"])
        merged.update(pulled)
        upsert_contract(
            project_id, contract["from_date"], contract["to_date"],
            contract["total_hours"], merged, clockify_project_id=sel_cid,
        )
        st.success(
            f"✅ Synced {len(pulled)} month(s) — {sum(pulled.values()):,.1f} billable h total. "
            "Values appear below and can be overridden manually."
        )
        st.rerun()


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("# ⏱️ Hours Tracking")
    st.markdown("---")

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
    st.markdown('<p class="ph-section">Contract</p>', unsafe_allow_html=True)
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
    st.markdown('<p class="ph-section">Monthly Burned Hours</p>', unsafe_allow_html=True)
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

    st.markdown('<p class="ph-section">Burn-down</p>', unsafe_allow_html=True)
    _pace_hero(s)

    var_color = STATUS_COLORS.get(s["pace_status"], "#F8FAFC")
    r1 = st.columns(3)
    with r1[0]:
        _metric_card("Avg / Month Target", f"{_fmt(s['avg_monthly'])} h",
                     f"{_fmt(s['total_hours'])} h ÷ {s['total_months']} months")
    with r1[1]:
        _metric_card("Burned to Date", f"{_fmt(s['burned_to_date'])} h",
                     f"of {_fmt(s['total_hours'])} h total")
    with r1[2]:
        _metric_card("Variance vs Expected", f"{'+' if s['variance'] >= 0 else '−'}{_fmt(abs(s['variance']))} h",
                     f"expected {_fmt(s['expected_to_date'])} h by now", var_color)

    r2 = st.columns(3)
    with r2[0]:
        _metric_card("Hours Remaining", f"{_fmt(s['remaining_hours'])} h",
                     f"{s['remaining_months']} months left")
    with r2[1]:
        need = s["projected_monthly_needed"]
        _metric_card("Needed / Month", f"{_fmt(need)} h" if s["remaining_months"] > 0 else "—",
                     "to finish on time" if s["remaining_months"] > 0 else "contract complete")
    with r2[2]:
        pct = (s["burned_to_date"] / s["total_hours"] * 100) if s["total_hours"] else 0.0
        _metric_card("Budget Used", f"{pct:.0f}%", "of contracted hours")

    st.markdown('<p class="ph-section">Month-by-Month</p>', unsafe_allow_html=True)
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
