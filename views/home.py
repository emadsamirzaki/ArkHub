"""
views/home.py — ArkScore home page content
(st.set_page_config is handled by app.py via st.navigation)
"""

import streamlit as st

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.hero-title {
    font-size: 6.5rem !important;
    font-weight: 900 !important;
    background: linear-gradient(120deg, #60A5FA 0%, #A78BFA 40%, #F472B6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 6px 0 !important;
    line-height: 1.0 !important;
    letter-spacing: -0.03em;
    filter: drop-shadow(0 0 32px rgba(99,102,241,0.45));
    display: block;
}
.hero-sub {
    font-size: 1.15rem;
    color: #94A3B8;
    margin: 0 0 2rem 0;
    letter-spacing: 0.02em;
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

/* ── About card ─────────────────────────────── */
.about-card {
    background: linear-gradient(135deg, #0F2044 0%, #1E1B4B 100%);
    border: 1px solid #3B82F6;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 28px;
}
.about-card-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #93C5FD;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 14px 0;
}
.about-card-body {
    color: #CBD5E1;
    font-size: 0.93rem;
    line-height: 1.75;
    margin: 0 0 18px 0;
}
.about-pill-row { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 4px; }
.about-pill {
    background: #1E3A5F;
    border: 1px solid #2563EB;
    border-radius: 999px;
    padding: 5px 14px;
    font-size: 0.78rem;
    font-weight: 600;
    color: #93C5FD;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div style="margin-bottom: 20px;">
  <img src="https://www.arkdev.net/icons/logo-dark.svg"
       style="height: 72px; width: auto;" alt="ArkDev Logo" />
</div>
<p class="hero-title" style="text-align:center;">ArkScore</p>
<p class="hero-sub" style="text-align:center;">EOS L10 Weekly Meeting Scorecard Dashboard</p>
""",
    unsafe_allow_html=True,
)
st.markdown("---")

# ── About ArkScore (full-width highlighted card) ─────────────────────────────
st.markdown(
    """
<div class="about-card">
  <p class="about-card-title">📌 About ArkScore</p>
  <p class="about-card-body">
    ArkScore is built on the <strong style="color:#93C5FD;">Entrepreneurial Operating System (EOS)</strong>
    framework, giving leadership teams a single place to track and present key operational
    metrics during weekly <strong style="color:#93C5FD;">L10 meetings</strong>.<br><br>
    Each scorecard module maps to an EOS measurable. Active modules are fully interactive;
    locked modules are on the roadmap and will unlock progressively.
  </p>
  <div class="about-pill-row">
    <span class="about-pill">📅 Weekly L10 Meetings</span>
    <span class="about-pill">📊 EOS Scorecards</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Body ──────────────────────────────────────────────────────────────────────
col_modules, col_guide = st.columns([3, 2], gap="large")

MODULES = [
    ("✅", "Utilization %",      "Team time utilisation vs. 35 h weekly target", True),
    ("✅", "Operational Health", "Project delivery status, weekly check-ins, health score", True),
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
        "**Utilization %**\n\n"
        "**1.** Open **Utilization %** in the sidebar  \n"
        "**2.** Upload your Clockify Detailed Report CSV  \n"
        "**3.** Confirm the auto-detected week label  \n"
        "**4.** Review metrics and present in your L10 meeting\n\n"
        "---\n\n"
        "**Operational Health**\n\n"
        "**1.** Add projects in **Project Management**  \n"
        "**2.** PMs submit check-ins in **Weekly Check-in**  \n"
        "**3.** Open **Operational Health → Dashboard** during L10"
    )
