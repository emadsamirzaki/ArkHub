"""
app.py — ArkScore home page
"""

import streamlit as st

st.set_page_config(
    page_title="ArkScore — L10 Meeting Scorecard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.hero-title {
    font-size: 3.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 4px 0;
    line-height: 1.1;
}
.hero-sub {
    font-size: 1.1rem;
    color: #94A3B8;
    margin: 0 0 2rem 0;
}
.module-row {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}
.module-row.active {
    border-color: #3B82F6;
    background: #172554;
}
.module-icon { font-size: 1.5rem; line-height: 1; padding-top: 2px; }
.module-name { font-weight: 600; font-size: 0.95rem; color: #E2E8F0; }
.module-desc { font-size: 0.8rem; color: #64748B; margin-top: 2px; }
.module-badge-active {
    display: inline-block;
    background: #1D4ED8;
    color: #BFDBFE;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    margin-left: 8px;
    vertical-align: middle;
}
.module-badge-soon {
    display: inline-block;
    background: #334155;
    color: #94A3B8;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    margin-left: 8px;
    vertical-align: middle;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">ArkScore</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">EOS L10 Weekly Meeting Scorecard Dashboard</p>',
    unsafe_allow_html=True,
)
st.markdown("---")

# ── Body ──────────────────────────────────────────────────────────────────────
col_modules, col_guide = st.columns([3, 2], gap="large")

MODULES = [
    ("✅", "Utilization %",      "Team time utilisation vs. 35 h weekly target", True),
    ("🔒", "Operational Health", "SLAs, resolution times, uptime metrics",        False),
    ("🔒", "Client Health",      "NPS, satisfaction scores, escalation tracking", False),
    ("🔒", "Process Compliance", "Checklist adherence and process audit results",  False),
    ("🔒", "Revenue per Head",   "Revenue efficiency and headcount ratios",        False),
    ("🔒", "BD Conversations",   "Pipeline activity, outreach, and conversion",    False),
    ("🔒", "Rock Completion",    "Quarterly rock progress and completion rates",    False),
]

with col_modules:
    st.markdown("### Scorecard Modules")
    for icon, name, desc, active in MODULES:
        row_class   = "module-row active" if active else "module-row"
        badge_class = "module-badge-active" if active else "module-badge-soon"
        badge_text  = "Active" if active else "Coming Soon"
        st.markdown(
            f"""
<div class="{row_class}">
  <div class="module-icon">{icon}</div>
  <div>
    <span class="module-name">{name}</span>
    <span class="{badge_class}">{badge_text}</span>
    <div class="module-desc">{desc}</div>
  </div>
</div>""",
            unsafe_allow_html=True,
        )

with col_guide:
    st.markdown("### Quick Start")
    st.info(
        "**1.** Open **Utilization %** in the sidebar  \n"
        "**2.** Upload your Clockify Detailed Report CSV  \n"
        "**3.** Confirm the auto-detected week label  \n"
        "**4.** Review all metrics and present in your L10 meeting"
    )

    st.markdown("### About ArkScore")
    st.markdown(
        """
Built on the **Entrepreneurial Operating System (EOS)** framework, ArkScore
gives leadership teams a single place to track and present key operational
metrics during weekly **L10 meetings**.

Each scorecard module maps to an EOS measurable. Active modules are fully
interactive; locked modules are on the roadmap.
"""
    )

    st.markdown("### Framework")
    st.markdown(
        """
| Threshold | Status |
|-----------|--------|
| ≥ 80 % | 🟢 On Target |
| 60 – 79 % | 🟡 Watch |
| < 60 % | 🔴 Critical |
"""
    )
