"""
views/home.py — ArkPanel platform homepage
"""

import streamlit as st

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

@keyframes gradientFlow {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes heroFadeUp {
    from { opacity: 0; transform: translateY(28px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes subFadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes glowPulse {
    0%, 100% { filter: drop-shadow(0 0 18px rgba(96,165,250,0.4)) drop-shadow(0 0 48px rgba(167,139,250,0.2)); }
    50%       { filter: drop-shadow(0 0 36px rgba(96,165,250,0.7)) drop-shadow(0 0 80px rgba(167,139,250,0.4)); }
}

.platform-hero {
    text-align: center;
    padding: 48px 0 20px 0;
    width: 100%;
    overflow: visible;
}
.platform-title {
    font-size: 10vw !important;
    font-weight: 900 !important;
    white-space: nowrap !important;
    display: block !important;
    background: linear-gradient(270deg, #60A5FA, #A78BFA, #F472B6, #A78BFA, #60A5FA) !important;
    background-size: 300% 300% !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    margin: 0 0 16px 0 !important;
    line-height: 1.0 !important;
    letter-spacing: -0.04em !important;
    animation:
        heroFadeUp   0.7s cubic-bezier(0.22,1,0.36,1) both,
        gradientFlow 5s ease infinite,
        glowPulse    3s ease-in-out infinite;
}
.platform-sub {
    font-size: 1.2rem !important;
    color: #94A3B8 !important;
    margin: 0 0 2.5rem 0 !important;
    animation: subFadeUp 0.9s 0.2s cubic-bezier(0.22,1,0.36,1) both;
    letter-spacing: 0.02em !important;
}

.system-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px;
    margin-top: 8px;
}
.system-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 24px 22px;
    transition: border-color 0.2s, transform 0.15s;
    cursor: default;
    text-decoration: none;
    display: block;
}
.system-card.active {
    border-color: #3B82F6;
    background: linear-gradient(135deg, #172554 0%, #1e1b4b 100%);
    cursor: pointer;
}
.system-card.active:hover {
    border-color: #60A5FA;
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(59,130,246,0.25);
}
.system-card-icon  { font-size: 2rem; margin-bottom: 10px; }
.system-card-name  { font-size: 1.05rem; font-weight: 700; color: #F1F5F9; margin: 0 0 4px 0; }
.system-card-desc  { font-size: 0.82rem; color: #64748B; margin: 0 0 14px 0; line-height: 1.5; }
.badge-active {
    display: inline-block;
    background: #1D4ED8;
    color: #BFDBFE;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 999px;
}
.badge-soon {
    display: inline-block;
    background: #334155;
    color: #94A3B8;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 999px;
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
       style="height: 56px; width: auto; opacity: 0.85;" alt="ArkDev Logo" />
</div>
<div class="platform-hero">
  <div class="platform-title">ArkPanel</div>
  <div class="platform-sub">All company tools — for employees, HR, and leadership</div>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown("---")

# ── Systems grid ──────────────────────────────────────────────────────────────
st.markdown("### Systems")

SYSTEMS = [
    {
        "icon":   "📊",
        "name":   "ArkScore",
        "desc":   "EOS L10 weekly scorecard — utilization, operational health, and project tracking.",
        "active": True,
        "url":    "/arkscore",
    },
    {
        "icon":   "📍",
        "name":   "Workforce",
        "desc":   "Working patterns, live team availability, and daily schedules.",
        "active": True,
        "url":    "/availability",
    },
    {
        "icon":   "👥",
        "name":   "HR System",
        "desc":   "Leave management, performance reviews, and employee records.",
        "active": False,
    },
    {
        "icon":   "💰",
        "name":   "Finance",
        "desc":   "Revenue tracking, headcount ratios, and financial reporting.",
        "active": False,
    },
    {
        "icon":   "🤝",
        "name":   "BD & Pipeline",
        "desc":   "Business development conversations, pipeline activity, and conversion tracking.",
        "active": False,
    },
]

cards_html = '<div class="system-grid">'
for s in SYSTEMS:
    card_class  = "system-card active" if s["active"] else "system-card"
    badge_class = "badge-active" if s["active"] else "badge-soon"
    badge_text  = "Active" if s["active"] else "Coming Soon"
    inner = f"""
  <div class="system-card-icon">{s['icon']}</div>
  <p class="system-card-name">{s['name']}</p>
  <p class="system-card-desc">{s['desc']}</p>
  <span class="{badge_class}">{badge_text}</span>"""
    if s.get("url"):
        cards_html += f'<a href="{s["url"]}" class="{card_class}" target="_self">{inner}</a>'
    else:
        cards_html += f'<div class="{card_class}">{inner}</div>'
cards_html += "</div>"

st.markdown(cards_html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<p style='font-size:0.8rem;color:#475569;'>Click an active system card to open it, or use the sidebar to navigate.</p>",
    unsafe_allow_html=True,
)
