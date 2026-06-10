"""
systems/project_hours/home.py
Overview — every retainer project with its hours-burn pace at a glance.
"""
from __future__ import annotations

import html as _html

import pandas as pd
import streamlit as st

from systems.arkscore.utils.project_store import get_retainer_projects
from systems.project_hours.utils.calc import summarize
from systems.project_hours.utils.constants import STATUS_COLORS, STATUS_ICONS
from systems.project_hours.utils.contract_store import get_all_contracts

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif!important}

.ph-section{
    font-size:.78rem;font-weight:700;color:#94A3B8;
    margin:28px 0 14px;padding-bottom:8px;
    border-bottom:1px solid #334155;
    text-transform:uppercase;letter-spacing:.1em;
}
.phcard{
    border-radius:12px;padding:16px 18px;margin-bottom:8px;
    border-left:5px solid;min-height:158px;background:#1E293B;
}
.phcard-title{font-size:.98rem;font-weight:700;color:#F1F5F9;margin:0 0 2px;}
.phcard-pm{font-size:.76rem;color:#94A3B8;margin:0 0 10px;}
.phcard-status{font-size:.9rem;font-weight:700;margin:0 0 10px;}
.phcard-row{font-size:.8rem;color:#CBD5E1;margin:3px 0;display:flex;justify-content:space-between;gap:12px;}
.phcard-row b{color:#F1F5F9;font-weight:600;}
.phcard-none{font-size:.8rem;color:#64748B;font-style:italic;margin:8px 0 0;}
</style>
"""


def _fmt(n: float) -> str:
    return f"{n:,.0f}" if abs(n - round(n)) < 0.05 else f"{n:,.1f}"


def _card(project: dict, contract: dict | None) -> None:
    name = _html.escape(project["name"])
    pm   = _html.escape(project.get("pm", "—"))

    if not contract:
        st.markdown(
            f"""<div class="phcard" style="border-left-color:#475569;">
  <p class="phcard-title">{name}</p>
  <p class="phcard-pm">PM: {pm}</p>
  <p class="phcard-none">No contract set — configure it in <b>Hours Tracking</b>.</p>
</div>""",
            unsafe_allow_html=True,
        )
        return

    s       = summarize(contract)
    status  = s["pace_status"]
    color   = STATUS_COLORS.get(status, "#94A3B8")
    icon    = STATUS_ICONS.get(status, "")
    var     = s["variance"]
    var_txt = f"{'+' if var >= 0 else '−'}{_fmt(abs(var))} h vs expected"

    st.markdown(
        f"""<div class="phcard" style="border-left-color:{color};">
  <p class="phcard-title">{name}</p>
  <p class="phcard-pm">PM: {pm}</p>
  <p class="phcard-status" style="color:{color};">{icon} {status}</p>
  <p class="phcard-row"><span>Avg / month</span><b>{_fmt(s['avg_monthly'])} h</b></p>
  <p class="phcard-row"><span>Burned to date</span><b>{_fmt(s['burned_to_date'])} / {_fmt(s['total_hours'])} h</b></p>
  <p class="phcard-row"><span>Pace</span><b style="color:{color};">{var_txt}</b></p>
</div>""",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("# ⏱️ Projects Hours Tracking")
    st.markdown("---")

    projects = get_retainer_projects()
    if not projects:
        st.info(
            "No retainer projects yet.\n\n"
            "Mark a project as **🔁 Retainer** in **ArkScore → Project Management**, "
            "then set its contract in **Hours Tracking**."
        )
        return

    contracts = {c["project_id"]: c for c in get_all_contracts()}

    st.markdown('<p class="ph-section">Retainer Projects</p>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, project in enumerate(projects):
        with cols[i % 3]:
            _card(project, contracts.get(project["id"]))

    # ── Summary table ──────────────────────────────────────────────────────────
    st.markdown('<p class="ph-section">Summary</p>', unsafe_allow_html=True)
    rows = []
    for p in projects:
        c = contracts.get(p["id"])
        if not c:
            rows.append({
                "Project": p["name"], "PM": p.get("pm", "—"), "Status": "No contract",
                "Total Hrs": None, "Burned": None, "Expected": None,
                "Variance": None, "Avg/Mo": None,
            })
            continue
        s = summarize(c)
        rows.append({
            "Project":   p["name"],
            "PM":        p.get("pm", "—"),
            "Status":    f"{STATUS_ICONS.get(s['pace_status'], '')} {s['pace_status']}",
            "Total Hrs": round(s["total_hours"], 1),
            "Burned":    round(s["burned_to_date"], 1),
            "Expected":  round(s["expected_to_date"], 1),
            "Variance":  round(s["variance"], 1),
            "Avg/Mo":    round(s["avg_monthly"], 1),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


main()
