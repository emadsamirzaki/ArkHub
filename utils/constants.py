# ── Calculation constants ─────────────────────────────────────────────────────
TARGET_HOURS: float = 35.0  # 7 hrs/day × 5 days/week

# ── Status thresholds (%) ─────────────────────────────────────────────────────
ON_TARGET_THRESHOLD: float = 80.0   # >= 80 %  → On Target
WATCH_THRESHOLD: float     = 60.0   # 60–79 %  → Watch
                                     # < 60 %   → Critical

# ── Status labels ─────────────────────────────────────────────────────────────
STATUS_ON_TARGET = "🟢 On Target"
STATUS_WATCH     = "🟡 Watch"
STATUS_CRITICAL  = "🔴 Critical"

# ── Colour palette ────────────────────────────────────────────────────────────
COLOR_ON_TARGET = "#22C55E"   # green
COLOR_WATCH     = "#F59E0B"   # amber
COLOR_CRITICAL  = "#EF4444"   # red
COLOR_BG        = "#0F172A"   # deep-navy background
COLOR_CARD      = "#1E293B"   # card surface
COLOR_BORDER    = "#334155"   # card border
COLOR_TEXT      = "#F8FAFC"   # primary text
COLOR_MUTED     = "#94A3B8"   # muted / label text

# ── Required columns in the Clockify Detailed Report CSV ─────────────────────
REQUIRED_COLUMNS: list[str] = [
    "Project",
    "Client",
    "Description",
    "Task",
    "User",
    "Group",
    "Email",
    "Tags",
    "Billable",
    "Start Date",
    "Start Time",
    "End Date",
    "End Time",
    "Duration (h)",
    "Duration (decimal)",
    "Billable Rate (EGP)",
    "Billable Amount (EGP)",
    "Date of creation",
]
