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
}
.system-card-icon  { font-size: 2rem; margin-bottom: 10px; }
.system-card-name  { font-size: 1.05rem; font-weight: 700; color: #F1F5F9; margin: 0 0 4px 0; }
.system-card-name a {
    color: #F1F5F9; text-decoration: none;
    transition: color 0.15s;
}
.system-card-name a:hover { color: #93C5FD; }
.system-card-desc  { font-size: 0.82rem; color: #64748B; margin: 0 0 12px 0; line-height: 1.5; }
.module-links {
    display: flex; flex-wrap: wrap; gap: 6px;
    margin: 0 0 14px 0;
}
.module-link {
    display: inline-block;
    background: rgba(59,130,246,0.1);
    border: 1px solid rgba(59,130,246,0.22);
    color: #93C5FD;
    font-size: 0.72rem; font-weight: 600;
    padding: 4px 10px; border-radius: 6px;
    text-decoration: none;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.module-link:hover {
    background: rgba(59,130,246,0.22);
    border-color: rgba(96,165,250,0.5);
    color: #BFDBFE;
}
.badge-active {
    display: inline-block;
    background: #1D4ED8;
    color: #BFDBFE;
    font-size: 0.7rem; font-weight: 700;
    padding: 3px 10px; border-radius: 999px;
}
.badge-soon {
    display: inline-block;
    background: #334155;
    color: #94A3B8;
    font-size: 0.7rem; font-weight: 700;
    padding: 3px 10px; border-radius: 999px;
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
        "modules": [
            {"icon": "🏆", "label": "L10 Scorecard",         "url": "/scorecard"},
            {"icon": "📝", "label": "Scorecard Entry",        "url": "/scorecard_entry"},
            {"icon": "📊", "label": "Utilization Dashboard",  "url": "/utilization_dashboard"},
            {"icon": "📤", "label": "Utilization Check-in",   "url": "/utilization_checkin"},
            {"icon": "🟢", "label": "Operational Health",     "url": "/operational_health"},
            {"icon": "✍️", "label": "Projects Check-in",      "url": "/weekly_checkin"},
        ],
    },
    {
        "icon":   "🏢",
        "name":   "Company Management",
        "desc":   "Employee directory, project management, working patterns, and live availability.",
        "active": True,
        "url":    "/employees",
        "modules": [
            {"icon": "👥", "label": "Employees",          "url": "/employees"},
            {"icon": "⚙️", "label": "Project Management", "url": "/project_management"},
            {"icon": "🗓️", "label": "Working Patterns",   "url": "/working_patterns"},
            {"icon": "📍", "label": "Availability Now",   "url": "/availability"},
        ],
    },
    {
        "icon":   "⏱️",
        "name":   "Projects Hours Tracking",
        "desc":   "Track billable hours per project across the team with Clockify sync and reporting.",
        "active": True,
        "url":    "/project_hours",
        "modules": [
            {"icon": "📋", "label": "Overview",       "url": "/project_hours"},
            {"icon": "⏱️", "label": "Hours Tracking", "url": "/hours_tracking"},
        ],
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
    is_active   = s["active"]
    card_class  = "system-card active" if is_active else "system-card"
    badge_class = "badge-active" if is_active else "badge-soon"
    badge_text  = "Active" if is_active else "Coming Soon"
    modules     = s.get("modules", [])

    name_html = (
        f'<a href="{s["url"]}" target="_self">{s["name"]}</a>'
        if is_active and s.get("url") else s["name"]
    )

    module_html = ""
    if modules:
        links = "".join(
            f'<a href="{m["url"]}" class="module-link" target="_self">{m["icon"]} {m["label"]}</a>'
            for m in modules
        )
        module_html = f'<div class="module-links">{links}</div>'

    inner = (
        f'<div class="system-card-icon">{s["icon"]}</div>'
        f'<p class="system-card-name">{name_html}</p>'
        f'<p class="system-card-desc">{s["desc"]}</p>'
        f'{module_html}'
        f'<span class="{badge_class}">{badge_text}</span>'
    )
    cards_html += f'<div class="{card_class}">{inner}</div>'
cards_html += "</div>"

st.markdown(cards_html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<p style='font-size:0.8rem;color:#475569;'>Click a module link or use the sidebar to navigate.</p>",
    unsafe_allow_html=True,
)
