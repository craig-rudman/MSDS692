# NWS Staffing Analysis - Statistical Utilities
# Developed with assistance from Claude Code (Anthropic)
#
# Small statistical helpers shared across analysis and synthesis notebooks.

import pandas as pd


def sig_stars(p: float) -> str:
    """Convert a p-value to a significance star string.

    Args:
        p: p-value.

    Returns:
        "***" if p < 0.001, "**" if p < 0.01, "*" if p < 0.05, else "ns".
    """
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def phase_label(row: pd.Series) -> str:
    """Map an events row to its NWS staffing phase label.

    Phases are defined by the known treatment timeline:
        baseline  — 2020–2024 (pre-treatment reference)
        pre       — Jan–Feb 2025 (before probationary terminations)
        post_term — Mar 2025 (post-termination, before departures)
        post_dep  — Apr–Jul 2025 (deferred resignations effective)
        post_hire — Aug–Dec 2025 (hiring exemption announced; no observed recovery)

    Args:
        row: A DataFrame row with integer "year" and integer "month" columns.

    Returns:
        Phase label string.
    """
    if row["year"] < 2025:
        return "baseline"
    m = row["month"]
    if m <= 2:
        return "pre"
    if m == 3:
        return "post_term"
    if m <= 7:
        return "post_dep"
    return "post_hire"
