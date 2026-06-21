# NWS Staffing Analysis - Shared Constants
# Developed with assistance from Claude Code (Anthropic)
#
# Single source of truth for project-wide constants used across
# 04_eda.ipynb, 05_analysis.ipynb, and 06_synthesis.ipynb.

# ── WFO filters ───────────────────────────────────────────────────────────────

# Re-exported from the project-wide module so the non-CONUS office list lives in
# exactly one place (src/constants.py), shared with the cleaning stage.
# 05_analysis.ipynb imports NON_CONUS from here; __all__ marks it as an
# intentional re-export, not a stray import.
from src.constants import NON_CONUS

__all__ = ["NON_CONUS"]

# ── Phenomena ─────────────────────────────────────────────────────────────────

PHENOMENA = ["TO", "SV", "FF"]

PHENOMENA_LABELS = {
    "TO": "Tornado",
    "SV": "Severe Thunderstorm",
    "FF": "Flash Flood",
}

# ── Study-year calendar mapping ───────────────────────────────────────────────

# Study year is a 1-based treatment-relative index: study year 1 is calendar 2016,
# study year 10 is calendar 2025. Add this offset to convert a study year to its
# calendar year for axis labelling. The models still use the numeric study_year;
# only the displayed axis is in calendar terms.
STUDY_YEAR_OFFSET = 2015


def study_year_to_calendar(study_year):
    """Convert a 1-based study year (or array of them) to its calendar year."""
    return study_year + STUDY_YEAR_OFFSET


# ── Plot styling ──────────────────────────────────────────────────────────────

# Per-phenomena colors used in EDA and analysis figures
PHENOMENA_COLORS = {
    "TO": "#4a90d9",
    "SV": "#e07b39",
    "FF": "#5aab61",
}

LSR_SIZES = {
    "TO": 5,
    "SV": 1.5,
    "FF": 3,
}

# CONUS bounding box for geographic plots
CONUS_XLIM = (-125, -66)
CONUS_YLIM = (24, 50)
