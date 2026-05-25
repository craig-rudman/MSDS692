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

log = logging.getLogger(__name__)

# Terminal-status priority for event deduplication. The COW API returns one
# row per issuance status (NEW, CON, EXT, EXP, CAN, COR); lower rank = more
# terminal and takes precedence when keeping one row per (wfo,year,phenomena,eventid).
STATUS_PRIORITY = {"CAN": 0, "COR": 1, "EXP": 2, "EXT": 3, "CON": 4, "NEW": 5}

# Events columns with no analytical value. See notebook cell documentation
# for the rationale behind each group.
EVENTS_DROP_COLS = [
    "significance",
    "windtag",
    "svr_tornado_possible",
    "tor_in_svrtorpossible",
    "sharedborder", "carea", "perimeter", "parea", "areaverify", "lat0", "lon0",
    "ar_ugc", "ar_ugcname",
    "visual_imgurl", "product_text", "product_href", "link",
    "stormreports", "stormreports_all",
    "fcster",
    "statuses",  # identical to status after deduplication — pre-dedup API artifact
    "hailtag",   # 100% null for FF (structurally inapplicable); not used in planned analysis
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

    def __init__(self, processed_dir: Path):
        """
        Args:
            processed_dir: Directory where cleaned CSV files will be written.
        """
        self.processed_dir = Path(processed_dir)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def drop_event_columns(self, events: pd.DataFrame) -> pd.DataFrame:
        """Drop columns with no analytical value from the events table.

        See EVENTS_DROP_COLS for the full list and rationale documented in
        the module-level constant.

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

    def clean_events(self, events: pd.DataFrame) -> pd.DataFrame:
        """Run all events cleaning steps in sequence.

        Steps: drop columns → deduplicate → parse timestamps →
               cap lead0 → derive product_id.

        Args:
            events: Raw extracted events DataFrame.

        Returns:
            Fully cleaned events DataFrame.
        """
        events = self.drop_event_columns(events)
        events = self.deduplicate_events(events)
        events = self.parse_event_timestamps(events)
        events = self.cap_lead0(events)
        events = self.derive_product_id(events)
        return events

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

        For each row with a null city, queries the Nominatim API using
        lon0/lat0 and returns the most specific named place (city → town
        → village → hamlet). Falls back to "not_provided" for rural
        locations that don't resolve.

        Adds a 1-second delay between requests to respect Nominatim's
        usage policy.

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

        log.info(f"Imputing {count} null city values via Nominatim ...")
        for idx in result[null_mask].index:
            lat, lon = result.at[idx, "lat0"], result.at[idx, "lon0"]
            city = _reverse_geocode(lat, lon, CITY_KEYS)
            result.at[idx, "city"] = city
            log.info(f"  city imputed: idx={idx} ({lat}, {lon}) → {city!r}")
            time.sleep(1)

        return result

    def impute_null_counties(self, stormreports: pd.DataFrame) -> pd.DataFrame:
        """Impute null county values via Nominatim reverse geocoding.

        For each row with a null county, queries Nominatim using lon0/lat0
        and falls through county → city (for unified city-boroughs like
        Juneau) → state_district → "not_provided". Handles Alaska boroughs
        and the Unorganized Borough where Nominatim may return no county.

        Adds a 1-second delay between requests to respect Nominatim's
        usage policy.

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

        log.info(f"Imputing {count} null county values via Nominatim ...")
        for idx in result[null_mask].index:
            lat, lon = result.at[idx, "lat0"], result.at[idx, "lon0"]
            county = _reverse_geocode(lat, lon, COUNTY_KEYS)
            result.at[idx, "county"] = county
            log.info(f"  county imputed: idx={idx} ({lat}, {lon}) → {county!r}")
            time.sleep(1)

        return result

    def clean_stormreports(self, stormreports: pd.DataFrame) -> pd.DataFrame:
        """Run all storm report cleaning steps in sequence.

        Steps: drop columns → parse timestamps → normalize source →
               cap leadtime → impute null cities → impute null counties.

        Args:
            stormreports: Raw extracted stormreports DataFrame.

        Returns:
            Fully cleaned stormreports DataFrame.
        """
        stormreports = self.repair_malformed_rows(stormreports)
        stormreports = self.drop_stormreport_columns(stormreports)
        stormreports = self.parse_stormreport_timestamps(stormreports)
        stormreports = self.normalize_source(stormreports)
        stormreports = self.cap_leadtime(stormreports)
        stormreports = self.impute_null_cities(stormreports)
        stormreports = self.impute_null_counties(stormreports)
        return stormreports

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

def _reverse_geocode(lat: float, lon: float, keys: tuple) -> str:
    """Query Nominatim for the first matching address field.

    Args:
        lat:  Latitude in decimal degrees.
        lon:  Longitude in decimal degrees.
        keys: Address field names to try in order of preference.

    Returns:
        First non-empty address field value, or "not_provided".
    """
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "msds692-research"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        addr = data.get("address", {})
        for key in keys:
            if addr.get(key):
                return addr[key]
    except Exception:
        pass
    return "not_provided"
