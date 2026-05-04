"""
app.py — ArkScore navigation controller
"""

import streamlit as st

st.set_page_config(
    page_title="ArkScore",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation(
    {
        "": [
            st.Page("views/home.py", title="Home", icon="🏠", default=True),
        ],
        "Utilization": [
            st.Page("pages/1_Utilization.py", title="Utilization %", icon="✅"),
        ],
        "Operational Health": [
            st.Page("pages/2_Operational_Health.py", title="Dashboard",            icon="📊"),
            st.Page("pages/3_Project_Management.py",  title="Project Management", icon="⚙️"),
            st.Page("pages/4_Weekly_Checkin.py",      title="Weekly Check-in",    icon="✍️"),
        ],
        "Coming Soon": [
            st.Page("pages/5_Client_Health.py",      title="Client Health",      icon="🔒"),
            st.Page("pages/6_Process_Compliance.py", title="Process Compliance", icon="🔒"),
            st.Page("pages/7_Revenue_per_Head.py",   title="Revenue per Head",   icon="🔒"),
            st.Page("pages/8_BD_Conversations.py",   title="BD Conversations",   icon="🔒"),
            st.Page("pages/9_Rock_Completion.py",    title="Rock Completion",    icon="🔒"),
        ],
    }
)

pg.run()
