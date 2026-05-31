# NWS Staffing Analysis - Shared Constants
# Developed with assistance from Claude Code (Anthropic)
#
# Single source of truth for project-wide constants used across
# 04_eda.ipynb, 05_analysis.ipynb, and 06_synthesis.ipynb.

import pandas as pd

# ── WFO filters ───────────────────────────────────────────────────────────────

NON_CONUS = {"GUM", "HFO", "AFC", "AJK", "PPG", "AFG", "AER"}

# Offices documented as losing overnight coverage (WaPo May 16, 2025 + follow-up)
OVERNIGHT_CLOSED = {"GLD", "JKL", "HNX", "STO", "CYS", "PAH", "MQT"}

# ── Phenomena ─────────────────────────────────────────────────────────────────

PHENOMENA = ["TO", "SV", "FF"]

PHENOMENA_LABELS = {
    "TO": "Tornado",
    "SV": "Severe Thunderstorm",
    "FF": "Flash Flood",
}

# ── Treatment timeline ────────────────────────────────────────────────────────

# Feb 27 2025: probationary terminations
CUT_DATE = pd.Timestamp("2025-02-27", tz="UTC")

# Apr 1 2025: deferred resignations effective — operationally most significant phase
DEPART_DATE = pd.Timestamp("2025-04-01", tz="UTC")

# Aug 1 2025: hiring exemption announced — not a recovery (vacancies persisted through Dec)
REHIRE_DATE = pd.Timestamp("2025-08-01", tz="UTC")

# ── Plot styling ──────────────────────────────────────────────────────────────

# Per-phenomena colors used in EDA and analysis figures
PHENOMENA_COLORS = {
    "TO": "#4a90d9",
    "SV": "#e07b39",
    "FF": "#5aab61",
}

# LSR geography maps (01b, 09a, 09b) use a different palette to distinguish type
LSR_COLORS = {
    "TO": "#d62728",
    "SV": "#bcbd22",
    "FF": "#1f77b4",
}

LSR_SIZES = {
    "TO": 5,
    "SV": 1.5,
    "FF": 3,
}

# CONUS bounding box for geographic plots
CONUS_XLIM = (-125, -66)
CONUS_YLIM = (24, 50)

# FIPS codes to exclude when clipping Census TIGER boundaries to CONUS
# (AK, HI, and US territories)
CONUS_FIPS_EXCLUDE = {"02", "15", "60", "66", "69", "72", "78"}
