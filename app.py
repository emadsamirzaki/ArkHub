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
        "Scorecard Modules": [
            st.Page("pages/1_Utilization.py",       title="Utilization %",      icon="✅"),
            st.Page("pages/2_Operational_Health.py", title="Operational Health", icon="🔒"),
            st.Page("pages/3_Client_Health.py",      title="Client Health",      icon="🔒"),
            st.Page("pages/4_Process_Compliance.py", title="Process Compliance", icon="🔒"),
            st.Page("pages/5_Revenue_per_Head.py",   title="Revenue per Head",   icon="🔒"),
            st.Page("pages/6_BD_Conversations.py",   title="BD Conversations",   icon="🔒"),
            st.Page("pages/7_Rock_Completion.py",    title="Rock Completion",    icon="🔒"),
        ],
    }
)

pg.run()
