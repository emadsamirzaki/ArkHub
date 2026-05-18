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

# Hide the built-in st.navigation sidebar; we render our own below
st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }

/* Section labels inside the custom sidebar */
.sidebar-section-label {
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    color: #475569 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    padding: 10px 0 4px 2px !important;
    display: block !important;
}
/* Top-level section labels (Company, etc.) */
.sidebar-top-label {
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    color: #64748B !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    padding: 16px 0 4px 2px !important;
    display: block !important;
    border-top: 1px solid #1E293B !important;
    margin-top: 4px !important;
}
</style>
""", unsafe_allow_html=True)

# Register all pages for URL-based routing
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
            st.Page("systems/arkscore/weekly_checkin.py",          title="Projects Weekly Check-in", icon="✍️"),
            st.Page("systems/arkscore/project_management.py",      title="Project Management",    icon="⚙️"),
        ],
        "Company Management": [
            st.Page("systems/people/employees.py",        title="Employees",        icon="👥"),
            st.Page("systems/people/working_patterns.py", title="Working Patterns", icon="🗓️"),
            st.Page("systems/people/availability.py",     title="Availability Now", icon="📍", url_path="availability"),
        ],
    }
)

# ── Custom sidebar navigation ──────────────────────────────────────────────────
with st.sidebar:
    st.page_link("views/home.py", label="Home", icon="🏠")

    st.markdown('<span class="sidebar-top-label">ArkScore</span>', unsafe_allow_html=True)
    with st.expander("📊 ArkScore", expanded=True):
        st.page_link("systems/arkscore/home.py", label="Overview", icon="📋")

        st.markdown('<span class="sidebar-section-label">Utilization</span>', unsafe_allow_html=True)
        st.page_link("systems/arkscore/utilization_dashboard.py", label="Dashboard", icon="📊")
        st.page_link("systems/arkscore/utilization_checkin.py",   label="Check-in",  icon="📤")

        st.markdown('<span class="sidebar-section-label">Operational Health</span>', unsafe_allow_html=True)
        st.page_link("systems/arkscore/operational_health.py",  label="Operational Health", icon="🟢")
        st.page_link("systems/arkscore/weekly_checkin.py",      label="Projects Weekly Check-in", icon="✍️")
        st.page_link("systems/arkscore/project_management.py",  label="Project Management", icon="⚙️")

    st.markdown('<span class="sidebar-top-label">Workforce</span>', unsafe_allow_html=True)
    with st.expander("📍 Workforce", expanded=False):
        st.page_link("systems/people/working_patterns.py", label="Working Patterns", icon="🗓️")
        st.page_link("systems/people/availability.py",     label="Availability Now", icon="📍")

    st.markdown('<span class="sidebar-top-label">Company Management</span>', unsafe_allow_html=True)
    st.page_link("systems/people/employees.py", label="Employees", icon="👥")

pg.run()
