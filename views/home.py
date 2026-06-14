"""
views/home.py — ArkPanel platform homepage
"""

import streamlit as st

# Only a scoped gradient for the wordmark; the gradient fill reads on both the
# light and dark themes. Fonts/colours otherwise come from the theme config.
st.markdown(
    """
<style>
@keyframes arkFadeUp { from {opacity:0; transform:translateY(18px);} to {opacity:1; transform:translateY(0);} }
.ark-hero { text-align:center; padding:32px 0 8px; }
.ark-title {
    font-size: clamp(2.6rem, 6vw, 4.4rem);
    font-weight: 900; line-height: 1.04; letter-spacing: -0.03em; margin: 0 0 10px;
    background: linear-gradient(120deg, #60A5FA 0%, #A78BFA 45%, #F472B6 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: arkFadeUp .6s cubic-bezier(.22,1,.36,1) both;
}
.ark-sub { font-size: 1.15rem; opacity: .7; margin: 0; animation: arkFadeUp .8s .1s cubic-bezier(.22,1,.36,1) both; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div style="margin-bottom:14px;">
  <img src="https://www.arkdev.net/icons/logo-dark.svg"
       style="height:52px;width:auto;opacity:.85;" alt="ArkDev" />
</div>
<div class="ark-hero">
  <div class="ark-title">ArkPanel</div>
  <p class="ark-sub">All company tools — for employees, HR, and leadership</p>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown("")

# ── Systems grid ──────────────────────────────────────────────────────────────
st.subheader("Systems", divider="gray")

SYSTEMS = [
    {
        "icon": "📊", "name": "ArkScore", "active": True, "url": "/arkscore",
        "desc": "EOS L10 weekly scorecard — utilization, operational health, and project tracking.",
        "modules": [
            ("🏆", "L10 Scorecard", "/scorecard"),
            ("📝", "Scorecard Entry", "/scorecard_entry"),
            ("📊", "Utilization", "/utilization_dashboard"),
            ("📤", "Util Check-in", "/utilization_checkin"),
            ("🟢", "Operational Health", "/operational_health"),
            ("✍️", "Projects Check-in", "/weekly_checkin"),
        ],
    },
    {
        "icon": "🏢", "name": "Company Management", "active": True, "url": "/employees",
        "desc": "Employee directory, project management, working patterns, and live availability.",
        "modules": [
            ("👥", "Employees", "/employees"),
            ("⚙️", "Project Management", "/project_management"),
            ("🗓️", "Working Patterns", "/working_patterns"),
            ("📍", "Availability Now", "/availability"),
        ],
    },
    {
        "icon": "⏱️", "name": "Projects Hours Tracking", "active": True, "url": "/project_hours",
        "desc": "Track billable hours per project across the team with Clockify sync and reporting.",
        "modules": [
            ("📋", "Overview", "/project_hours"),
            ("⏱️", "Hours Tracking", "/hours_tracking"),
        ],
    },
    {"icon": "👥", "name": "HR System", "active": False,
     "desc": "Leave management, performance reviews, and employee records."},
    {"icon": "💰", "name": "Finance", "active": False,
     "desc": "Revenue tracking, headcount ratios, and financial reporting."},
    {"icon": "🤝", "name": "BD & Pipeline", "active": False,
     "desc": "Business development conversations, pipeline activity, and conversion tracking."},
]


def _render_card(s: dict) -> None:
    with st.container(border=True):
        st.markdown(f"### {s['icon']}　{s['name']}")
        st.caption(s["desc"])
        if s["active"]:
            modules = s.get("modules", [])
            if modules:
                links = "　·　".join(f"[{ic} {lbl}]({url})" for ic, lbl, url in modules)
                st.markdown(links)
            st.markdown(":green-badge[● Active]")
        else:
            st.markdown(":gray-badge[Coming soon]")


for row_start in range(0, len(SYSTEMS), 3):
    cols = st.columns(3, gap="medium")
    for col, s in zip(cols, SYSTEMS[row_start:row_start + 3]):
        with col:
            _render_card(s)

st.markdown("")
st.caption("Click a module link or use the sidebar to navigate.")
