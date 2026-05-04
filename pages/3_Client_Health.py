"""pages/3_Client_Health.py — Placeholder"""
import streamlit as st

st.set_page_config(
    page_title="Client Health — ArkScore",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("# 🔒 Client Health")
st.markdown("---")
st.info(
    "**This module is coming soon.**\n\n"
    "When built, it will track:\n"
    "- NPS and CSAT scores per client\n"
    "- Active escalations and at-risk accounts\n"
    "- Contract renewal pipeline\n"
    "- QBR completion rates"
)
st.markdown("_Navigate to **Utilization %** in the sidebar to use the active module._")
