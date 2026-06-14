"""
app.py — ArkPanel navigation controller
"""

import streamlit as st

st.set_page_config(
    page_title="ArkPanel",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide the built-in st.navigation sidebar; we render our own below.
# (Fonts, colours and borders are handled by the theme in .streamlit/config.toml.)
st.markdown(
    '<style>[data-testid="stSidebarNav"]{display:none!important;}</style>',
    unsafe_allow_html=True,
)

# Register all pages for URL-based routing
pg = st.navigation(
    {
        "": [
            st.Page("views/home.py", title="Home", icon="🏠", default=True, url_path=""),
        ],
        "ArkScore": [
            st.Page("systems/arkscore/home.py",                    title="Overview",                       icon="📋", url_path="arkscore"),
            st.Page("systems/arkscore/scorecard_dashboard.py",     title="L10 Scorecard",                  icon="🏆", url_path="scorecard"),
            st.Page("systems/arkscore/scorecard_entry.py",         title="L10 Weekly Scorecard Entry",     icon="📝", url_path="scorecard_entry"),
            st.Page("systems/arkscore/utilization_dashboard.py",   title="Utilization Dashboard", icon="📊"),
            st.Page("systems/arkscore/utilization_checkin.py",     title="Utilization Check-in",  icon="📤"),
            st.Page("systems/arkscore/operational_health.py",      title="Operational Health",    icon="🟢"),
            st.Page("systems/arkscore/weekly_checkin.py",          title="Projects Weekly Check-in", icon="✍️"),
        ],
        "Company Management": [
            st.Page("systems/people/employees.py",        title="Employees",        icon="👥"),
            st.Page("systems/arkscore/project_management.py", title="Project Management", icon="⚙️"),
            st.Page("systems/people/working_patterns.py", title="Working Patterns", icon="🗓️"),
            st.Page("systems/people/availability.py",     title="Availability Now", icon="📍", url_path="availability"),
        ],
        "Projects Hours Tracking": [
            st.Page("systems/project_hours/home.py",          title="Overview",       icon="📋", url_path="project_hours"),
            st.Page("systems/project_hours/hours_tracking.py", title="Hours Tracking", icon="⏱️"),
        ],
    }
)

# ── Custom sidebar navigation ──────────────────────────────────────────────────
with st.sidebar:
    st.page_link("views/home.py", label="Home", icon="🏠")

    with st.expander("📊 ArkScore", expanded=True):
        st.page_link("systems/arkscore/home.py", label="Overview", icon="📋")

        st.caption("Scorecard")
        st.page_link("systems/arkscore/scorecard_dashboard.py", label="L10 Scorecard", icon="🏆")
        st.page_link("systems/arkscore/scorecard_entry.py",     label="L10 Weekly Scorecard Entry",     icon="📝")

        st.caption("Utilization")
        st.page_link("systems/arkscore/utilization_dashboard.py", label="Dashboard", icon="📊")
        st.page_link("systems/arkscore/utilization_checkin.py",   label="Check-in",  icon="📤")

        st.caption("Operational Health")
        st.page_link("systems/arkscore/operational_health.py",  label="Operational Health", icon="🟢")
        st.page_link("systems/arkscore/weekly_checkin.py",      label="Projects Weekly Check-in", icon="✍️")

    with st.expander("🏢 Company Management", expanded=False):
        st.page_link("systems/people/employees.py",            label="Employees", icon="👥")
        st.page_link("systems/arkscore/project_management.py", label="Project Management", icon="⚙️")

    with st.expander("⏱️ Projects Hours Tracking", expanded=False):
        st.page_link("systems/project_hours/home.py", label="Overview", icon="📋")
        st.page_link("systems/project_hours/hours_tracking.py", label="Hours Tracking", icon="⏱️")

    with st.expander("📍 Workforce", expanded=False):
        st.page_link("systems/people/working_patterns.py", label="Working Patterns", icon="🗓️")
        st.page_link("systems/people/availability.py",     label="Availability Now", icon="📍")

pg.run()
