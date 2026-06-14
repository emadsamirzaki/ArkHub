"""
systems/utils/ui.py — shared, theme-aware UI helpers for ArkPanel.

Streamlit does not reliably expose the active theme's colours to custom
st.markdown HTML, so these helpers lean on native widgets that re-theme
themselves automatically when the user switches between the light and dark
themes (configured in .streamlit/config.toml). Pages should use these instead
of hand-rolled HTML with hardcoded hex.
"""

from __future__ import annotations

import streamlit as st

# Map domain statuses to Streamlit's semantic colour names. The actual hexes
# for each name are set per-theme in config.toml (greenColor/redColor/…), so
# badges and coloured text flip with the active theme.
_STATUS_COLOR = {
    "On Track":   "green",
    "On Target":  "green",
    "Watch":      "orange",
    "Off Track":  "red",
    "Critical":   "red",
    "Awaiting":   "gray",
    "Active":     "green",
    "Inactive":   "gray",
}


def section(title: str, divider: str = "gray") -> None:
    """Consistent section header used across every page.

    Renders a native subheader with a coloured underline — theme-aware and
    far more legible than the old 0.7rem uppercase labels.
    """
    st.subheader(title, divider=divider)


def status_color(label: str) -> str:
    """Return the Streamlit colour name for a status label (default gray)."""
    key = label.strip().lstrip("🟢🔴🟡⚫⏳ ").strip()
    return _STATUS_COLOR.get(key, "gray")


def status_badge(label: str, *, color: str | None = None) -> str:
    """Inline badge markdown for a status (e.g. ':green-badge[On Track]').

    Use inside st.markdown / st.write. Colour flips with the theme.
    """
    name = color or status_color(label)
    return f":{name}-badge[{label}]"
