"""
systems/arkscore/home.py — ArkScore system overview page
"""

import streamlit as st

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.arkscore-title {
    font-size: 4.5rem;
    font-weight: 900;
    background: linear-gradient(120deg, #60A5FA 0%, #A78BFA 40%, #F472B6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 6px 0;
    line-height: 1.05;
    letter-spacing: -0.03em;
    filter: drop-shadow(0 0 28px rgba(99,102,241,0.4));
}
.arkscore-sub {
    font-size: 1.05rem;
    color: #94A3B8;
    margin: 0 0 2rem 0;
}

.about-card {
    background: linear-gradient(135deg, #0F2044 0%, #1E1B4B 100%);
    border: 1px solid #3B82F6;
    border-radius: 16px;
    padding: 26px 30px;
    margin-bottom: 24px;
}
.about-card-title {
    font-size: 1rem;
    font-weight: 700;
    color: #93C5FD;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 12px 0;
}
.about-card-body {
    color: #CBD5E1;
    font-size: 0.9rem;
    line-height: 1.75;
    margin: 0 0 16px 0;
}
.about-pill-row { display: flex; flex-wrap: wrap; gap: 10px; }
.about-pill {
    background: #1E3A5F;
    border: 1px solid #2563EB;
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 0.76rem;
    font-weight: 600;
    color: #93C5FD;
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
}
.module-row.active { border-color: #3B82F6; background: #172554; }
.module-icon { font-size: 1.4rem; line-height: 1; padding-top: 2px; }
.module-name { font-weight: 600; font-size: 0.92rem; color: #E2E8F0; }
.module-desc { font-size: 0.78rem; color: #64748B; margin-top: 2px; }
.badge-active {
    display: inline-block; background: #1D4ED8; color: #BFDBFE;
    font-size: 0.68rem; font-weight: 700; padding: 2px 8px;
    border-radius: 999px; margin-left: 8px; vertical-align: middle;
}
.badge-soon {
    display: inline-block; background: #334155; color: #94A3B8;
    font-size: 0.68rem; font-weight: 700; padding: 2px 8px;
    border-radius: 999px; margin-left: 8px; vertical-align: middle;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
<p class="arkscore-title">ArkScore</p>
<p class="arkscore-sub">EOS L10 Weekly Scorecard System</p>
""",
    unsafe_allow_html=True,
)
st.markdown("---")

# ── About card ────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="about-card">
  <p class="about-card-title">📌 About ArkScore</p>
  <p class="about-card-body">
    ArkScore is built on the <strong style="color:#93C5FD;">Entrepreneurial Operating System (EOS)</strong>
    framework, giving leadership teams a single place to track and present key operational
    metrics during weekly <strong style="color:#93C5FD;">L10 meetings</strong>.<br><br>
    Each module maps to an EOS measurable. Active modules are fully interactive;
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

SCORECARD_MODULES = [
    ("🏆", "L10 Scorecard",              "Weekly leadership dashboard with 10 key metrics",                  "scorecard"),
    ("📝", "L10 Weekly Scorecard Entry", "Enter and update metrics for the leadership meeting",              "scorecard_entry"),
]

with col_modules:
    st.markdown("### 🏆 Scorecard Modules")
    for icon, name, desc, url_path in SCORECARD_MODULES:
        st.markdown(
            f"""
<div class="module-row active">
  <div class="module-icon">{icon}</div>
  <div style="flex: 1;">
    <a href="/{url_path}" style="text-decoration: none; color: inherit;">
      <span class="module-name">{name}</span>
      <span class="badge-active">Active</span>
      <div class="module-desc">{desc}</div>
    </a>
  </div>
</div>""",
            unsafe_allow_html=True,
        )

with col_guide:
    st.markdown("### Quick Start")
    st.info(
        "**📝 L10 Weekly Scorecard Entry**\n\n"
        "**1.** Select the week to enter data\n"
        "**2.** Fill in metrics for each area (BD, Health, Financial, etc.)\n"
        "**3.** Add context hints for AI Adoption metric\n"
        "**4.** Click **Save Scorecard Entry**\n\n"
        "---\n\n"
        "**🏆 L10 Scorecard**\n\n"
        "**1.** View all 10 metrics in one dashboard\n"
        "**2.** Compare week-over-week trends\n"
        "**3.** See owner assignments and status\n"
        "**4.** Review color-coded sections for each area"
    )
