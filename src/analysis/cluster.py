# NWS Staffing Analysis - Storm-Clustering Helpers
# Developed with assistance from Claude Code (Anthropic)
#
# Appendix-only helpers that group correlated records into weather "outbreaks" and
# refit the year-10 model with cluster-robust standard errors. Storm reports are not
# independent: a single severe-weather outbreak generates dozens to hundreds of
# correlated rows in one office on one day. The main analysis (05_analysis) reports
# naive standard errors; these helpers quantify how much that independence assumption
# understates uncertainty, as a robustness demonstration on the one live finding
# (severe-storm false alarms). See the appendix section of 05_analysis.
#
# Two grouping choices are made here and are stated as choices, not load-bearing
# constants: the convective day is a noon-to-noon (12 UTC) window so an afternoon
# outbreak stays intact instead of splitting at midnight, and offices are linked into
# one multi-office outbreak when their report centroids fall within LINK_KM. Both were
# validated in exploration; vary them in a sensitivity pass (future work) before
# treating any single number as fixed.

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from sklearn.metrics.pairwise import haversine_distances

# Default linkage radius between office report-centroids, in kilometres. A stated
# choice (see module docstring), not a tuned constant.
LINK_KM = 300.0

EARTH_KM = 6371.0


def convective_day(ts: pd.Series, cutoff_hour: int = 12) -> pd.Series:
    """Map timestamps to a noon-to-noon convective-day date.

    Severe weather peaks in the afternoon and evening, so a calendar (UTC-midnight)
    day splits a single outbreak across two dates whenever it runs past 00 UTC. A
    convective day that rolls over at `cutoff_hour` UTC (noon by default) keeps the
    afternoon-into-evening outbreak in one bucket. The returned value is the date of
    the convective day each timestamp belongs to (the date after subtracting the
    cutoff), suitable as a grouping key on either the reports or the warnings table.

    Args:
        ts: Timezone-aware UTC timestamps (e.g. report `valid` or warning `issue`).
        cutoff_hour: Hour (UTC) at which the convective day rolls over (default 12).

    Returns:
        Series of `datetime.date`, the convective-day date for each timestamp.
    """
    return (ts - pd.Timedelta(hours=cutoff_hour)).dt.date


def build_outbreaks(reports: pd.DataFrame, link_km: float = LINK_KM,
                    cutoff_hour: int = 12) -> tuple[pd.Series, dict]:
    """Group storm reports into multi-office weather outbreaks.

    Reports carry real point coordinates (`lon0`, `lat0`), so an outbreak is defined
    on the reports table directly. Within each convective day, each office's report
    centroid (mean of its report coordinates that day) is a point; offices whose
    centroids fall within `link_km` great-circle of each other are linked into one
    outbreak via connected components. Offices that share no near neighbour that day
    form their own single-office outbreak. The result is the cluster key the appendix
    uses for the POD and lead-time models, and the key warnings are routed onto for
    the FAR model (see `route_warnings`).

    Linkage uses haversine (great-circle) distance on the centroids' latitude and
    longitude, so it has no fixed-latitude scaling bias across the continental U.S.

    Args:
        reports: Rows for one event type, with `wfo`, `valid` (UTC), `lon0`, `lat0`.
        link_km: Centroid linkage radius in kilometres (default LINK_KM).
        cutoff_hour: Convective-day rollover hour, passed through (default 12).

    Returns:
        (outbreak_id, key2outbreak):
          outbreak_id: integer Series aligned to `reports`, one outbreak id per row.
          key2outbreak: dict mapping (convective_day, wfo) -> outbreak id, so warnings
            can be routed onto the same outbreaks (see `route_warnings`).
    """
    df = reports[["wfo"]].copy()
    df["cday"] = convective_day(reports["valid"], cutoff_hour)
    unit = (reports.assign(cday=df["cday"])
            .groupby(["cday", "wfo"])
            .agg(lon=("lon0", "mean"), lat=("lat0", "mean"))
            .reset_index())

    next_id = 0
    key2outbreak: dict = {}
    for cday, grp in unit.groupby("cday"):
        if len(grp) == 1:
            key2outbreak[(cday, grp["wfo"].iloc[0])] = next_id
            next_id += 1
            continue
        coords = np.radians(grp[["lat", "lon"]].to_numpy())
        dist_km = haversine_distances(coords) * EARTH_KM
        adj = sparse.csr_matrix((dist_km < link_km).astype(int))
        _, labels = connected_components(adj, directed=False)
        base = next_id
        for wfo, label in zip(grp["wfo"], labels):
            key2outbreak[(cday, wfo)] = base + int(label)
        next_id = base + len(np.unique(labels))

    outbreak_id = pd.Series(
        [key2outbreak[(c, w)] for c, w in zip(df["cday"], df["wfo"])],
        index=reports.index, dtype=int, name="outbreak_id")
    return outbreak_id, key2outbreak


def route_warnings(warnings: pd.DataFrame, key2outbreak: dict,
                   cutoff_hour: int = 12) -> tuple[pd.Series, dict]:
    """Assign each warning to a report-defined outbreak by office and convective day.

    Warnings are polygons with no point coordinate, so they cannot define an outbreak
    centroid of their own. Instead each warning inherits the outbreak of its office on
    its convective day from `key2outbreak` (built by `build_outbreaks` on the reports
    table). A warning with no matching report-outbreak, almost always a false alarm in
    an office-day that produced no report at all, gets its own singleton cluster, the
    conservative choice: it contributes no within-cluster correlation. Routing by
    (office, convective-day) reproduces the exact report join almost perfectly (see the
    join-key validation in the appendix), so the precise LSR-to-warning join is not
    needed in the pipeline.

    Args:
        warnings: Rows for one event type, with `wfo` and `issue` (UTC).
        key2outbreak: (convective_day, wfo) -> outbreak id, from `build_outbreaks`.
        cutoff_hour: Convective-day rollover hour (default 12).

    Returns:
        (cluster_id, diagnostics):
          cluster_id: integer Series aligned to `warnings`, the cluster for each row
            (a report-outbreak id where routed, else a fresh singleton id).
          diagnostics: dict with n (warnings), n_routed, frac_routed, n_singleton.
    """
    cday = convective_day(warnings["issue"], cutoff_hour)
    routed = pd.Series([key2outbreak.get((c, w)) for c, w in zip(cday, warnings["wfo"])],
                       index=warnings.index, dtype="float")

    # Hand each unrouted warning its own cluster id, numbered above every report id so
    # there is no collision with a real outbreak.
    next_id = (max(key2outbreak.values()) + 1) if key2outbreak else 0
    missing = routed.isna()
    routed.loc[missing] = np.arange(next_id, next_id + int(missing.sum()))
    cluster_id = routed.astype(int)
    cluster_id.name = "cluster_id"

    diagnostics = {"n": len(warnings), "n_routed": int((~missing).sum()),
                   "frac_routed": float((~missing).mean()),
                   "n_singleton": int(missing.sum())}
    return cluster_id, diagnostics


def validate_routing(reports: pd.DataFrame, warnings: pd.DataFrame,
                     outbreak_id: pd.Series, cluster_id: pd.Series) -> dict:
    """Check that warnings route to the same outbreak as their linked report.

    Each storm report carries the id of the warning it was matched to (`events`), and
    each warning carries its own id (`product_id`); the two are the precise
    LSR-to-warning join. This cross-check confirms the cheap (office, convective-day)
    routing in `route_warnings` reproduces that exact join: for every warning whose id
    appears as a report's `events`, it compares the warning's routed cluster against
    the outbreak of its joined report. High agreement means the precise join is not
    needed in the pipeline, the (office, convective-day) key suffices.

    Args:
        reports: Report rows for one event type, with `events` and the outbreak id.
        warnings: Warning rows for one event type, with `product_id` and cluster id.
        outbreak_id: Outbreak id aligned to `reports` (from `build_outbreaks`).
        cluster_id: Cluster id aligned to `warnings` (from `route_warnings`).

    Returns:
        Dict with n_linked (warnings joinable to a report) and frac_agree (share of
        those whose routed cluster equals their joined report's outbreak).
    """
    rep = reports.assign(_ob=outbreak_id).dropna(subset=["events"])
    report_outbreak = rep.groupby("events")["_ob"].agg(lambda s: s.mode().iloc[0])

    war = warnings.assign(_cl=cluster_id)
    joined = war.assign(_join_ob=war["product_id"].map(report_outbreak)).dropna(
        subset=["_join_ob"])
    agree = (joined["_join_ob"].astype(int) == joined["_cl"]).mean()
    return {"n_linked": int(len(joined)), "frac_agree": float(agree)}


def clustered_year10(df: pd.DataFrame, outcome_col: str, kind: str,
                     groups: pd.Series) -> dict:
    """Refit the year-10 model naive and cluster-robust, and report the SE inflation.

    Fits the same `outcome ~ C(season_cat) + study_year + is_year10` model as
    `stats.fit_main_model`, once with default (independence) standard errors and once
    with covariance clustered on `groups` (the outbreak / cluster id). The point
    estimate is identical between the two; only the standard error, confidence
    interval and p-value of the `is_year10` term change. The ratio of clustered to
    naive standard error is the design effect of storm clustering on this metric: how
    much the independence assumption understated uncertainty.

    Args:
        df: Rows for one event type and metric (caller subsets; for lead time, warned
            reports only).
        outcome_col: Outcome column ("warned", "verify"/"false_alarm", or "leadtime").
        kind: "logit" for the binary metrics, "ols" for lead time.
        groups: Cluster id aligned to `df` (outbreak id, or routed cluster id).

    Returns:
        Dict with coef (is_year10, native scale, shared by both fits); naive_se,
        naive_p, naive_ci_low, naive_ci_high; clustered_se, clustered_p,
        clustered_ci_low, clustered_ci_high; se_inflation (clustered_se / naive_se);
        n (rows) and n_clusters. For logit the coef is log-odds (exponentiate for an
        odds ratio); for OLS it is minutes.
    """
    f = f"{outcome_col} ~ C(season_cat) + study_year + is_year10"
    fit = (lambda **kw: smf.logit(f, data=df).fit(disp=0, **kw)) if kind == "logit" \
        else (lambda **kw: smf.ols(f, data=df).fit(**kw))

    naive = fit()
    clustered = fit(cov_type="cluster", cov_kwds={"groups": groups})

    coef = float(naive.params["is_year10"])
    n_ci = naive.conf_int().loc["is_year10"]
    c_ci = clustered.conf_int().loc["is_year10"]
    naive_se = float(naive.bse["is_year10"])
    clustered_se = float(clustered.bse["is_year10"])
    return {"coef": coef, "n": int(naive.nobs), "n_clusters": int(groups.nunique()),
            "naive_se": naive_se, "naive_p": float(naive.pvalues["is_year10"]),
            "naive_ci_low": float(n_ci[0]), "naive_ci_high": float(n_ci[1]),
            "clustered_se": clustered_se, "clustered_p": float(clustered.pvalues["is_year10"]),
            "clustered_ci_low": float(c_ci[0]), "clustered_ci_high": float(c_ci[1]),
            "se_inflation": clustered_se / naive_se}
