# NWS Staffing Analysis - Project-Wide Constants
# Developed with assistance from Claude Code (Anthropic)
#
# Single source of truth for constants shared across pipeline stages
# (cleaning, analysis). Stage-specific packages import from here rather
# than re-declaring values, so a change lands in exactly one place.

import pandas as pd

# ── Treatment timeline ────────────────────────────────────────────────────────

# Feb 27 2025: probationary terminations. This date anchors the Spring season
# boundary in cleaning (see cleaner.SEASON_BOUNDS), so every *-Spring season
# aligns to the same treatment-relative boundary across years. Lives here, in the
# shared module, because cleaning derives the season windows from it.
CUT_DATE = pd.Timestamp("2025-02-27", tz="UTC")

# ── WFO filters ───────────────────────────────────────────────────────────────

# Weather Forecast Offices (WFOs) outside the continental United States
# (CONUS): Guam (GUM), Honolulu (HFO), the Alaska offices (AFC, AJK, AFG, AER),
# and Pago Pago (PPG). The study footprint is CONUS only, so these offices are
# clipped out in cleaning (see COWCleaner.clip_to_conus).
NON_CONUS = {"GUM", "HFO", "AFC", "AJK", "PPG", "AFG", "AER"}
