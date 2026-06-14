# NWS Staffing Analysis - Statistical Utilities
# Developed with assistance from Claude Code (Anthropic)
#
# Small statistical helpers shared across analysis and synthesis notebooks.


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
