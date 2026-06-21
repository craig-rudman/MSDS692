# NWS Staffing Analysis - COW Data Cleaner
# Developed with assistance from Claude Code (Anthropic)
#
# Applies all cleaning transformations to the extracted events and
# stormreports tables. Each method is a discrete cleaning step so that
# the notebook can invoke them individually for documentation purposes.
# The clean_events() and clean_stormreports() convenience methods run all
# steps in order and write processed CSVs to data/03_cleaning/.

import json
import logging
import time
import urllib.request
from pathlib import Path

import pandas as pd

from src.constants import CUT_DATE, NON_CONUS

log = logging.getLogger(__name__)

# Terminal-status priority for event deduplication. The COW API returns one
# row per issuance status (NEW, CON, EXT, EXP, CAN, COR); lower rank = more
# terminal and takes precedence when keeping one row per (wfo,year,phenomena,eventid).
STATUS_PRIORITY = {"CAN": 0, "COR": 1, "EXP": 2, "EXT": 3, "CON": 4, "NEW": 5}

# Events columns with no analytical value. See notebook cell documentation
# for the rationale behind each group.
#
# Storm-mode covariates retained for regression (NOT dropped):
#   svr_tornado_possible, tor_in_svrtorpossible — forecaster-flagged triage indicators
#   hailtag, windtag — storm intensity proxies for SV warnings
#   carea, parea, sharedborder — warning geometry / outbreak density proxies
EVENTS_DROP_COLS = [
    "significance",
    "perimeter", "areaverify", "lat0", "lon0",
    "ar_ugc", "ar_ugcname",
    "visual_imgurl", "product_text", "product_href", "link",
    "stormreports", "stormreports_all",
    "fcster",
    "statuses",  # identical to status after deduplication — pre-dedup API artifact
]

# Storm reports columns with no analytical value.
STORMREPORTS_DROP_COLS = ["type", "magnitude", "link"]

# Canonical mapping for source normalization. Handles truncation artifacts,
# spelling variants, abbreviation variants, automated station codes, and junk.
SOURCE_CANONICAL = {
    # Truncation artifacts — leading character(s) clipped
    "MERGENCY MNGR":    "EMERGENCY MNGR",
    "EMERGENCY MANAGE": "EMERGENCY MNGR",
    "STATE EMRG MGMT":  "EMERGENCY MNGR",
    "UBLIC":            "PUBLIC",
    "ESONET":           "MESONET",
    "TILITY COMPANY":   "UTILITY COMPANY",
    "AW ENFORCEMENT":   "LAW ENFORCEMENT",
    "RAINED SPOTTER":   "TRAINED SPOTTER",
    "ROADCAST MEDIA":   "BROADCAST MEDIA",
    "IRE DEPT/RESCUE":  "FIRE DEPT/RESCUE",
    "11 CALL CENTER":   "911 CALL CENTER",
    "EPT OF HIGHWAYS":  "DEPT OF HIGHWAYS",
    "DEPT OF":          "DEPT OF HIGHWAYS",
    "WS STORM SURVEY":  "NWS STORM SURVEY",
    "NWS STORM":        "NWS STORM SURVEY",
    "NWS DAMAGE SURVEY":"NWS STORM SURVEY",
    "NWS ALBANY OFFIC": "NWS OFFICE",
    "NWS":              "NWS EMPLOYEE",
    "PARK SRVC":        "PARK/FOREST SRVC",
    # Misspelled / abbreviated variants
    "COUNTY EMERGY MG":   "COUNTY OFFICIAL",
    "COUNTY EMERGY MGMT": "COUNTY OFFICIAL",
    "LOCAL OFFICIAL":     "COUNTY OFFICIAL",
    "CITY OFFICIAL":      "COUNTY OFFICIAL",
    "STATE OFFICIAL":     "COUNTY OFFICIAL",
    "TRIBAL LEADER":      "TRIBAL OFFICIAL",
    "HAM RADIO":          "AMATEUR RADIO",
    "MEDIA":              "BROADCAST MEDIA",
    "NEWSPAPER":          "PRINT MEDIA",
    "WTEN":               "BROADCAST MEDIA",
    "POSTAL EMPLOYEE":    "POST OFFICE",
    "METEOROLOGIST":      "NWS EMPLOYEE",
    "RETIRED NWS EMP.":   "NWS EMPLOYEE",
    "WX OBSERVER FAA":    "AIRPLANE PILOT",
    "TX DOT":             "DEPT OF HIGHWAYS",
    "NMDOT":              "DEPT OF HIGHWAYS",
    # Automated station network codes collapsed to one category
    "WEATHERFLOW":     "AUTOMATED STATION",
    "WXFLOW":          "AUTOMATED STATION",
    "MESOWEST":        "AUTOMATED STATION",
    "NYS MESONET":     "AUTOMATED STATION",
    "NYSM":            "AUTOMATED STATION",
    "MPING":           "AUTOMATED STATION",
    "APRSWXNET/CWOP":  "AUTOMATED STATION",
    "HADS":            "AUTOMATED STATION",
    "RAWS":            "AUTOMATED STATION",
    "DEOS2":           "AUTOMATED STATION",
    "NOS":             "AUTOMATED STATION",
    "NOS-PORTS":       "AUTOMATED STATION",
    "TIDE GAGE":       "AUTOMATED STATION",
    "C-MAN STATION":   "AUTOMATED STATION",
    "BUOY":            "AUTOMATED STATION",
    "SHIP":            "AUTOMATED STATION",
    # Junk / unresolvable
    "X":       "not_provided",
    "NONE":    "not_provided",
    "UNKNOWN": "not_provided",
    "FIRE":    "not_provided",
}

# Nominatim address keys tried in order for city and county imputation.
CITY_KEYS   = ("city", "town", "village", "hamlet")
COUNTY_KEYS = ("county", "city", "state_district")

# Seasonal-window boundaries as (month, day) tuples, half-open [start, next).
# Each window is three months; Winter wraps the calendar-year boundary. The
# Spring boundary is the treatment anniversary (CUT_DATE, Feb 27), taken from the
# shared constant so the season grid and the treatment anchor cannot drift apart;
# the other boundaries are three-month offsets from it. So every *-Spring season
# aligns to the same treatment-relative boundary across years. The label year is
# taken from the window's first day, so Jan 1–Feb 26 belongs to the PRIOR year's
# Winter (e.g. 2026-02-15 → "2025-Winter").
_SPRING_START = (CUT_DATE.month, CUT_DATE.day)  # (2, 27) from the treatment anchor
SEASON_BOUNDS = [
    (_SPRING_START, (5, 27), "Spring"),
    ((5, 27), (8, 27), "Summer"),
    ((8, 27), (11, 27), "Fall"),
]  # Winter (Nov 27 – Feb 26) is the implicit complement; handled in _season_label.

# Season-of-year categories, in chronological order within a study year.
SEASON_CATS = ["Spring", "Summer", "Fall", "Winter"]

# The study span runs from 2016-Spring (season_year 2016) through 2025-Winter
# (season_year 2025). study_year is a 1-based index over those ten season years:
# study_year = season_year - STUDY_START_YEAR + 1 maps 2016 -> 1 ... 2025 -> 10.
# This is a treatment-relative index, NOT a calendar year. A January 2026 row
# labels as 2025-Winter, season_year 2025, study_year 10. study_year 10 is the
# treated period (the staffing cut anniversary anchors every Spring boundary).
STUDY_START_YEAR = 2016
STUDY_END_YEAR = 2025
TREATED_STUDY_YEAR = STUDY_END_YEAR - STUDY_START_YEAR + 1  # 10


class COWCleaner:
    """Applies cleaning transformations to extracted events and stormreports DataFrames.

    Each public method performs one discrete cleaning step so that callers
    (notebooks) can invoke them individually and inspect intermediate state.
    The clean_events() and clean_stormreports() convenience methods run all
    steps in sequence and return the cleaned DataFrame.

    Null city/county imputation calls the Nominatim reverse-geocoding API,
    which requires a network connection. This step is isolated so it can be
    skipped if needed.
    """

    def __init__(self, processed_dir: Path, cache_dir: Path | None = None):
        """
        Args:
            processed_dir: Directory where cleaned CSV files will be written.
            cache_dir:     Directory for the persisted geocode cache. Defaults
                           to a 'cache' sibling of processed_dir. The cache maps
                           a rounded (lat, lon) key to its Nominatim address
                           dict so repeat runs skip the API call and its rate
                           limit; it is shared by city and county imputation.
        """
        self.processed_dir = Path(processed_dir)
        self.cache_dir = Path(cache_dir) if cache_dir else self.processed_dir.parent / "cache"
        self._geocode_cache_path = self.cache_dir / "geocode_cache.json"
        self._geocode_cache = self._load_geocode_cache()

    def _load_geocode_cache(self) -> dict:
        """Load the persisted geocode cache, or start empty if none exists."""
        if self._geocode_cache_path.exists():
            with open(self._geocode_cache_path) as f:
                cache = json.load(f)
            log.info(f"Loaded geocode cache: {len(cache):,} entries from {self._geocode_cache_path}")
            return cache
        log.info("No geocode cache found; starting empty")
        return {}

    def _save_geocode_cache(self) -> None:
        """Persist the geocode cache to disk, creating the cache dir if needed."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with open(self._geocode_cache_path, "w") as f:
            json.dump(self._geocode_cache, f, indent=1, sort_keys=True)
        log.info(f"Saved geocode cache: {len(self._geocode_cache):,} entries")

    def _resolve_address(self, lat: float, lon: float) -> dict:
        """Return the address dict for a coordinate, using the cache first.

        On a cache miss, fetches from Nominatim and stores the result, pausing
        1 second afterward to respect the usage policy. A failed fetch is not
        cached, so it is retried on a later run rather than poisoning the cache
        with a permanent miss. Cache hits incur no delay.
        """
        key = _geocode_key(lat, lon)
        if key in self._geocode_cache:
            return self._geocode_cache[key]

        addr = _fetch_address(lat, lon)
        time.sleep(1)
        if addr is None:
            return {}  # fetch failed; do not cache, retry next run
        self._geocode_cache[key] = addr
        return addr

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def drop_event_columns(self, events: pd.DataFrame) -> pd.DataFrame:
        """Drop columns with no analytical value from the events table.

        Storm-mode covariates (svr_tornado_possible, tor_in_svrtorpossible,
        hailtag, windtag, carea, parea, sharedborder) are intentionally
        retained for use as regression covariates in 05_analysis.ipynb.
        See EVENTS_DROP_COLS for the full drop list and rationale.

        Args:
            events: Raw extracted events DataFrame.

        Returns:
            DataFrame with uninformative columns removed.
        """
        dropped = [c for c in EVENTS_DROP_COLS if c in events.columns]
        result = events.drop(columns=dropped)
        log.info(f"Dropped {len(dropped)} event columns; {len(result.columns)} remaining")
        return result

    def deduplicate_events(self, events: pd.DataFrame) -> pd.DataFrame:
        """Keep one row per warning event at its terminal status.

        The COW API returns one row per issuance status (NEW, CON, EXT,
        EXP, CAN, COR). This method keeps the most terminal status row per
        (wfo, year, phenomena, eventid) using STATUS_PRIORITY.

        Args:
            events: Events DataFrame that may contain multiple status rows
                    per warning.

        Returns:
            Deduplicated DataFrame with one row per warning.
        """
        before = len(events)
        events = events.copy()
        events["_status_rank"] = events["status"].map(STATUS_PRIORITY).fillna(9).astype(int)
        result = (
            events
            .sort_values("_status_rank")
            .drop_duplicates(subset=["wfo", "year", "phenomena", "eventid"], keep="first")
            .drop(columns="_status_rank")
            .reset_index(drop=True)
        )
        log.info(f"Deduplicated events: {before:,} → {len(result):,} rows (removed {before - len(result):,})")
        return result

    def parse_event_timestamps(self, events: pd.DataFrame) -> pd.DataFrame:
        """Parse issue/expire to UTC datetimes and derive duration_min.

        Args:
            events: Events DataFrame with string issue and expire columns.

        Returns:
            DataFrame with issue and expire as UTC-aware datetimes and a
            new duration_min column (warning duration in minutes).
        """
        result = events.copy()
        result["issue"]  = pd.to_datetime(result["issue"],  utc=True)
        result["expire"] = pd.to_datetime(result["expire"], utc=True)
        result["duration_min"] = (result["expire"] - result["issue"]).dt.total_seconds() / 60
        log.info("Parsed issue/expire timestamps; derived duration_min")
        return result

    def cap_lead0(self, events: pd.DataFrame) -> pd.DataFrame:
        """Cap extreme lead0 values at the 99th percentile per phenomena.

        lead0 is the API-supplied lead time in minutes for the first
        confirming storm report. FF warnings can have physically implausible
        values (max ~7,900 min) from spatial overlap with reports days later.
        Capped rows are flagged with lead0_capped=True.

        Args:
            events: Events DataFrame with numeric lead0 column.

        Returns:
            DataFrame with lead0 capped and lead0_capped flag column added.
        """
        result = events.copy()
        result["lead0_capped"] = False
        verified_mask = result["verify"] == True
        caps = result[verified_mask].groupby("phenomena")["lead0"].quantile(0.99)

        for phenomena, cap in caps.items():
            mask = verified_mask & (result["phenomena"] == phenomena) & (result["lead0"] > cap)
            result.loc[mask, "lead0_capped"] = True
            result.loc[mask, "lead0"] = cap
            log.info(f"lead0 cap: {phenomena} cap={cap:.0f} min, {mask.sum():,} rows capped")

        return result

    def derive_product_id(self, events: pd.DataFrame) -> pd.DataFrame:
        """Derive the VTEC product_id join key for each event.

        Format: {year}{wfo}{eventid}{phenomena}W1 (e.g. 2020ABQ41SVW1).
        This matches the value in stormreports.events (the FK column) so
        the two tables can be joined unambiguously.

        Args:
            events: Events DataFrame with year, wfo, eventid, phenomena columns.

        Returns:
            DataFrame with product_id column added.
        """
        result = events.copy()
        result["product_id"] = (
            result["year"].astype(str)
            + result["wfo"]
            + result["eventid"].astype(str)
            + result["phenomena"]
            + "W1"
        )
        log.info(f"Derived product_id for {len(result):,} events")
        return result

    def derive_season(self, df: pd.DataFrame, time_col: str) -> pd.DataFrame:
        """Derive the YYYY-Season label and model-ready time columns.

        Season windows are three months with half-open [start, next) boundaries:
        Spring (Feb 27 – May 26), Summer (May 27 – Aug 26), Fall (Aug 27 –
        Nov 26), Winter (Nov 27 – Feb 26). Winter wraps the calendar-year
        boundary; the label year is the window's first day, so Jan 1–Feb 26
        carries the PRIOR year's Winter label (e.g. 2026-02-15 → "2025-Winter").

        Must run after the timestamp-parse step, since it reads a UTC-aware
        datetime. The season label is distinct from the calendar `year` field:
        a January row has year=2026 but season="2025-Winter".

        From the YYYY-Season label this derives the columns the models consume,
        so every time term traces back to the season label rather than the
        calendar timestamp (the two disagree at the Winter wrap):

          season_cat   season-of-year category (Spring/Summer/Fall/Winter), the
                       4-level categorical for C(season_cat).
          season_year  the YYYY anchor (the window's first-day year).
          study_year   1-based treatment-relative index, season_year - 2015,
                       so 2016 -> 1 ... 2025 -> 10. Named study_year, not year,
                       to avoid confusion with the calendar year field.
          is_year10    integer 0/1 treated indicator, 1 where study_year == 10.
                       Derived from study_year, never hand-entered.

        This labels every row, including the 2015-Winter wrap of the earliest
        data and any 2026 rows past the study window. Restricting to the ten
        study seasons is a separate, explicit step (clip_to_study_span), so the
        drop is visible and logged rather than buried in a labeler.

        Args:
            df:       Events or stormreports DataFrame.
            time_col: Name of the parsed UTC datetime column to bin on
                      ('issue' for events, 'valid' for stormreports).

        Returns:
            DataFrame with season, season_cat, season_year, study_year, and
            is_year10 columns added.

        Raises:
            ValueError: If any row fails to bin to a season, or if a parsed
                season category is not one of the four expected labels.
        """
        result = df.copy()
        result["season"] = result[time_col].map(_season_label)

        missing = result["season"].isna().sum()
        if missing:
            raise ValueError(
                f"derive_season: {missing} rows did not bin to a season from "
                f"{time_col!r}; refusing to emit silent NaNs in a model column."
            )

        # Split YYYY-Season into its two components. The label is the single
        # source of truth for both the categorical and the numeric time terms.
        parts = result["season"].str.split("-", n=1, expand=True)
        result["season_year"] = parts[0].astype(int)
        result["season_cat"] = parts[1]
        result["study_year"] = result["season_year"] - STUDY_START_YEAR + 1
        result["is_year10"] = (result["study_year"] == TREATED_STUDY_YEAR).astype(int)

        bad_cat = set(result["season_cat"].unique()) - set(SEASON_CATS)
        if bad_cat:
            raise ValueError(f"derive_season: unexpected season categories {bad_cat}.")

        log.info(
            f"Derived season from {time_col!r}: {result['season'].nunique()} "
            f"labels, study_year {result['study_year'].min()}-"
            f"{result['study_year'].max()}"
        )
        return result

    def clip_to_conus(self, df: pd.DataFrame) -> pd.DataFrame:
        """Restrict to the continental United States (CONUS) by Weather Forecast Office.

        The study footprint is CONUS only. The extracted data also carries the
        non-CONUS offices (Guam, Honolulu, the Alaska offices, and Pago Pago;
        see NON_CONUS), which have different climatology and reporting practice
        and are out of scope. This step drops their rows as an explicit, logged
        operation so the geographic scope is enforced once, globally, on the
        cleaned tables rather than re-derived in each downstream consumer.

        Clipping is by WFO code, not by coordinate: warnings are areas with no
        single point, so the office code is the one key common to both tables.

        Args:
            df: Events or stormreports DataFrame with a wfo column.

        Returns:
            DataFrame containing only rows from CONUS offices.

        Raises:
            ValueError: If no rows remain after clipping.
        """
        in_conus = ~df["wfo"].isin(NON_CONUS)
        dropped = df.loc[~in_conus]
        if len(dropped):
            by_wfo = dropped["wfo"].value_counts().sort_index()
            detail = ", ".join(f"{wfo}={n:,}" for wfo, n in by_wfo.items())
            log.info(
                f"clip_to_conus: dropping {len(dropped):,} of {len(df):,} rows "
                f"from {dropped['wfo'].nunique()} non-CONUS offices ({detail})"
            )

        result = df.loc[in_conus].copy()
        if result.empty:
            raise ValueError("clip_to_conus: no rows remain after clipping to CONUS.")

        log.info(
            f"clip_to_conus: kept {len(result):,} rows from {result['wfo'].nunique()} "
            f"CONUS offices"
        )
        return result

    def clip_to_study_span(self, df: pd.DataFrame) -> pd.DataFrame:
        """Restrict to the ten study seasons (2016-Spring through 2025-Winter).

        The extracted data extends beyond the study window: a 2015-Winter wrap
        of the earliest January/February data, and 2026 rows collected after the
        window closed (the collection ran to mid-2026). Those rows are real but
        out of scope. This step drops them as an explicit, logged operation so
        the study window is enforced once, globally, rather than re-derived in
        each model fit.

        Must run after derive_season, since it reads season_year/study_year.

        Args:
            df: Events or stormreports DataFrame with season columns derived.

        Returns:
            DataFrame containing only rows with season_year in the study span.

        Raises:
            ValueError: If the result is empty or has no rows in the treated
                period (study_year == 10).
        """
        in_span = df["season_year"].between(STUDY_START_YEAR, STUDY_END_YEAR)
        dropped = df.loc[~in_span]
        if len(dropped):
            by_label = dropped["season"].value_counts().sort_index()
            detail = ", ".join(f"{lbl}={n:,}" for lbl, n in by_label.items())
            log.info(
                f"clip_to_study_span: dropping {len(dropped):,} of {len(df):,} "
                f"rows outside {STUDY_START_YEAR}-Spring..{STUDY_END_YEAR}-Winter "
                f"({detail})"
            )

        result = df.loc[in_span].copy()
        if result.empty:
            raise ValueError("clip_to_study_span: no rows remain within the study span.")
        if result["is_year10"].sum() == 0:
            raise ValueError(
                "clip_to_study_span: no rows in the treated period (study_year "
                f"{TREATED_STUDY_YEAR}); is_year10 would be all zeros."
            )

        log.info(
            f"clip_to_study_span: kept {len(result):,} rows, study_year "
            f"{result['study_year'].min()}-{result['study_year'].max()}, "
            f"{result['is_year10'].sum():,} treated rows"
        )
        return result

    def cast_outcome(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        """Cast a boolean outcome column to integer 0/1 for modeling.

        The logistic models require integer 0/1 outcomes (`warned` for POD on
        storm reports, `verify` for FAR on events). Casting here, once, makes
        the cleaned CSVs model-ready and avoids a per-fit .astype(int) that is
        easy to forget. It also avoids a CSV round-trip issue: a boolean column
        serializes as True/False strings and reads back as object dtype, so a
        0/1 integer column reloads cleanly while a boolean one would not.

        Fails loudly if the column is missing, contains NaN, or holds anything
        other than True/False, since a stray value coercing into an outcome
        would silently corrupt a model fit.

        Args:
            df:  Events or stormreports DataFrame.
            col: Name of the boolean outcome column ('verify' or 'warned').

        Returns:
            DataFrame with `col` cast to int64 (0/1).

        Raises:
            ValueError: If the column is missing, has NaN, or is not boolean.
        """
        if col not in df.columns:
            raise ValueError(f"cast_outcome: column {col!r} not found.")

        n_missing = df[col].isna().sum()
        if n_missing:
            raise ValueError(
                f"cast_outcome: {col!r} has {n_missing} NaN values; refusing "
                f"to coerce missing data into a 0/1 outcome."
            )

        observed = set(df[col].unique())
        if not observed <= {True, False}:
            raise ValueError(
                f"cast_outcome: {col!r} contains non-boolean values {observed}; "
                f"expected only True/False."
            )

        result = df.copy()
        result[col] = result[col].astype(int)
        counts = result[col].value_counts().to_dict()
        log.info(f"Cast {col!r} to int 0/1: {counts}")
        return result

    # ------------------------------------------------------------------
    # Storm Reports
    # ------------------------------------------------------------------

    def repair_malformed_rows(self, stormreports: pd.DataFrame) -> pd.DataFrame:
        """Repair rows corrupted by a fixed-width field overflow bug in the IEM API.

        When a long remark is serialized, the API occasionally overflows into
        adjacent fixed-width columns, corrupting lat0, lon0, state, county, and
        source. Four distinct corruption patterns are present in the dataset:

        1. lat0 truncation with a clean duplicate present — the leading digit(s)
           of lat0 were consumed by the preceding field (e.g. 32.91 → 2.91).
           A clean copy of the same report exists in the same file. The corrupt
           row is dropped; the clean copy is retained.

        2. lat0 truncation with no clean duplicate — same overflow as above but
           the corrupt row is the only copy. The missing leading digit is inferred
           from the WFO's latitude range and prepended to restore the value.

        3. lon0 sign loss — the negative sign was consumed, producing a positive
           longitude (e.g. -89.15 → 89.15). Detected as CONUS WFO with lon0 > 0;
           repaired by negating lon0.

        4. Junk state/county with valid coordinates — state and county contain
           placeholder values (XX, XXX) but lat0/lon0 are correct. State is
           inferred from the WFO's known state; county is imputed via Nominatim
           in the subsequent impute_null_counties() step.

        This method must run before any step that reads the affected columns.
        GUM (Guam/Saipan) reports with positive lon0 are legitimate — they are
        identified by wfo='GUM' and left untouched.

        Args:
            stormreports: Extracted stormreports DataFrame.

        Returns:
            DataFrame with malformed rows repaired or removed.
        """
        result = stormreports.copy()

        # --- Case 1: lat0 truncation — drop corrupt rows that have a clean duplicate ---
        # Corrupt rows have lat0 < 10 with a valid CONUS lon0. For each, check
        # whether a clean copy exists (same wfo, valid, lsrtype, lon0, lat0 >= 10).
        corrupt_mask = (
            (result["lat0"] < 10) &
            (result["lon0"] >= -180) & (result["lon0"] <= -60)
        )
        drop_idx = []
        repair_idx = []
        for idx in result[corrupt_mask].index:
            row = result.loc[idx]
            clean = result[
                (result["wfo"] == row["wfo"]) &
                (result["valid"] == row["valid"]) &
                (result["lsrtype"] == row["lsrtype"]) &
                (result["lon0"] == row["lon0"]) &
                (result["lat0"] >= 10)
            ]
            if len(clean) >= 1:
                drop_idx.append(idx)
            else:
                repair_idx.append(idx)

        if drop_idx:
            result = result.drop(index=drop_idx).reset_index(drop=True)
            log.warning(f"Dropped {len(drop_idx)} corrupt rows with clean duplicates present")

        # --- Case 2: lat0 truncation — repair rows with no clean duplicate ---
        # The missing leading digit is inferred by finding the prefix p that
        # places the repaired lat0 closest to the median lat0 of other clean
        # rows from the same WFO (the most reliable within-dataset reference).
        for idx in result[(result["lat0"] < 10) & (result["lon0"].between(-180, -60))].index:
            corrupt_lat = result.at[idx, "lat0"]
            wfo = result.at[idx, "wfo"]
            wfo_median = result.loc[
                (result["wfo"] == wfo) & (result["lat0"] >= 10), "lat0"
            ].median()
            best_prefix = min(range(1, 7), key=lambda p: abs(p * 10 + corrupt_lat - wfo_median))
            repaired = best_prefix * 10 + corrupt_lat
            result.at[idx, "lat0"] = repaired
            log.warning(f"Repaired lat0: idx={idx} wfo={wfo} {corrupt_lat} → {repaired}")

        # --- Case 3: lon0 sign loss — negate positive CONUS longitudes ---
        # GUM (Guam/Saipan) legitimately has positive lon0; skip it.
        sign_mask = (result["lon0"] > 0) & (result["wfo"] != "GUM")
        if sign_mask.sum():
            result.loc[sign_mask, "lon0"] = -result.loc[sign_mask, "lon0"]
            log.warning(f"Repaired lon0 sign for {sign_mask.sum()} rows")

        # --- Case 4: junk state/county with valid coordinates ---
        # Replace placeholder state values with null so impute_null_counties()
        # will resolve them via Nominatim. State is set to null here; a
        # dedicated state-inference step is not warranted for 1 row.
        junk_state_mask = result["state"].isin(["XX", "  ", "X "])
        if junk_state_mask.sum():
            result.loc[junk_state_mask, "state"] = None
            result.loc[junk_state_mask, "county"] = None
            log.warning(f"Nulled junk state/county for {junk_state_mask.sum()} rows")

        return result

    def drop_stormreport_columns(self, stormreports: pd.DataFrame) -> pd.DataFrame:
        """Drop columns with no analytical value from the stormreports table.

        Drops type (duplicates lsrtype), magnitude (67% null, not used in
        any planned analysis), and link (URL blob). Retains lon0/lat0 for
        spatial EDA and events as the FK trace link to matched warnings.

        Args:
            stormreports: Raw extracted stormreports DataFrame.

        Returns:
            DataFrame with uninformative columns removed.
        """
        dropped = [c for c in STORMREPORTS_DROP_COLS if c in stormreports.columns]
        result = stormreports.drop(columns=dropped)
        log.info(f"Dropped {len(dropped)} stormreport columns; {len(result.columns)} remaining")
        return result

    def parse_stormreport_timestamps(self, stormreports: pd.DataFrame) -> pd.DataFrame:
        """Parse valid to a UTC-aware datetime.

        Args:
            stormreports: Storm reports DataFrame with string valid column.

        Returns:
            DataFrame with valid as a UTC-aware datetime.
        """
        result = stormreports.copy()
        result["valid"] = pd.to_datetime(result["valid"], utc=True)
        log.info("Parsed stormreports.valid timestamps")
        return result

    def normalize_source(self, stormreports: pd.DataFrame) -> pd.DataFrame:
        """Normalize the source column to a consistent set of categories.

        Applies SOURCE_CANONICAL to resolve truncation artifacts, spelling
        variants, abbreviation variants, and automated station codes. Nulls
        and unresolvable junk values become "not_provided".

        Args:
            stormreports: Storm reports DataFrame with raw source column.

        Returns:
            DataFrame with normalized source values.
        """
        result = stormreports.copy()
        before = result["source"].nunique()
        result["source"] = (
            result["source"]
            .str.strip()
            .str.upper()
            .map(lambda s: SOURCE_CANONICAL.get(s, s) if pd.notna(s) else "not_provided")
        )
        after = result["source"].nunique()
        log.info(f"Normalized source: {before} → {after} unique values")
        return result

    def cap_leadtime(self, stormreports: pd.DataFrame) -> pd.DataFrame:
        """Cap extreme leadtime values at the 99th percentile per lsrtype.

        leadtime is the API-supplied lead time in minutes between warning
        issuance and storm report time. FF has a max of ~7,996 min from
        spatial overlap matches; TO and SV are naturally bounded. Capped
        rows are flagged with leadtime_capped=True.

        Args:
            stormreports: Storm reports DataFrame with numeric leadtime column.

        Returns:
            DataFrame with leadtime capped and leadtime_capped flag added.
        """
        result = stormreports.copy()
        result["leadtime_capped"] = False
        warned_mask = result["warned"] == True
        caps = result[warned_mask].groupby("lsrtype")["leadtime"].quantile(0.99)

        for lsrtype, cap in caps.items():
            mask = warned_mask & (result["lsrtype"] == lsrtype) & (result["leadtime"] > cap)
            result.loc[mask, "leadtime_capped"] = True
            result.loc[mask, "leadtime"] = cap
            log.info(f"leadtime cap: {lsrtype} cap={cap:.0f} min, {mask.sum():,} rows capped")

        return result

    def impute_null_cities(self, stormreports: pd.DataFrame) -> pd.DataFrame:
        """Impute null city values via Nominatim reverse geocoding.

        For each row with a null city, resolves the address for lon0/lat0
        (cache first, Nominatim on a miss) and returns the most specific named
        place (city → town → village → hamlet). Falls back to "not_provided"
        for rural locations that don't resolve.

        The shared geocode cache is persisted after the pass, so reruns skip
        the API call and its 1-second rate limit for coordinates seen before.

        Args:
            stormreports: Storm reports DataFrame with city, lon0, lat0 columns.

        Returns:
            DataFrame with null city values imputed.
        """
        result = stormreports.copy()
        null_mask = result["city"].isnull()
        count = null_mask.sum()

        if count == 0:
            log.info("No null city values to impute")
            return result

        start_size = len(self._geocode_cache)
        log.info(f"Imputing {count} null city values (cache: {start_size:,} entries) ...")
        for idx in result[null_mask].index:
            lat, lon = result.at[idx, "lat0"], result.at[idx, "lon0"]
            city = _pick_address_field(self._resolve_address(lat, lon), CITY_KEYS)
            result.at[idx, "city"] = city
            log.info(f"  city imputed: idx={idx} ({lat}, {lon}) → {city!r}")

        log.info(f"city imputation: {len(self._geocode_cache) - start_size:,} new cache entries")
        self._save_geocode_cache()
        return result

    def impute_null_counties(self, stormreports: pd.DataFrame) -> pd.DataFrame:
        """Impute null county values via Nominatim reverse geocoding.

        For each row with a null county, resolves the address for lon0/lat0
        (cache first, Nominatim on a miss) and falls through county → city
        (for unified city-boroughs like Juneau) → state_district →
        "not_provided". Handles Alaska boroughs and the Unorganized Borough
        where Nominatim may return no county.

        The shared geocode cache is persisted after the pass. Because city
        imputation runs first and caches the same coordinates, county
        imputation often resolves entirely from cache with no API calls.

        Args:
            stormreports: Storm reports DataFrame with county, lon0, lat0 columns.

        Returns:
            DataFrame with null county values imputed.
        """
        result = stormreports.copy()
        null_mask = result["county"].isnull()
        count = null_mask.sum()

        if count == 0:
            log.info("No null county values to impute")
            return result

        start_size = len(self._geocode_cache)
        log.info(f"Imputing {count} null county values (cache: {start_size:,} entries) ...")
        for idx in result[null_mask].index:
            lat, lon = result.at[idx, "lat0"], result.at[idx, "lon0"]
            county = _pick_address_field(self._resolve_address(lat, lon), COUNTY_KEYS)
            result.at[idx, "county"] = county
            log.info(f"  county imputed: idx={idx} ({lat}, {lon}) → {county!r}")

        log.info(f"county imputation: {len(self._geocode_cache) - start_size:,} new cache entries")
        self._save_geocode_cache()
        return result

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, df: pd.DataFrame, filename: str) -> Path:
        """Write a DataFrame to CSV in the processed directory.

        Args:
            df:       DataFrame to save.
            filename: Output filename (e.g. 'events.csv').

        Returns:
            Path to the written file.
        """
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.processed_dir / filename
        df.to_csv(out_path, index=False)
        log.info(f"Saved {len(df):,} rows to {out_path}")
        return out_path

    def __repr__(self) -> str:
        return f"COWCleaner(processed={self.processed_dir})"


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _season_label(t: pd.Timestamp) -> str:
    """Map a UTC timestamp to its YYYY-Season label.

    Compares on (month, day) tuples to avoid constructing boundary Timestamps
    (no Feb-29 construction risk, no timezone drift). Half-open boundaries:
    a timestamp on a boundary midnight belongs to the window that boundary
    opens. See SEASON_BOUNDS and derive_season for the windowing scheme.

    Args:
        t: A UTC-aware pandas Timestamp.

    Returns:
        Label of the form "YYYY-Season" (e.g. "2025-Winter"), or pd.NA if t
        is null.
    """
    if pd.isna(t):
        return pd.NA
    md = (t.month, t.day)
    for start, end, name in SEASON_BOUNDS:
        if start <= md < end:
            return f"{t.year}-{name}"
    # Winter: md >= Nov 27 (label year = t.year) or md < Feb 27 (label year - 1).
    year = t.year if md >= (11, 27) else t.year - 1
    return f"{year}-Winter"


# Decimal places used to round (lat, lon) into a cache key. Five places is
# about 1 meter, well finer than a storm-report location, and collapses
# float-repr jitter so effectively-identical points hit the same cache entry.
GEOCODE_KEY_PRECISION = 5


def _geocode_key(lat: float, lon: float) -> str:
    """Stable cache key for a coordinate, rounded to GEOCODE_KEY_PRECISION."""
    return f"{round(float(lat), GEOCODE_KEY_PRECISION)},{round(float(lon), GEOCODE_KEY_PRECISION)}"


def _fetch_address(lat: float, lon: float) -> dict | None:
    """Query Nominatim and return the address dict for a coordinate.

    Returns the full `address` object so a single lookup serves both city and
    county resolution. Returns an empty dict when the point resolves to no
    address, and None on a network/parse failure so the caller can distinguish
    "no address here" (safe to cache) from "fetch failed" (do not cache).

    Args:
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.

    Returns:
        Address dict, empty dict, or None on failure.
    """
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "msds692-research"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return data.get("address", {})
    except Exception:
        return None


def _pick_address_field(addr: dict, keys: tuple) -> str:
    """First non-empty value among `keys` in an address dict, else not_provided."""
    for key in keys:
        if addr.get(key):
            return addr[key]
    return "not_provided"
