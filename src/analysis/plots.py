# NWS Staffing Analysis - Plot Helpers
# Developed with assistance from Claude Code (Anthropic)
#
# Reusable single-panel figure builders for the EDA notebook. Each helper draws one
# figure for one event type or metric, so a notebook cell is a one-line call and the
# repeated matplotlib body lives here rather than being copy-pasted per event type.

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from scipy import stats

from .constants import (PHENOMENA_LABELS, PHENOMENA_COLORS, CONUS_XLIM, CONUS_YLIM,
                        study_year_to_calendar)

# Solid-fill, bordered legend box shared across EDA figures.
LEGEND_KW = dict(fontsize=8, frameon=True, facecolor="white", edgecolor="#444", framealpha=1.0)


def plot_lta_dist(stormreports, t: str, img_dir: Path):
    """Single-panel LTA (lead-time) histogram for one event type, warned reports only.

    Draws the lead-time distribution with median (dashed) and mean (dotted) markers,
    so the right skew and the gap between median and mean read directly. Saves to
    `04_lta_dist_{t}.png`.

    Args:
        stormreports: Cleaned storm-reports DataFrame.
        t: Event-type code ("TO", "SV", "FF").
        img_dir: Directory to save the figure in.
    """
    lt = stormreports[(stormreports["lsrtype"] == t) & (stormreports["warned"] == 1)]["leadtime"].dropna()
    fig, ax = plt.subplots(figsize=(7, 4.0))
    ax.hist(lt, bins=40, color=PHENOMENA_COLORS[t], alpha=0.8)
    ax.axvline(lt.median(), color="#222", ls="--", lw=1, label=f"median {lt.median():.0f}")
    ax.axvline(lt.mean(),   color="#222", ls=":",  lw=1, label=f"mean {lt.mean():.0f}")
    ax.set_xlabel("LTA: lead time (minutes)"); ax.set_ylabel("warned reports")
    ax.set_title(f"LTA distribution: {PHENOMENA_LABELS[t]} (n={len(lt):,})", fontsize=10)
    ax.legend(**LEGEND_KW)
    fig.tight_layout()
    fig.savefig(img_dir / f"04_lta_dist_{t}.png", dpi=120, bbox_inches="tight")
    plt.show()


def plot_wfo_volume(events, wfo_coords, states, img_dir: Path):
    """Single-panel map of each office (WFO) sized by total warnings issued.

    One marker per office at its NWS-API location, area proportional to that
    office's total warning count (all event types pooled). State outlines
    underlie the markers for reference. A three-dot size legend keys area to
    count. Saves to `04_scope_wfo_volume.png`.

    Args:
        events: Cleaned events DataFrame (one row per warning).
        wfo_coords: DataFrame with wfo, lat, lon from data.load_wfo_coords.
        states: CONUS state-boundary GeoDataFrame from data.load_states.
        img_dir: Directory to save the figure in.
    """
    vol = events.groupby("wfo").size().rename("n").reset_index()
    pts = wfo_coords.merge(vol, on="wfo", how="inner")

    # Marker area proportional to warning count; AREA_PER_WARNING sets the scale.
    AREA_PER_WARNING = 4000 / pts["n"].max()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    states.boundary.plot(ax=ax, color="#bbb", linewidth=0.6, zorder=1)
    ax.scatter(pts["lon"], pts["lat"], s=pts["n"] * AREA_PER_WARNING,
               c="#4a6fa5", alpha=0.45, linewidths=0.5, edgecolors="#2a3f5a", zorder=2)

    ax.set_xlim(*CONUS_XLIM); ax.set_ylim(*CONUS_YLIM)
    ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    ax.set_title(f"Warning volume by office ({len(pts)} WFOs, {int(pts['n'].sum()):,} warnings, "
                 "area proportional to count)", fontsize=10)

    # Size legend: three reference counts spanning the observed range, areas matched to the markers.
    refs = [round(pts["n"].max() / k, -3) for k in (4, 2, 1)]
    handles = [ax.scatter([], [], s=r * AREA_PER_WARNING, c="#4a6fa5", alpha=0.45,
                          linewidths=0.5, edgecolors="#2a3f5a", label=f"{int(r):,}") for r in refs]
    ax.legend(handles=handles, title="warnings issued", loc="lower left",
              labelspacing=1.6, borderpad=1.0, **LEGEND_KW)

    fig.tight_layout()
    fig.savefig(img_dir / "04_scope_wfo_volume.png", dpi=120, bbox_inches="tight")
    plt.show()


def plot_coverage(stormreports, states, t: str, img_dir: Path):
    """Single-panel log-colored hexbin of storm-report density for one event type.

    State outlines underlie a log-normalized hexbin so concentration is visible
    despite heavy skew in per-cell counts. Saves to `04_coverage_density_{t}.png`.

    Args:
        stormreports: Cleaned storm-reports DataFrame (coords may be null; filtered here).
        states: CONUS state-boundary GeoDataFrame from data.load_states.
        t: Event-type code ("TO", "SV", "FF").
        img_dir: Directory to save the figure in.
    """
    pts = stormreports[(stormreports["lsrtype"] == t)
                       & stormreports["lon0"].notna() & stormreports["lat0"].notna()]
    fig, ax = plt.subplots(figsize=(8, 5.0))
    states.boundary.plot(ax=ax, color="black", linewidth=0.5, zorder=1)
    hb = ax.hexbin(pts["lon0"], pts["lat0"], gridsize=45, cmap="viridis",
                   norm=LogNorm(), mincnt=1, extent=(*CONUS_XLIM, *CONUS_YLIM),
                   alpha=0.85, zorder=2)
    ax.set_xlim(*CONUS_XLIM); ax.set_ylim(*CONUS_YLIM)
    ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    ax.set_title(f"Storm report density: {PHENOMENA_LABELS[t]} (n={len(pts):,}, log color)", fontsize=10)
    fig.colorbar(hb, ax=ax, label="reports per cell (log)", shrink=0.8)
    fig.tight_layout()
    fig.savefig(img_dir / f"04_coverage_density_{t}.png", dpi=120, bbox_inches="tight")
    plt.show()


def plot_coverage_diff(stormreports, states, t: str, img_dir: Path, gridsize: int = 30):
    """Single-panel year-10-minus-baseline report-share difference map for one event type.

    Bins year-10 reports and baseline reports (years 1-9) on one identical grid, converts
    each period's per-cell count to a share of that period's national total, and maps the
    difference (year-10 share minus baseline share). This isolates whether the geographic
    distribution shifted in year 10 independent of total volume, the composition confound
    behind a national POD/FAR move. Red cells drew a larger share of reports in year 10,
    blue a smaller share. Diverging scale, symmetric and clipped at the 98th percentile of
    absolute difference so a few extreme cells do not wash it out. Saves to
    `04_coverage_diff_{t}.png`.

    Args:
        stormreports: Cleaned storm-reports DataFrame with is_year10 and lon0/lat0.
        states: CONUS state-boundary GeoDataFrame from data.load_states.
        t: Event-type code ("TO", "SV", "FF").
        img_dir: Directory to save the figure in.
        gridsize: Number of bins per axis (coarse by default; year 10 is one year of data).
    """
    sub = stormreports[(stormreports["lsrtype"] == t)
                       & stormreports["lon0"].notna() & stormreports["lat0"].notna()]
    base = sub[sub["is_year10"] == 0]
    y10  = sub[sub["is_year10"] == 1]

    # One identical grid for both periods, fixed to the CONUS box.
    xedges = np.linspace(*CONUS_XLIM, gridsize + 1)
    yedges = np.linspace(*CONUS_YLIM, gridsize + 1)
    hb, _, _ = np.histogram2d(base["lon0"], base["lat0"], bins=[xedges, yedges])
    h10, _, _ = np.histogram2d(y10["lon0"], y10["lat0"], bins=[xedges, yedges])

    # Each period as a share of its own national total, then difference (year10 - baseline).
    diff = (h10 / h10.sum()) - (hb / hb.sum())
    # Blank cells empty in both periods so they read as no-data, not zero-difference.
    diff = np.where((hb == 0) & (h10 == 0), np.nan, diff)

    lim = np.nanpercentile(np.abs(diff), 98)   # symmetric, clipped so outliers do not dominate
    fig, ax = plt.subplots(figsize=(8, 5.0))
    states.boundary.plot(ax=ax, color="black", linewidth=0.5, zorder=1)
    mesh = ax.pcolormesh(xedges, yedges, diff.T, cmap="RdBu_r", vmin=-lim, vmax=lim,
                         alpha=0.85, zorder=2)
    ax.set_xlim(*CONUS_XLIM); ax.set_ylim(*CONUS_YLIM)
    ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    ax.set_title(f"Year-10 vs baseline report share: {PHENOMENA_LABELS[t]} "
                 f"(n_base={len(base):,}, n_yr10={len(y10):,})", fontsize=10)
    fig.colorbar(mesh, ax=ax, label="share difference (year 10 - baseline)", shrink=0.8)
    fig.tight_layout()
    fig.savefig(img_dir / f"04_coverage_diff_{t}.png", dpi=120, bbox_inches="tight")
    plt.show()


def plot_baseline_trend(raw_yearly, trend: dict, t: str, title: str, ylabel: str,
                        tag: str, img_dir: Path):
    """Single-panel figure contrasting the flat-mean and the fitted-trend yardstick.

    Teaches what a year-10 departure is measured against, using baseline years only.
    Scatters the raw per-year values for study years 1 to 9 / calendar 2016 to 2024
    (the noisy baseline data, x-axis shown in calendar years),
    overlays the season-adjusted trend line (slope = the study_year coefficient) and a
    dotted flat-mean line for contrast. The two lines diverge across the baseline span:
    a drifting metric means the flat mean is the wrong reference, and the year-10
    departure should be read against the trend instead. The lines are not extended to
    year 10 and no year-10 marker is drawn; this is a baseline-only diagnostic and the
    year-10 verdict belongs to 05_analysis.

    Both yardsticks come from the same season-adjusted model: the flat line is the
    trend evaluated at the mean baseline year, so the two share one level and only the
    slope separates them. To match the OLS model the line mirrors, pass mean (not
    median) yearly values so the dots and the line sit on the same scale.
    Saves to `04_baseline_trend_{tag}.png`.

    Args:
        raw_yearly: Per-study-year pandas Series (index 1-9) of the raw metric (mean).
        trend: Output of stats.season_adjusted_trend (slope, intercept).
        t: Event-type code for color ("TO", "SV", "FF").
        title: Metric title for the figure (e.g. "SV lead time").
        ylabel: Y-axis label.
        tag: Filename tag (e.g. "lta_sv").
        img_dir: Directory to save the figure in.
    """
    c = PHENOMENA_COLORS[t]
    yrs = list(raw_yearly.index)            # baseline study years 1-9
    x_line = np.array([yrs[0], yrs[-1]])    # trend/mean drawn across the baseline span only
    slope, b0 = trend["slope"], trend["intercept"]
    trend_line = b0 + slope * x_line
    # Both yardsticks from the same model: the flat mean is the trend at the mean
    # baseline year, so the divergence across the span is pure drift.
    flat = b0 + slope * np.mean(yrs)
    # Display the x-axis in calendar years (study year 1 = 2016); the trend math is
    # unchanged, only the plotted positions and ticks are shifted.
    cal_yrs = study_year_to_calendar(np.array(yrs))

    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ax.scatter(cal_yrs, raw_yearly.values, color=c, s=45, zorder=4,
               label="raw yearly value (2016-2024)")
    ax.plot(study_year_to_calendar(x_line), trend_line, color=c, lw=1.6, zorder=3,
            label=f"season-adjusted trend ({slope:+.2f}/yr)")
    ax.axhline(flat, color="#888", ls=":", lw=1.2, zorder=2,
               label="flat baseline mean (season-adjusted)")
    ax.set_xticks(cal_yrs)
    ax.set_xlabel("calendar year (baseline, 2016-2024)")
    ax.set_ylabel(ylabel)
    ax.set_title(f"Trend vs. flat mean across the baseline: {title}", fontsize=10)
    ax.legend(loc="best", **LEGEND_KW)
    fig.tight_layout()
    fig.savefig(img_dir / f"04_baseline_trend_{tag}.png", dpi=120, bbox_inches="tight")
    plt.show()


def plot_year10_departure(raw_yearly, trend: dict, y10_actual: float, t: str,
                          title: str, ylabel: str, tag: str, img_dir: Path):
    """Single-panel figure drawing the year-10 departure from the baseline trend.

    The year-10 companion to plot_baseline_trend. Scatters the raw per-year values for
    study years 1 to 9, overlays the season-adjusted trend fit on those baseline years
    only, extends that line dashed to year 10 (the out-of-sample baseline expectation),
    and marks the actual year-10 value. A vertical connector between the extrapolated
    trend and the actual is the departure the test quantifies: the gap the reader sees
    is the `is_year10` effect drawn rather than tabulated. Because the year-10 point
    played no part in fitting the line, the gap is a clean out-of-sample departure.

    Scale note: for a binary metric the trend and points are on the rate scale (a linear
    -probability fit from stats.season_adjusted_trend), chosen for a readable picture.
    The formal test is on the logit (odds-ratio) scale and is not numerically identical;
    the caption says so, and the forest plot carries the odds-ratio test. Saves to
    `05_year10_departure_{tag}.png`.

    Args:
        raw_yearly: Per-study-year pandas Series (index 1-9) of the raw metric (mean
            rate for a binary outcome, mean minutes for lead time).
        trend: Output of stats.season_adjusted_trend (slope, intercept) over years 1-9.
        y10_actual: The actual year-10 value on the same scale as raw_yearly (mean rate
            or mean minutes), the point the trend extrapolation is compared against.
        t: Event-type code for color ("TO", "SV", "FF").
        title: Metric title for the figure (e.g. "TO detection rate (POD)").
        ylabel: Y-axis label.
        tag: Filename tag (e.g. "pod_to").
        img_dir: Directory to save the figure in.
    """
    c = PHENOMENA_COLORS[t]
    yrs = list(raw_yearly.index)                  # baseline study years 1-9
    slope, b0 = trend["slope"], trend["intercept"]
    base_line = b0 + slope * np.array([yrs[0], yrs[-1]])   # trend across the baseline span
    y10_pred = b0 + slope * 10                      # extrapolated baseline expectation at year 10
    # Display the x-axis in calendar years (study year 1 = 2016, year 10 = 2025); the
    # trend math is unchanged, only the plotted positions and ticks are shifted.
    cal_yrs = study_year_to_calendar(np.array(yrs))
    cal_y10 = study_year_to_calendar(10)

    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ax.scatter(cal_yrs, raw_yearly.values, color=c, s=45, zorder=4,
               label="raw yearly value (2016-2024)")
    ax.plot(study_year_to_calendar(np.array([yrs[0], yrs[-1]])), base_line, color=c, lw=1.6, zorder=3,
            label=f"season-adjusted baseline trend ({slope:+.3f}/yr)")
    ax.plot([study_year_to_calendar(yrs[-1]), cal_y10], [base_line[-1], y10_pred],
            color=c, lw=1.4, ls="--", zorder=3,
            label="trend extrapolated to 2025")
    # The departure: connector from the extrapolated expectation to the actual year-10 value.
    ax.plot([cal_y10, cal_y10], [y10_pred, y10_actual], color="#444", lw=1.2, ls=":", zorder=4)
    ax.scatter([cal_y10], [y10_pred], facecolors="white", edgecolors=c, s=55, zorder=5,
               label="2025 baseline expectation")
    ax.scatter([cal_y10], [y10_actual], color="#c0392b", s=45, zorder=6,
               label=f"2025 actual ({y10_actual - y10_pred:+.3f} vs. trend)")
    ax.set_xticks(list(cal_yrs) + [cal_y10])
    ax.set_xlabel("calendar year (2016-2024 baseline, 2025 = treatment year)")
    ax.set_ylabel(ylabel)
    ax.set_title(f"Year-10 departure from the baseline trend: {title}", fontsize=10)
    ax.legend(loc="best", **LEGEND_KW)
    fig.tight_layout()
    fig.savefig(img_dir / f"05_year10_departure_{tag}.png", dpi=120, bbox_inches="tight")
    plt.show()


def plot_placebo(placebo: "pd.DataFrame", real_coef: float, t: str, title: str,
                 xlabel: str, tag: str, img_dir: Path):
    """Single-panel figure placing the real year-10 effect against the placebo spread.

    The falsification check, drawn. Each baseline placebo year (year 10 dropped) plots
    its `is_placebo` effect as a point; the real `is_year10` effect plots as a distinct
    marker, with a null reference line at zero. If the real effect sits inside the
    placebo cloud, the machinery flags innocent years as readily as year 10 and the
    year-10 result is not credible; the real effect standing clearly outside the spread
    is persuasive. With only a handful of usable placebo years this is a rough
    credibility check, not a formal null. All effects are on the model's native scale
    (log-odds for the binary metrics, minutes for lead time). Saves to
    `05_placebo_{tag}.png`.

    Args:
        placebo: Output of stats.run_placebo (columns year, n, coef, p).
        real_coef: The real is_year10 coefficient on the same native scale.
        t: Event-type code for color ("TO", "SV", "FF").
        title: Metric title for the figure (e.g. "TO detection rate (POD)").
        xlabel: X-axis label naming the effect scale (e.g. "is_year10 effect (log-odds)").
        tag: Filename tag (e.g. "pod_to").
        img_dir: Directory to save the figure in.
    """
    c = PHENOMENA_COLORS[t]
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.axvline(0.0, color="#888", lw=1, ls="-", zorder=1, label="null (no effect)")
    ax.scatter(placebo["coef"], [0.4] * len(placebo), color=c, alpha=0.7, s=55, zorder=3,
               label=f"placebo baseline years (n={len(placebo)})")
    for _, r in placebo.iterrows():
        ax.annotate(f"yr {int(r['year'])}", (r["coef"], 0.4), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=7, color="#555")
    ax.scatter([real_coef], [0.4], color="#c0392b", s=55, zorder=5,
               label="real year-10 effect")
    ax.annotate("yr 10", (real_coef, 0.4), textcoords="offset points",
                xytext=(0, 8), ha="center", fontsize=7, color="#c0392b")
    ax.set_ylim(0.2, 0.8); ax.set_yticks([])
    ax.set_xlabel(xlabel)
    ax.set_title(f"Placebo falsification: {title}", fontsize=10)
    ax.legend(loc="best", **LEGEND_KW)
    fig.tight_layout()
    fig.savefig(img_dir / f"05_placebo_{tag}.png", dpi=120, bbox_inches="tight")
    plt.show()


def plot_lta_residual_qq(resid_by_transform: dict, t: str, img_dir: Path):
    """Single-panel residual Q-Q comparison of LTA outcome transforms for one type.

    The LTA model is OLS, so the relevant question is whether its residuals are near
    normal, not whether the raw outcome is. Standardizes each candidate transform's
    residuals and plots their theoretical-vs-sample quantiles against the 45-degree
    line; the transform whose points track the line most closely is the best behaved.
    Saves to `04_lta_residual_qq_{t}.png`.

    Args:
        resid_by_transform: Mapping transform label -> (residuals ndarray, skew float),
            as built from stats.lta_residuals (e.g. "raw", "log1p", "sqrt").
        t: Event-type code ("TO", "SV", "FF").
        img_dir: Directory to save the figure in.
    """
    colors = {"raw": "#888", "log1p": "#4a6fa5", "sqrt": PHENOMENA_COLORS[t]}
    fig, ax = plt.subplots(figsize=(6.0, 6.0))
    for label, (resid, skew) in resid_by_transform.items():
        z = (resid - resid.mean()) / resid.std()
        osm, osr = stats.probplot(z, dist="norm", fit=False)
        ax.plot(osm, osr, ".", ms=2, alpha=0.5, color=colors.get(label, "#222"),
                label=f"{label} (skew {skew:+.2f})")
    lim = [-4, 4]
    ax.plot(lim, lim, color="#222", lw=1, ls="--", zorder=5, label="normal (45 deg)")
    ax.set_xlim(*lim); ax.set_ylim(*lim)
    ax.set_xlabel("theoretical quantiles"); ax.set_ylabel("standardized residual quantiles")
    ax.set_title(f"LTA OLS residual Q-Q by transform: {PHENOMENA_LABELS[t]}", fontsize=10)
    ax.legend(loc="upper left", **LEGEND_KW)
    fig.tight_layout()
    fig.savefig(img_dir / f"04_lta_residual_qq_{t}.png", dpi=120, bbox_inches="tight")
    plt.show()


def plot_baseline_variability(series_by_type: dict, title: str, ylabel: str,
                              years, tag: str, img_dir: Path):
    """Single-panel baseline year-to-year variability of one metric, all event types.

    For each event type, plots the per-year baseline series with its mean (dashed) and
    a shaded plus/minus one standard deviation band, so the reader sees how much the
    metric normally wobbles. Saves to `04_baseline_variability_{tag}.png`.

    Args:
        series_by_type: Mapping event-type code -> per-year pandas Series (baseline years).
        title: Metric title for the figure (e.g. "POD: detection rate").
        ylabel: Y-axis label.
        years: Baseline year range, used for the shaded band x-extent and ticks.
        tag: Filename tag (e.g. "pod", "far", "lta").
        img_dir: Directory to save the figure in.
    """
    years = list(years)
    # Display the x-axis in calendar years (study year 1 = 2016); the series math is
    # unchanged, only the plotted positions and ticks are shifted.
    cal_years = [study_year_to_calendar(y) for y in years]
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    for t, s in series_by_type.items():
        m, sd = s.mean(), s.std()
        c = PHENOMENA_COLORS[t]
        ax.fill_between(cal_years, m - sd, m + sd, color=c, alpha=0.12)
        ax.axhline(m, color=c, ls="--", lw=0.8, alpha=0.7)
        ax.plot(study_year_to_calendar(np.asarray(s.index)), s.values, "o-", color=c, lw=1, ms=5,
                label=f"{PHENOMENA_LABELS[t]} (±1 SD = {sd:.2g})")
    ax.set_xticks(cal_years); ax.set_xlabel("calendar year")
    ax.set_ylabel(ylabel); ax.set_title(f"Baseline variability: {title} (2016-2024)", fontsize=10)
    ax.legend(loc="best", **LEGEND_KW)
    fig.tight_layout()
    fig.savefig(img_dir / f"04_baseline_variability_{tag}.png", dpi=120, bbox_inches="tight")
    plt.show()


def plot_year10_forest(table: "pd.DataFrame", kind: str, title: str, xlabel: str,
                       tag: str, img_dir: Path):
    """Single-panel forest plot of the year-10 effects for one model family.

    Draws the `is_year10` coefficient and its confidence interval as a point-and-whisker
    row per event type, for the tests sharing one native scale (the binary metrics in
    log-odds, lead time in minutes; the two are never mixed on one axis). A null line at
    zero anchors the reading, each row is colored by event type, and rows that survive the
    Benjamini-Hochberg false-discovery-rate correction are drawn with a filled marker while
    non-survivors are hollow, so the figure shows at a glance which departures hold up once
    the nine tests are read as a family. Saves to `05_forest_{tag}.png`.

    Args:
        table: Subset of `stats.synthesis_table` for one `kind`, with columns event_type,
            metric, coef, ci_low, ci_high, survives.
        kind: "logit" or "ols", used only to pick the null-line label scale wording.
        title: Figure title (e.g. "Year-10 departure: detection and false alarms").
        xlabel: X-axis label naming the scale (e.g. "is_year10 coefficient (log-odds)").
        tag: Filename tag (e.g. "binary" or "lta").
        img_dir: Directory to save the figure in.
    """
    rows = table.reset_index(drop=True)
    ypos = list(range(len(rows)))[::-1]  # first row at top
    fig, ax = plt.subplots(figsize=(7.5, 0.7 * len(rows) + 1.6))
    ax.axvline(0.0, color="#888", lw=1, zorder=1, label="null (no effect)")
    for y, (_, r) in zip(ypos, rows.iterrows()):
        c = PHENOMENA_COLORS[r["event_type"]]
        ax.plot([r["ci_low"], r["ci_high"]], [y, y], color=c, lw=2, zorder=2)
        ax.scatter([r["coef"]], [y], s=70, zorder=3, color=c,
                   edgecolor=c, facecolor=(c if r["survives"] else "white"))
    ax.set_yticks(ypos)
    ax.set_yticklabels([f"{r['event_type']} {r['metric']}" for _, r in rows.iterrows()])
    ax.set_xlabel(xlabel)
    ax.set_title(title, fontsize=10)
    # Legend conveys the filled/hollow survival encoding and the null line.
    ax.scatter([], [], s=70, color="#444", label="survives FDR (filled)")
    ax.scatter([], [], s=70, edgecolor="#444", facecolor="white", label="does not survive (hollow)")
    ax.legend(loc="best", **LEGEND_KW)
    fig.tight_layout()
    fig.savefig(img_dir / f"05_forest_{tag}.png", dpi=120, bbox_inches="tight")
    plt.show()


def plot_office_spread(hetero_by_type: dict, kind: str, metric: str, title: str,
                       xlabel: str, img_dir: Path, seed: int = 0):
    """Single-panel strip plot of per-office year-10 effects, one row per event type.

    Shows the dispersion behind the office-heterogeneity table: each row is one event
    type's kept-office year-10 effects, scattered with vertical jitter so individual
    offices are visible, on the interpretable scale (odds ratio for the logistic metrics,
    minutes for lead time). A reference line marks no departure (odds ratio 1 for logit,
    0 minutes for lead time), and the median office effect is drawn as a diamond on each
    row to locate the centre of the cloud. Each row is annotated with its kept/total
    office count, so a row built on few offices (acutely tornado) is visibly weaker
    rather than read as equal evidence. This is descriptive: it pictures the spread the
    table summarizes, not a test. Saves to `05_office_spread_{metric}.png`.

    Args:
        hetero_by_type: Maps event-type code (TO/SV/FF) to that cell's
            `stats.fit_office_heterogeneity` result dict (needs office_effects,
            n_offices_kept, n_offices_total). One metric's three cells.
        kind: "logit" or "ols". Selects the native-to-interpretable transform: exp() to an
            odds ratio for logit, square (undo sqrt) to minutes for ols.
        metric: Metric code (POD/FAR/LTA), used only for the filename tag.
        title: Figure title.
        xlabel: X-axis label naming the interpretable scale.
        img_dir: Directory to save the figure in.
        seed: RNG seed for the reproducible jitter.
    """
    # Native model scale -> the scale a reader interprets: odds ratio (logit) or minutes
    # (ols, undoing the sqrt the lead-time model was fit on). The null sits at 1 vs 0.
    to_scale = (lambda e: np.exp(e)) if kind == "logit" else (lambda e: np.square(e))
    null_x = 1.0 if kind == "logit" else 0.0

    order = [t for t in ("TO", "SV", "FF") if t in hetero_by_type]
    ypos = list(range(len(order)))[::-1]  # first type at top
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(7.5, 0.9 * len(order) + 1.6))
    ax.axvline(null_x, color="#888", lw=1, zorder=1, label="no departure")
    for y, t in zip(ypos, order):
        h = hetero_by_type[t]
        c = PHENOMENA_COLORS[t]
        eff = to_scale(np.asarray(h["office_effects"]))
        jitter = rng.uniform(-0.16, 0.16, size=len(eff))
        ax.scatter(eff, y + jitter, s=18, color=c, alpha=0.5,
                   edgecolor="none", zorder=2)
        # Median office effect locates the centre of the per-office cloud.
        ax.scatter([np.median(eff)], [y], marker="D", s=70, color=c,
                   edgecolor="white", linewidth=0.8, zorder=3)
        ax.text(0.0, y + 0.34, f"{PHENOMENA_LABELS[t]}  "
                f"({h['n_offices_kept']}/{h['n_offices_total']} offices)",
                transform=ax.get_yaxis_transform(), ha="left", va="bottom", fontsize=8)
    ax.set_yticks(ypos)
    ax.set_yticklabels(order)
    ax.set_ylim(-0.6, len(order) - 0.4)
    ax.set_xlabel(xlabel)
    ax.set_title(title, fontsize=10)
    ax.scatter([], [], marker="D", s=70, color="#444", edgecolor="white",
               label="median office")
    ax.scatter([], [], s=18, color="#444", alpha=0.5, label="one office")
    ax.legend(loc="best", **LEGEND_KW)
    fig.tight_layout()
    fig.savefig(img_dir / f"05_office_spread_{metric.lower()}.png", dpi=120, bbox_inches="tight")
    plt.show()


def plot_office_effect_hist(office_effects, event_type: str, national_or: float,
                            title: str, xlabel: str, fname: str, img_dir: Path,
                            bins: int = 20):
    """Single-type histogram of per-office year-10 effects on the odds-ratio scale.

    Where `plot_office_spread` compresses three event types into jittered strips, this
    pictures one event type's per-office year-10 effects as a distribution, so the shape
    (central mass, skew, right tail) reads directly. Built for the severe-storm false-alarm
    (FAR) cell, the one credible national departure: it shows whether that national rise is
    broad across offices or driven by a few. Two vertical references frame the read: odds
    ratio 1 (no departure) anchors the lean, and the national year-10 odds ratio shows where
    the pooled finding sits relative to the office cloud. A national line falling inside the
    bulk says the rise is representative of offices, not one office dragging the average.

    This is descriptive, not a test. It pictures the spread of the per-office point
    estimates; it does not establish the spread exceeds sampling noise (no valid joint test
    at this design; see stats.fit_office_heterogeneity). Saves to `05_{fname}.png`.

    Args:
        office_effects: Per-office year-10 effects on the model's native log-odds scale
            (the `office_effects` array from stats.fit_office_heterogeneity, logit kind).
            Exponentiated here to odds ratios.
        event_type: Event-type code (TO/SV/FF), selects the bar color.
        national_or: The pooled national year-10 odds ratio for this metric (from the
            main fit), drawn as the second reference line. Pass it live so it cannot drift.
        title: Figure title.
        xlabel: X-axis label naming the odds-ratio scale.
        fname: Filename stem; the figure saves as `05_{fname}.png`.
        img_dir: Directory to save the figure in.
        bins: Histogram bin count (default 20), fixed for a reproducible figure.
    """
    eff = np.exp(np.asarray(office_effects))  # log-odds -> odds ratio
    color = PHENOMENA_COLORS[event_type]

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.hist(eff, bins=bins, color=color, alpha=0.7, edgecolor="white", linewidth=0.6)
    ax.axvline(1.0, color="#888", lw=1.2, zorder=3, label="no departure (OR 1)")
    ax.axvline(national_or, color="#222", lw=1.4, ls="--", zorder=3,
               label=f"national year-10 (OR {national_or:.2f})")
    ax.text(0.98, 0.96, f"n = {len(eff)} offices", transform=ax.transAxes,
            ha="right", va="top", fontsize=8)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("offices")
    ax.set_title(title, fontsize=10)
    ax.legend(loc="upper right", **LEGEND_KW)
    fig.tight_layout()
    fig.savefig(img_dir / f"05_{fname}.png", dpi=120, bbox_inches="tight")
    plt.show()


def plot_placebo_normalized(frame: "pd.DataFrame", img_dir: Path):
    """Consolidated single-panel view of all nine placebo tests on one standardized scale.

    Draws every (event type x metric) cell as one row: the placebo baseline years as
    grey points and the real year-10 effect as an event-colored diamond, all on the
    standardized coef/SE (Wald) axis built by stats.standardized_placebo_frame, so the
    nine otherwise-incomparable tests share one axis. A shaded |z| < 1.96 band marks the
    two-sided 0.05 significance zone and a null line sits at zero; a year-10 diamond
    standing outside both its grey placebo cloud and the band is the distinctive, credible
    case, while one sitting inside the cloud is flagged about as readily as an innocent
    baseline year. The axis is the raw signed Wald statistic, so positive means a positive
    coefficient (higher POD better, higher FAR worse, longer lead time better); the caption
    carries that convention. Rows follow the frame's cell order so event types stay grouped.

    Each year-10 diamond also carries the two-filter verdict: it is filled (event color)
    when the cell survives the Benjamini-Hochberg FDR correction and hollow (white) when it
    does not, and it gains a bold dark ring when the real effect falls outside its placebo
    spread. The one diamond that is both filled and ringed is the single departure that
    clears both filters. Saves to `05_placebo_normalized.png`.

    Args:
        frame: Output of stats.standardized_placebo_frame (columns event, metric, label,
            kind in {placebo, year10}, z, p, outside_placebo, survives_fdr).
        img_dir: Directory to save the figure in.
    """
    labels = list(dict.fromkeys(frame["label"]))  # preserve cell order
    ypos = {lab: y for lab, y in zip(labels, range(len(labels) - 1, -1, -1))}
    rng = np.random.default_rng(7)

    fig, ax = plt.subplots(figsize=(8.0, 6.0))
    band = ax.axvspan(-1.96, 1.96, color="#eeeeee", zorder=0,
                      label="|z| < 1.96 (approx. .05, uncorrected)")
    for edge in (-1.96, 1.96):
        ax.axvline(edge, color="#bbb", lw=0.8, ls="--", zorder=1)
    ax.axvline(0.0, color="#888", lw=1, zorder=1)

    placebo = frame[frame["kind"] == "placebo"]
    jit = (rng.random(len(placebo)) - 0.5) * 0.18
    ax.scatter(placebo["z"], [ypos[l] for l in placebo["label"]] + jit,
               color="#999", alpha=0.6, s=28, zorder=2)
    for _, r in frame[frame["kind"] == "year10"].iterrows():
        ev = r["event"]
        # Fill encodes FDR survival, the ring encodes falling outside the placebo spread.
        face = PHENOMENA_COLORS[ev] if r["survives_fdr"] else "white"
        edge = "#111" if r["outside_placebo"] else "#888"
        lw = 2.0 if r["outside_placebo"] else 0.6
        ax.scatter([r["z"]], [ypos[r["label"]]], marker="D", s=70, zorder=4,
                   facecolors=face, edgecolors=edge, linewidths=lw)

    ax.set_yticks([ypos[l] for l in labels])
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("standardized effect  (is_year10 / is_placebo coefficient / SE)")
    ax.set_title("Year-10 effect vs placebo spread, all nine tests (standardized)", fontsize=11)
    ax.grid(axis="x", color="#ddd", lw=0.5, zorder=0)
    ax.margins(y=0.04)

    h_fdr = ax.scatter([], [], color="#444", marker="D", s=70, edgecolors="#888",
                       linewidths=0.6, label="survives BH FDR (filled; hollow if not)")
    h_ring = ax.scatter([], [], facecolors="white", marker="D", s=70, edgecolors="#111",
                        linewidths=2.0, label="outside placebo spread (bold ring)")
    h_pl = ax.scatter([], [], color="#999", alpha=0.6, s=28, label="placebo baseline years")
    ax.legend(handles=[h_fdr, h_ring, h_pl, band], loc="upper right", **LEGEND_KW)
    fig.tight_layout()
    fig.savefig(img_dir / "05_placebo_normalized.png", dpi=120, bbox_inches="tight")
    plt.show()
