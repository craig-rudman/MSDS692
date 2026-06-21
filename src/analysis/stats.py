# NWS Staffing Analysis - Statistical Utilities
# Developed with assistance from Claude Code (Anthropic)
#
# Small statistical helpers shared across analysis and synthesis notebooks.

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats


def baseline_yearly(df: pd.DataFrame, outcome_col: str, year_col: str = "year",
                    agg: str = "mean", years=range(2016, 2025)) -> pd.Series:
    """Per-year baseline value of an outcome, restricted to the baseline span.

    Summarizes one outcome by calendar year over the baseline years only (2016-2024
    by default, excluding the year-10 treatment year). Used to show how much a metric
    naturally varies year to year before the year-10 comparison is made.

    Args:
        df: Rows for one event type (already subset by caller).
        outcome_col: Column to aggregate (e.g. "warned", "verify", "leadtime").
        year_col: Calendar-year column.
        agg: Aggregation per year, "mean" for rates or "median" for skewed lead time.
        years: Baseline years to keep.

    Returns:
        Series indexed by year, one aggregated value per baseline year.
    """
    b = df[df[year_col].isin(list(years))]
    return b.groupby(year_col)[outcome_col].agg(agg)


def season_adjusted_trend(df: pd.DataFrame, outcome_col: str,
                          years=range(1, 10)) -> dict:
    """Season-adjusted baseline trend in one outcome across study years 1 to 9.

    Fits `outcome ~ C(season_cat) + study_year` on the baseline study years and
    returns the trend the year-10 departure is measured against. The slope it
    reports is exactly the `study_year` coefficient: per-year drift net of season
    mix, the same quantity `05_analysis` reads from the full model. This is the
    yardstick the "measure against the trend, not the flat mean" figure draws.

    Because `study_year` enters as a single numeric term, the season-adjusted
    per-year predictions lie exactly on a line; the figure therefore scatters the
    raw per-year medians (the noisy data the slope was estimated from) and overlays
    this line, rather than plotting the on-line adjusted points.

    Args:
        df: Rows for one event type, baseline study years only (caller subsets).
        outcome_col: Outcome to model (e.g. "leadtime").
        years: Baseline study-year range to fit over (1 to 9 by default).

    Returns:
        Dict with: slope (study_year coefficient, units of outcome per year) and
        intercept (so trend value at study_year y is intercept + slope * y). The
        intercept holds season at the baseline mean composition (each season's
        prediction weighted by its share of the baseline rows), so the line sits at
        the level of the all-season yearly medians rather than floating above them
        at a single season's level.
    """
    b = df[df["study_year"].isin(list(years))]
    model = smf.ols(f"{outcome_col} ~ C(season_cat) + study_year", data=b).fit()
    # Trend value at study_year 0, season-marginalized: predict at each season and
    # average weighted by that season's share of the baseline rows. This puts the
    # line at the mean season mix, level with the all-season medians the figure
    # scatters, instead of anchored to one (high-lead) season.
    season_share = b["season_cat"].value_counts(normalize=True)
    grid = pd.DataFrame({"study_year": 0, "season_cat": season_share.index})
    intercept = float((model.predict(grid).to_numpy() * season_share.to_numpy()).sum())
    return {"slope": float(model.params["study_year"]),
            "intercept": intercept}


def lta_residuals(df: pd.DataFrame, transform: str, years=range(1, 10)):
    """Residuals of the baseline LTA model under a given outcome transform.

    Fits `f(leadtime) ~ C(season_cat) + study_year` on warned baseline rows for one
    event type and returns the residuals, for an OLS-fit diagnostic (the LTA model is
    OLS, so its residuals, not the raw outcome, are what must be near-normal). Used by
    the "does OLS hold for lead time" section to compare candidate transforms.

    Args:
        df: Warned storm-report rows for one event type, baseline years (caller subsets).
        transform: One of "raw", "log1p", "sqrt"; the function applied to leadtime.
        years: Baseline study-year range to fit over (1 to 9 by default).

    Returns:
        Tuple of (residuals ndarray, skew float) for the fitted model.
    """
    funcs = {"raw": lambda x: x, "log1p": np.log1p, "sqrt": np.sqrt}
    b = df[df["study_year"].isin(list(years))].copy()
    b["_y"] = funcs[transform](b["leadtime"])
    model = smf.ols("_y ~ C(season_cat) + study_year", data=b).fit()
    return model.resid.to_numpy(), float(stats.skew(model.resid))


def cell_summary(df: pd.DataFrame, group_col: str, outcome_col: str) -> pd.DataFrame:
    """Per-group count and binary-outcome rate, for thin-cell and separation checks.

    Summarizes a binary 0/1 outcome (e.g. warned, verify) within each level of a
    grouping column. Intended for the pre-modeling diagnostic: confirm each cell a
    model term must estimate has enough rows and is not at a degenerate 0/1 rate.
    Not for continuous outcomes such as lead time; describe those directly instead.

    Args:
        df: Rows to summarize (typically already subset to one event type).
        group_col: Column to group by (e.g. "season_cat").
        outcome_col: Binary 0/1 outcome column (e.g. "warned", "verify").

    Returns:
        DataFrame indexed by group_col with columns: n (row count),
        n_pos (count of outcome == 1), rate (mean of the outcome).
    """
    g = df.groupby(group_col)[outcome_col]
    out = pd.DataFrame({"n": g.size(), "n_pos": g.sum(), "rate": g.mean()})
    return out


def fit_main_model(df: pd.DataFrame, outcome_col: str, kind: str) -> dict:
    """Fit the full model on all ten years and extract the year-10 departure.

    Fits `outcome ~ C(season_cat) + study_year + is_year10` on all ten study
    years. The `is_year10` term is the quantity of interest: how far year 10
    departs from the season-adjusted baseline trend (`study_year` absorbs the
    baseline drift, `C(season_cat)` the season-of-year pattern). This is the
    main test of 05_analysis; read its coefficient, confidence interval, and
    p-value directly. For logistic outcomes the coefficient is also exponentiated
    to an odds ratio so the effect is reported on an interpretable scale; for OLS
    the coefficient is already in the outcome's units (minutes for lead time).

    Args:
        df: Rows for one event type (caller subsets by lsrtype/phenomena).
        outcome_col: Outcome column ("warned", "verify", or "leadtime").
        kind: "logit" for the two binary metrics, "ols" for lead time.

    Returns:
        Dict with: n (rows fit), coef (is_year10 coefficient on the model's
        native scale, log-odds for logit / minutes for OLS), se (standard error
        of the coefficient, same scale), ci_low, ci_high (95% confidence interval,
        same scale), p (two-sided p-value), and for logit also or_ (odds ratio =
        exp(coef)), or_low, or_high (exp of the CI). The se supports the
        standardized coef/SE comparison drawn by the consolidated placebo figure.
    """
    f = f"{outcome_col} ~ C(season_cat) + study_year + is_year10"
    model = smf.logit(f, data=df).fit(disp=0) if kind == "logit" else smf.ols(f, data=df).fit()
    coef = float(model.params["is_year10"])
    ci = model.conf_int().loc["is_year10"]
    ci_low, ci_high = float(ci[0]), float(ci[1])
    out = {"n": int(model.nobs), "coef": coef, "se": float(model.bse["is_year10"]),
           "ci_low": ci_low, "ci_high": ci_high, "p": float(model.pvalues["is_year10"])}
    if kind == "logit":
        out.update({"or_": np.exp(coef), "or_low": np.exp(ci_low),
                    "or_high": np.exp(ci_high)})
    return out


def fit_drift(df: pd.DataFrame, outcome_col: str, kind: str,
              years=range(1, 10)) -> dict:
    """Diagnostic baseline-drift fit on study years 1 to 9 only.

    Fits `outcome ~ C(season_cat) + study_year` on the baseline years and reports
    the `study_year` slope: how much the metric was already drifting per year
    before year 10, net of season. This is the drift check, not the test; it is
    used to understand whether the baseline was moving and to sanity-check the
    full model's `study_year` term against it (a large swing between the two
    suggests year 10 is influencing the trend estimate).

    Args:
        df: Rows for one event type (caller subsets).
        outcome_col: Outcome column ("warned", "verify", or "leadtime").
        kind: "logit" for the two binary metrics, "ols" for lead time.
        years: Baseline study-year range to fit over (1 to 9 by default).

    Returns:
        Dict with: n (rows fit), slope (study_year coefficient, native scale),
        ci_low, ci_high (95% CI), p (two-sided p-value).
    """
    b = df[df["study_year"].isin(list(years))]
    f = f"{outcome_col} ~ C(season_cat) + study_year"
    model = smf.logit(f, data=b).fit(disp=0) if kind == "logit" else smf.ols(f, data=b).fit()
    ci = model.conf_int().loc["study_year"]
    return {"n": int(model.nobs), "slope": float(model.params["study_year"]),
            "ci_low": float(ci[0]), "ci_high": float(ci[1]),
            "p": float(model.pvalues["study_year"])}


def _heterogeneity_eligible(sub: pd.DataFrame, outcome_col: str, kind: str,
                            min_cell: int) -> set:
    """Offices with a year-10 cell well-sampled enough to carry an interaction term.

    An office can only contribute a per-office year-10 effect if it has enough year-10
    rows, and (for the binary metrics) a year-10 outcome that is neither all-0 nor
    all-1; a degenerate or empty cell makes the saturated interaction model singular.
    This returns the offices that clear `min_cell` year-10 rows and are non-degenerate,
    the set the heterogeneity fit is restricted to.

    Args:
        sub: Rows for one event type (caller subsets).
        outcome_col: Outcome column ("warned", "verify", or "leadtime").
        kind: "logit" (rate, must be non-degenerate) or "ols" (size check only).
        min_cell: Minimum year-10 rows an office must have to be eligible.

    Returns:
        Set of eligible WFO codes.
    """
    y10 = sub[sub["is_year10"] == 1]
    if kind == "ols":
        size = y10.groupby("wfo")[outcome_col].size()
        return set(size[size >= min_cell].index)
    g = y10.groupby("wfo")[outcome_col].agg(["size", "mean"])
    g = g[(g["size"] >= min_cell) & (g["mean"] > 0) & (g["mean"] < 1)]
    return set(g.index)


def fit_office_heterogeneity(df: pd.DataFrame, outcome_col: str, kind: str,
                             min_cell: int = 20) -> dict:
    """Describe how much the year-10 departure varies across offices (WFOs).

    Fits `outcome ~ C(season_cat) + study_year + C(wfo) + C(wfo):is_year10` on all
    ten study years for one event type, with cluster-robust covariance clustered on
    `wfo` so the per-office estimates carry within-office storm clustering. `C(wfo)`
    gives each office its own intercept (office fixed effects); the `C(wfo):is_year10`
    interaction block lets each office's year-10 departure differ from the shared one.
    For the lead-time (LTA) model the outcome is `sqrt(leadtime)`, matching the
    transform `05_analysis` settled on, so the OLS residuals stay near-normal.

    The fit is restricted to offices whose year-10 cell is well sampled (at least
    `min_cell` year-10 rows, and for the binary metrics a non-degenerate 0-to-1 rate);
    a saturated per-office interaction is otherwise singular where an office has an
    empty or all-0/all-1 year-10 cell. The kept/total office counts are returned and
    are themselves informative: tornado keeps far fewer offices than severe storm,
    which is exactly why naming individual offices is left to a future study.

    The deliverable is descriptive, not a formal test: the spread of the per-office
    year-10 effects, read as a signal of where to direct further inquiry rather than a
    tested claim. A valid joint test of the interaction block is deliberately not
    attempted here. A cluster-robust Wald test over per-office terms clustered on the
    same office is rank-deficient (the constraint covariance does not reach full rank),
    so its p-value would be invalid; a rigorous heterogeneity test is left to a future
    study with more years per office.

    The per-office year-10 effects are summarized by their standard deviation on the
    model's native scale (log-odds for logit, sqrt-minutes for OLS). With `C(wfo)`
    already in the model the saturated interaction yields one `C(wfo)[X]:is_year10`
    coefficient per kept office and no bare `is_year10` term, so each office's year-10
    effect is simply its own interaction coefficient. For logit the spread is also
    reported as an odds-ratio multiplier (exp of the SD), the interpretable read.

    Args:
        df: Rows for one event type (caller subsets by lsrtype/phenomena).
        outcome_col: Outcome column ("warned", "verify", or "leadtime").
        kind: "logit" for the two binary metrics, "ols" for lead time.
        min_cell: Minimum year-10 rows for an office to be eligible (default 20).

    Returns:
        Dict with: n (rows fit), n_offices_kept, n_offices_total (eligible vs all
        offices for this type), effect_sd (SD of per-office year-10 effects, native
        scale), office_effects (the per-office year-10 effects array, native scale, one
        entry per kept office), and for logit effect_sd_or (exp(effect_sd), the
        odds-ratio spread). The strip plot consumes office_effects; the table consumes
        effect_sd.
    """
    n_total = df["wfo"].nunique()
    keep = _heterogeneity_eligible(df, outcome_col, kind, min_cell)
    sub = df[df["wfo"].isin(keep)].copy()

    yexpr = "np.sqrt(leadtime)" if kind == "ols" else outcome_col
    f = f"{yexpr} ~ C(season_cat) + study_year + C(wfo) + C(wfo):is_year10"
    cov = {"cov_type": "cluster", "cov_kwds": {"groups": sub["wfo"]}}
    model = (smf.logit(f, data=sub).fit(disp=0, **cov) if kind == "logit"
             else smf.ols(f, data=sub).fit(**cov))

    # The interaction block is every coefficient carrying both wfo and is_year10. With
    # C(wfo) already in the model, the formula yields one C(wfo)[X]:is_year10 term per
    # kept office and no bare is_year10 main effect, so each office's year-10 effect IS
    # its own interaction coefficient directly; there is no shared baseline to add.
    inter = [name for name in model.params.index
             if "C(wfo)" in name and "is_year10" in name]

    # Per-office year-10 effects are the interaction coefficients themselves. Their
    # spread is the descriptive deliverable; no joint test is computed (see docstring).
    office_effects = model.params[inter].to_numpy()
    effect_sd = float(np.std(office_effects, ddof=1))

    out = {"n": int(model.nobs), "n_offices_kept": len(inter),
           "n_offices_total": n_total, "effect_sd": effect_sd,
           "office_effects": office_effects}
    if kind == "logit":
        out["effect_sd_or"] = float(np.exp(effect_sd))
    return out


def run_placebo(df: pd.DataFrame, outcome_col: str, kind: str,
                placebo_years=range(2, 9)) -> pd.DataFrame:
    """Falsification test: substitute a fake year indicator into baseline years.

    Drops year 10 entirely so the real effect cannot leak in, then for each
    candidate baseline year fits the same model structure with an `is_placebo`
    indicator in place of `is_year10`:
    `outcome ~ C(season_cat) + study_year + is_placebo`, one fit per year. If the
    machinery flags an innocent baseline year as readily as it flags year 10, the
    year-10 result cannot be trusted. Every interior baseline year is tested; the
    default range excludes only years 1 and 9, the endpoints that anchor the trend.
    With nine baseline years this is a rough credibility check, not a formal null
    distribution.

    Args:
        df: Rows for one event type (caller subsets).
        outcome_col: Outcome column ("warned", "verify", or "leadtime").
        kind: "logit" for the two binary metrics, "ols" for lead time.
        placebo_years: Baseline study years to test as the fake treatment year.

    Returns:
        DataFrame, one row per placebo year, columns: year (the placebo year),
        n, coef (is_placebo coefficient, native scale), se (standard error of the
        coefficient, same scale), p. The real is_year10 effect is compared against
        the spread of these by the caller; se supports the standardized coef/SE
        comparison drawn by the consolidated placebo figure.
    """
    baseline = df[df["study_year"] != 10]
    rows = []
    for y in placebo_years:
        b = baseline.copy()
        b["is_placebo"] = (b["study_year"] == y).astype(int)
        f = f"{outcome_col} ~ C(season_cat) + study_year + is_placebo"
        model = smf.logit(f, data=b).fit(disp=0) if kind == "logit" else smf.ols(f, data=b).fit()
        rows.append({"year": y, "n": int(model.nobs),
                     "coef": float(model.params["is_placebo"]),
                     "se": float(model.bse["is_placebo"]),
                     "p": float(model.pvalues["is_placebo"])})
    return pd.DataFrame(rows)


def bh_fdr(pvals) -> np.ndarray:
    """Benjamini-Hochberg false-discovery-rate adjusted p-values.

    Adjusts a family of p-values (the nine year-10 tests across three metrics and
    three event types) for multiple comparisons by the Benjamini-Hochberg step-up
    procedure. Returned values are on the same 0-1 scale as the inputs and can be
    thresholded directly; with nine tests this controls the expected false
    discovery rate rather than the family-wise error rate, the appropriate choice
    for an exploratory family this size.

    Args:
        pvals: Sequence of raw p-values.

    Returns:
        ndarray of adjusted p-values, aligned to the input order.
    """
    p = np.asarray(pvals, dtype=float)
    n = p.size
    order = np.argsort(p)
    ranked = p[order] * n / (np.arange(n) + 1)
    # Enforce monotonicity from the largest rank down, then clip to 1.
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(ranked, 1.0)
    return out


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


def departure_summary(trend: dict, actual: float) -> dict:
    """Year-10 departure on the raw rate (or minutes) scale the figure draws.

    Extrapolates the season-adjusted baseline trend to study year 10 and compares
    it to the observed year-10 value. This is the gap the dotted connector in the
    departure figure represents, printed so the caption can read it off exactly.
    Note this is the descriptive rate-scale gap, not the model `is_year10` term:
    for the two logistic metrics the formal test is on the odds-ratio scale and is
    not numerically identical (see the per-metric fit output above).

    Args:
        trend: Output of `season_adjusted_trend` (slope and intercept).
        actual: Observed year-10 value (rate or mean minutes).

    Returns:
        Dict with: trend_at_10 (extrapolated baseline value at year 10), actual,
        and gap (actual minus trend_at_10, signed).
    """
    trend_at_10 = trend["intercept"] + trend["slope"] * 10
    return {"trend_at_10": trend_at_10, "actual": actual,
            "gap": actual - trend_at_10}


def placebo_summary(placebo: pd.DataFrame, real_coef: float,
                    alpha: float = 0.05) -> dict:
    """Locate the real year-10 effect within the placebo spread.

    Summarizes a `run_placebo` table against the real `is_year10` coefficient so
    the caption can state, from printed numbers, whether the real effect sits
    inside the placebo cloud (the method flags innocent years as readily as year
    10) or outside it (the year-10 effect is distinctive), and how many placebo
    years came back significant. With only a handful of placebo years this is a
    rough credibility check, not a formal null.

    Args:
        placebo: Output of `run_placebo` (one row per placebo year, with coef, p).
        real_coef: The real `is_year10` coefficient on the same native scale.
        alpha: Significance threshold for counting placebo hits.

    Returns:
        Dict with: lo and hi (min and max placebo coef), real_coef, inside (True if
        the real effect lies within the placebo spread), n_sig (placebo years with
        p < alpha), and n (number of placebo years).
    """
    coefs = placebo["coef"].to_numpy()
    lo, hi = float(coefs.min()), float(coefs.max())
    return {"lo": lo, "hi": hi, "real_coef": float(real_coef),
            "inside": bool(lo <= real_coef <= hi),
            "n_sig": int((placebo["p"] < alpha).sum()), "n": len(placebo)}


def standardized_placebo_frame(cells) -> pd.DataFrame:
    """Stack the nine placebo tests onto one standardized (coef/SE) scale.

    The nine (event type x metric) tests live on incomparable native scales: POD
    and FAR coefficients are log-odds, lead time is in minutes. Dividing each
    coefficient by its standard error yields the Wald statistic (coef/SE), a
    unitless standardized effect that is comparable across the logistic and OLS
    fits and whose +/-1.96 marks the usual two-sided 0.05 significance threshold.
    This builds the tidy long frame the consolidated placebo figure consumes: every
    placebo year and the real year-10 effect for all nine cells, one row each.

    The sign is left on the raw coefficient scale, so a positive z means a positive
    coefficient, whose performance meaning differs per metric (higher POD is better,
    higher FAR is worse, longer lead time is better). The figure caption states this
    convention rather than re-orienting the axis.

    Each year-10 row also carries the two-filter verdict the figure encodes:
    `outside_placebo` (the real coefficient lies beyond the min-max spread of that
    cell's placebo coefficients, computed here) and `survives_fdr` (the cell cleared
    the Benjamini-Hochberg correction across the family of nine, supplied by the
    caller from the synthesis table since that correction spans all cells and cannot
    be decided cell by cell). Placebo rows carry both as False.

    Args:
        cells: Iterable of dicts, one per (event, metric) cell, each with keys
            "event" (TO/SV/FF), "metric" (POD/FAR/LTA), "placebo" (a run_placebo
            DataFrame carrying coef and se), "main" (a fit_main_model dict carrying
            coef and se for the real year-10 effect), and "survives_fdr" (bool, the
            cell's BH-FDR survival from the synthesis table).

    Returns:
        DataFrame, one row per placebo year plus one per year-10 effect, columns:
        event, metric, label ("TO  POD"), kind ("placebo" or "year10"), z (coef/se),
        p, outside_placebo (bool), survives_fdr (bool). Cell order follows the input
        order so the figure rows stay grouped by event type.
    """
    rows = []
    for c in cells:
        ev, metric = c["event"], c["metric"]
        label = f"{ev}  {metric}"
        pl = c["placebo"]
        for _, r in pl.iterrows():
            rows.append({"event": ev, "metric": metric, "label": label,
                         "kind": "placebo", "z": float(r["coef"] / r["se"]),
                         "p": float(r["p"]), "outside_placebo": False,
                         "survives_fdr": False})
        m = c["main"]
        lo, hi = float(pl["coef"].min()), float(pl["coef"].max())
        rows.append({"event": ev, "metric": metric, "label": label,
                     "kind": "year10", "z": float(m["coef"] / m["se"]),
                     "p": float(m["p"]),
                     "outside_placebo": not (lo <= float(m["coef"]) <= hi),
                     "survives_fdr": bool(c["survives_fdr"])})
    return pd.DataFrame(rows)


def synthesis_table(results, alpha: float = 0.05) -> pd.DataFrame:
    """Assemble the nine year-10 tests into one false-discovery-corrected table.

    Collects the per-metric, per-event-type `is_year10` fits accumulated during the
    analysis and applies the Benjamini-Hochberg false-discovery-rate (FDR) correction
    across the whole nine-test family (three metrics times three event types). The raw
    per-test p-values overstate how many departures are real once nine tests are read
    together; the `p_fdr` column is the family-corrected p-value, and `survives` marks
    the tests that clear the threshold after correction. This is the single place the
    nine separate questions are read as a family, as the multiple-comparison caution
    requires.

    Args:
        results: Sequence of dicts as accumulated by the notebook's `report_fit`,
            each with at least event_type, metric, kind, n, coef, ci_low, ci_high,
            p, and (for logit) or.
        alpha: Threshold applied to the FDR-adjusted p-values for the `survives` flag.

    Returns:
        DataFrame, one row per test, with the raw fit columns plus `p_fdr` (BH-adjusted
        p-value), `survives` (bool, p_fdr < alpha), and `stars` (significance string on
        the FDR-adjusted p-value). Ordered by event type then metric.
    """
    df = pd.DataFrame(list(results)).copy()
    df["p_fdr"] = bh_fdr(df["p"].to_numpy())
    df["survives"] = df["p_fdr"] < alpha
    df["stars"] = [sig_stars(p) for p in df["p_fdr"]]
    type_order = pd.Categorical(df["event_type"], categories=["TO", "SV", "FF"], ordered=True)
    metric_order = pd.Categorical(df["metric"], categories=["POD", "FAR", "LTA"], ordered=True)
    df = df.assign(_t=type_order, _m=metric_order).sort_values(["_t", "_m"]).drop(columns=["_t", "_m"])
    return df.reset_index(drop=True)
