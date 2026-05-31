# NWS Staffing Analysis - Data Loading and Filtering
# Developed with assistance from Claude Code (Anthropic)
#
# Canonical data loading, CONUS filtering, and top-quartile WFO selection.
# All notebooks should import from here rather than re-deriving these operations.

from pathlib import Path

import numpy as np
import pandas as pd

from .constants import NON_CONUS, PHENOMENA


def load_events(clean_dir: Path) -> pd.DataFrame:
    """Load and prepare the cleaned events table.

    Parses issue/expire as UTC datetimes and adds year_month and month
    convenience columns used throughout the analysis notebooks.

    Args:
        clean_dir: Path to the data/03_cleaning/ directory.

    Returns:
        DataFrame with one row per warning event, datetime columns parsed.
    """
    df = pd.read_csv(
        clean_dir / "events.csv",
        parse_dates=["issue", "expire"],
    )
    df["issue"]      = pd.to_datetime(df["issue"],  utc=True)
    df["expire"]     = pd.to_datetime(df["expire"], utc=True)
    df["year_month"] = df["issue"].dt.to_period("M")
    df["month"]      = df["issue"].dt.month
    return df


def load_stormreports(clean_dir: Path) -> pd.DataFrame:
    """Load and prepare the cleaned storm reports table.

    Args:
        clean_dir: Path to the data/03_cleaning/ directory.

    Returns:
        DataFrame with one row per LSR, valid column parsed as UTC datetime.
    """
    df = pd.read_csv(clean_dir / "stormreports.csv", parse_dates=["valid"])
    df["valid"]      = pd.to_datetime(df["valid"], utc=True)
    df["year_month"] = df["valid"].dt.to_period("M")
    return df


def filter_conus(events: pd.DataFrame) -> pd.DataFrame:
    """Return CONUS-only events with analysis helper columns added.

    Drops non-CONUS WFOs and adds year2025 (0/1 indicator used in logistic
    regression models).

    Args:
        events: Full events DataFrame from load_events().

    Returns:
        Filtered DataFrame restricted to CONUS WFOs.
    """
    conus = events[~events["wfo"].isin(NON_CONUS)].copy()
    conus["year2025"] = (conus["year"] == 2025).astype(int)
    return conus


def get_p75_wfos(events: pd.DataFrame) -> dict[str, set]:
    """Compute top-quartile WFO sets by phenomena from baseline years.

    A WFO qualifies for a phenomena if its mean annual event count over
    2020–2024 is at or above the 75th percentile across all CONUS WFOs
    for that phenomena. Low-volume offices are excluded because their
    per-year verify rates are too noisy for reliable inference.

    Args:
        events: Full (or CONUS-only) events DataFrame. Non-CONUS WFOs are
            excluded before computing thresholds regardless.

    Returns:
        Dict mapping phenomena code ("TO", "SV", "FF") to the set of WFO
        codes that meet the top-quartile threshold.
    """
    conus_events = events[~events["wfo"].isin(NON_CONUS)]

    wfo_annual = (
        conus_events[conus_events["year"] <= 2024]
        .groupby(["wfo", "phenomena", "year"])
        .size()
        .reset_index(name="n_events")
    )
    wfo_mean = (
        wfo_annual
        .groupby(["wfo", "phenomena"])["n_events"]
        .mean()
        .reset_index(name="mean_annual")
    )

    p75_wfos = {}
    for phen in PHENOMENA:
        sub = wfo_mean[wfo_mean["phenomena"] == phen]
        thresh = sub["mean_annual"].quantile(0.75)
        p75_wfos[phen] = set(sub[sub["mean_annual"] >= thresh]["wfo"])

    return p75_wfos


def get_wfo_baseline_stats(events: pd.DataFrame) -> pd.DataFrame:
    """Compute per-WFO baseline mean annual event counts for all phenomena.

    Returns the intermediate DataFrame used by EDA visualizations (WFO volume
    distribution, delta plots). Includes a non_conus flag for coloring.

    Args:
        events: Full events DataFrame from load_events().

    Returns:
        DataFrame with columns: wfo, phenomena, mean_annual_events, non_conus.
    """
    conus_events = events[~events["wfo"].isin(NON_CONUS)]

    wfo_annual = (
        conus_events
        .groupby(["wfo", "year", "phenomena"])
        .size()
        .reset_index(name="n_events")
    )
    wfo_baseline = (
        wfo_annual[wfo_annual["year"] <= 2024]
        .groupby(["wfo", "phenomena"])["n_events"]
        .mean()
        .reset_index(name="mean_annual_events")
    )
    wfo_baseline["non_conus"] = wfo_baseline["wfo"].isin(NON_CONUS)
    return wfo_baseline
