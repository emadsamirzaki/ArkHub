"""
systems/arkscore/home.py — ArkScore system overview page
"""

import streamlit as st

# Scoped gradient wordmark only; the gradient fill reads on light and dark.
st.markdown(
    """
<style>
.arkscore-title {
    font-size: clamp(2.4rem, 5vw, 4rem); font-weight: 900;
    background: linear-gradient(120deg, #60A5FA 0%, #A78BFA 40%, #F472B6 100%);
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 4px; line-height: 1.05; letter-spacing: -0.03em;
}
.arkscore-sub { font-size: 1.05rem; opacity: .7; margin: 0 0 1rem; }
</style>
<p class="arkscore-title">ArkScore</p>
<p class="arkscore-sub">EOS L10 Weekly Scorecard System</p>
""",
    unsafe_allow_html=True,
)
st.divider()

# ── About card ────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("##### 📌 About ArkScore")
    st.markdown(
        "ArkScore is built on the **Entrepreneurial Operating System (EOS)** framework, "
        "giving leadership teams a single place to track and present key operational metrics "
        "during weekly **L10 meetings**.\n\n"
        "Each module maps to an EOS measurable. Active modules are fully interactive; "
        "locked modules are on the roadmap and will unlock progressively."
    )
    st.markdown(":blue-badge[📅 Weekly L10 Meetings]　:blue-badge[📊 EOS Scorecards]")

st.markdown("")

# ── Body ──────────────────────────────────────────────────────────────────────
col_modules, col_guide = st.columns([3, 2], gap="large")

SCORECARD_MODULES = [
    ("🏆", "L10 Scorecard",              "Weekly leadership dashboard with 10 key metrics",     "scorecard_dashboard.py"),
    ("📝", "L10 Weekly Scorecard Entry", "Enter and update metrics for the leadership meeting", "scorecard_entry.py"),
]

with col_modules:
    st.subheader("🏆 Scorecard Modules", divider="gray")
    for icon, name, desc, page in SCORECARD_MODULES:
        with st.container(border=True):
            st.page_link(f"systems/arkscore/{page}", label=f"**{name}**", icon=icon)
            st.caption(desc)

with col_guide:
    st.subheader("Quick Start", divider="gray")
    st.markdown("**📝 L10 Weekly Scorecard Entry**")
    st.markdown(
        "1. Select the week to enter data\n"
        "2. Fill in metrics for each area (BD, Health, Financial, etc.)\n"
        "3. Add context hints for the AI Adoption metric\n"
        "4. Click **Save Scorecard Entry**"
    )
    st.divider()
    st.markdown("**🏆 L10 Scorecard**")
    st.markdown(
        "1. View all 10 metrics in one dashboard\n"
        "2. Compare week-over-week trends\n"
        "3. See owner assignments and status\n"
        "4. Review colour-coded sections for each area"
    )
