"""
app.py — ArkHub navigation controller
"""

import streamlit as st

st.set_page_config(
    page_title="ArkHub",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation(
    {
        "": [
            st.Page("views/home.py", title="Home", icon="🏠", default=True, url_path=""),
        ],
        "ArkScore": [
            st.Page("systems/arkscore/home.py",                    title="Overview",              icon="📋", url_path="arkscore"),
            st.Page("systems/arkscore/utilization_dashboard.py",   title="Utilization Dashboard", icon="📊"),
            st.Page("systems/arkscore/utilization_checkin.py",     title="Utilization Check-in",  icon="📤"),
            st.Page("systems/arkscore/operational_health.py",      title="Operational Health",    icon="🟢"),
            st.Page("systems/arkscore/weekly_checkin.py",          title="Weekly Check-in",       icon="✍️"),
            st.Page("systems/arkscore/project_management.py",      title="Project Management",    icon="⚙️"),
        ],
        "Company": [
            st.Page("systems/people/employees.py",        title="Employees",        icon="👥"),
        ],
        "Workforce": [
            st.Page("systems/people/working_patterns.py", title="Working Patterns", icon="🗓️"),
            st.Page("systems/people/availability.py",     title="Availability Now", icon="📍", url_path="availability"),
        ],
        # Add new systems here as new sections, e.g.:
        # "HR System": [
        #     st.Page("systems/hr/home.py", title="Overview", icon="🏢"),
        # ],
    }
)

pg.run()
