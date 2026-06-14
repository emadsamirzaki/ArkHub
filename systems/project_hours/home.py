"""
systems/project_hours/home.py
Overview — every retainer project with its hours-burn pace at a glance.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from systems.arkscore.utils.project_store import get_retainer_projects
from systems.project_hours.utils.calc import summarize
from systems.project_hours.utils.constants import STATUS_COLOR_NAMES, STATUS_ICONS
from systems.project_hours.utils.contract_store import get_all_contracts
from systems.utils import ui


def _fmt(n: float) -> str:
    return f"{n:,.0f}" if abs(n - round(n)) < 0.05 else f"{n:,.1f}"


def _card(project: dict, contract: dict | None) -> None:
    name = project["name"]
    pm   = project.get("pm", "—")

    with st.container(border=True):
        st.markdown(f"**{name}**")
        st.caption(f"PM: {pm}")

        if not contract:
            st.markdown(":gray-badge[No contract set]")
            st.caption("Configure it in **Hours Tracking**.")
            return

        s       = summarize(contract)
        status  = s["pace_status"]
        color   = STATUS_COLOR_NAMES.get(status, "gray")
        icon    = STATUS_ICONS.get(status, "")
        var     = s["variance"]
        var_txt = f"{'+' if var >= 0 else '−'}{_fmt(abs(var))} h vs expected"

        st.markdown(f":{color}-badge[{icon} {status}]")
        st.markdown(f"Avg / month　**{_fmt(s['avg_monthly'])} h**")
        st.markdown(f"Burned to date　**{_fmt(s['burned_to_date'])} / {_fmt(s['total_hours'])} h**")
        st.markdown(f"Pace　:{color}[**{var_txt}**]")


def main() -> None:
    st.title("⏱️ Projects Hours Tracking")
    st.divider()

    projects = get_retainer_projects()
    if not projects:
        st.info(
            "No retainer projects yet.\n\n"
            "Mark a project as **🔁 Retainer** in **ArkScore → Project Management**, "
            "then set its contract in **Hours Tracking**."
        )
        return

    contracts = {c["project_id"]: c for c in get_all_contracts()}

    ui.section("Retainer Projects")
    cols = st.columns(3)
    for i, project in enumerate(projects):
        with cols[i % 3]:
            _card(project, contracts.get(project["id"]))

    # ── Summary table ──────────────────────────────────────────────────────────
    ui.section("Summary")
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
