"""
systems/project_hours/utils/constants.py
Constants for the Projects Hours Tracking system.
"""
from __future__ import annotations

from systems.arkscore.utils.constants import (
    COLOR_CRITICAL,
    COLOR_ON_TARGET,
    COLOR_WATCH,
)

# Tolerance band (±) around the expected burn before a project is flagged
# below / above pace. 0.05 = ±5 %.
TOLERANCE: float = 0.05

# ── Pace status labels ────────────────────────────────────────────────────────
STATUS_IN_RANGE = "In range"
STATUS_BELOW    = "Below pace"   # burned fewer hours than expected by now
STATUS_ABOVE    = "Above pace"   # burned more hours than expected — budget at risk
STATUS_UPCOMING = "Upcoming"     # month hasn't been reached / logged yet

# Neutral grey for not-yet-reached months
COLOR_UPCOMING = "#64748B"

STATUS_COLORS: dict[str, str] = {
    STATUS_IN_RANGE: COLOR_ON_TARGET,  # green
    STATUS_BELOW:    COLOR_CRITICAL,   # red
    STATUS_ABOVE:    COLOR_WATCH,      # amber
    STATUS_UPCOMING: COLOR_UPCOMING,   # grey
}

STATUS_ICONS: dict[str, str] = {
    STATUS_IN_RANGE: "🟢",
    STATUS_BELOW:    "🔴",
    STATUS_ABOVE:    "🟡",
    STATUS_UPCOMING: "⚪",
}
