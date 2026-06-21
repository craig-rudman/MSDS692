# NWS Staffing Analysis - Data Loading and Filtering
# Developed with assistance from Claude Code (Anthropic)
#
# Canonical data loading, CONUS filtering, and top-quartile WFO selection.
# All notebooks should import from here rather than re-deriving these operations.

import glob
import json
import urllib.request
from pathlib import Path

import pandas as pd

# US Census 2022 cartographic state boundaries (20m), used only for map outlines.
_STATES_URL = "https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_state_20m.zip"

# US Census 2023 ZCTA (ZIP) gazetteer, used for ZIP-centroid fallback when an
# office street address does not resolve at street level.
_ZCTA_URL = ("https://www2.census.gov/geo/docs/maps-data/data/gazetteer/"
             "2023_Gazetteer/2023_Gaz_zcta_national.zip")

# COW event-matching parameters that must be constant across all years for the
# detection comparison to be valid; a change here can masquerade as a real change.
MATCHING_PARAMS = ["lsrbuffer", "wind", "hailsize", "warningbuffer"]


def collect_matching_params(raw_dir: Path) -> pd.DataFrame:
    """Tabulate the COW event-matching parameters across every raw collection file.

    Reads the `params` block from each `WFO_YEAR.json` and pulls the matching
    tolerances (MATCHING_PARAMS). These must be identical across all ten years, or
    a change in matching rules could be mistaken for a change in detection
    performance. The caller checks for uniqueness; this function only gathers.

    Args:
        raw_dir: Directory of raw COW JSON files (one per WFO and year).

    Returns:
        DataFrame with columns: wfo, year, and one column per MATCHING_PARAMS,
        one row per source file.
    """
    rows = []
    for path in sorted(glob.glob(str(raw_dir / "*.json"))):
        with open(path) as f:
            p = json.load(f)["params"]
        stem = Path(path).stem            # e.g. "ABQ_2016"
        wfo, year = stem.rsplit("_", 1)
        rows.append({"wfo": wfo, "year": int(year),
                     **{k: p.get(k) for k in MATCHING_PARAMS}})
    return pd.DataFrame(rows)


def load_states(geo_dir: Path):
    """Load CONUS state boundaries as a GeoDataFrame, downloading and caching once.

    Fetches the Census cartographic state file to `geo_dir` on first call and reads
    from the cached zip thereafter. Non-CONUS states and territories are dropped so
    the result matches the analysis footprint. Used only to draw reference outlines
    under the storm-report scatter; geopandas is imported lazily so the rest of the
    module has no hard geospatial dependency.

    Args:
        geo_dir: Directory to cache the shapefile zip in (created if absent).

    Returns:
        GeoDataFrame of the 48 contiguous states plus DC, in EPSG:4269.
    """
    import geopandas as gpd

    geo_dir.mkdir(parents=True, exist_ok=True)
    dst = geo_dir / "cb_2022_us_state_20m.zip"
    if not dst.exists():
        urllib.request.urlretrieve(_STATES_URL, dst)
    states = gpd.read_file(f"zip://{dst}")
    drop = {"AK", "HI", "PR", "GU", "AS", "VI", "MP"}
    return states[~states["STUSPS"].isin(drop)]


def _load_zcta_centroids(geo_dir: Path) -> dict:
    """Load Census ZCTA (ZIP) centroids as {zip5: (lat, lon)}, caching once.

    Downloads the Census 2023 ZCTA gazetteer to `geo_dir` on first call and reads
    the cached zip thereafter. Used only as the ZIP-centroid fallback when an
    office street address does not resolve at street level.

    Args:
        geo_dir: Directory to cache the gazetteer zip in (created if absent).

    Returns:
        Dict mapping 5-digit ZIP (GEOID) to (lat, lon) of the ZCTA centroid.
    """
    geo_dir.mkdir(parents=True, exist_ok=True)
    dst = geo_dir / "2023_Gaz_zcta_national.zip"
    if not dst.exists():
        req = urllib.request.Request(_ZCTA_URL, headers={"User-Agent": "msds692-research"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dst.write_bytes(resp.read())
    df = pd.read_csv(dst, sep="\t", dtype={"GEOID": str}, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]   # gazetteer headers carry trailing spaces
    return {z: (lat, lon) for z, lat, lon
            in zip(df["GEOID"], df["INTPTLAT"], df["INTPTLONG"])}


def _geocode_address(addr: dict, zcta: dict) -> tuple[float, float]:
    """Forward-geocode an NWS office postal address to (lat, lon).

    Uses the US Census Bureau one-line-address geocoder (no API key, no rate
    limit, US addresses only) for a street-level match. The few NWS offices at
    airports or weather stations that the Census address file does not carry fall
    back to the ZIP-code (ZCTA) centroid from the gazetteer, an approximate point
    in the right ZIP.

    Args:
        addr: NWS /offices address dict (streetAddress, addressLocality,
            addressRegion, postalCode).
        zcta: ZIP-to-centroid lookup from _load_zcta_centroids.

    Returns:
        (lat, lon) of the office address (street-level or ZIP-centroid fallback).
    """
    from urllib.parse import urlencode

    # streetAddress is sometimes multi-line (a building name above the street);
    # the last non-empty line is the mailing street.
    street_lines = [ln.strip() for ln in addr.get("streetAddress", "").splitlines() if ln.strip()]
    street = street_lines[-1] if street_lines else ""
    city, state = addr.get("addressLocality", ""), addr.get("addressRegion", "")
    zip5 = addr.get("postalCode", "").split("-")[0]

    q = urlencode({"address": f"{street}, {city}, {state} {zip5}",
                   "benchmark": "Public_AR_Current", "format": "json"})
    url = f"https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": "msds692-research"})
    hits = json.loads(urllib.request.urlopen(req, timeout=15).read())["result"]["addressMatches"]
    if hits:
        c = hits[0]["coordinates"]
        return float(c["y"]), float(c["x"])   # y = latitude, x = longitude
    if zip5 in zcta:                           # ZIP-centroid fallback (approximate)
        return zcta[zip5]
    raise ValueError(f"No street match and no ZCTA centroid for office address: {addr}")


def load_wfo_coords(coords_path: Path, geo_dir: Path, wfos) -> pd.DataFrame:
    """Load office (WFO) building coordinates, caching to coords_path.

    Warnings are areas, not points, so the cleaned tables carry no office
    location. For each office this reads the street address from the NWS API
    (https://api.weather.gov/offices/{wfo}) and forward-geocodes it with the US
    Census geocoder to the office building's latitude/longitude. Results cache to
    `coords_path` thereafter, mirroring load_states' cache-or-fetch pattern;
    only offices not already cached are fetched. The geocoded coordinates are a
    tracked input (data/wfo/), so coords_path is kept distinct from geo_dir,
    which holds only the regenerable Census ZIP-centroid fallback.

    Args:
        coords_path: Path to the wfo_coords.csv cache (parent created if absent).
        geo_dir: Directory holding the regenerable ZCTA fallback zip.
        wfos: Iterable of WFO codes to resolve (the in-scope office set).

    Returns:
        DataFrame with columns wfo, lat, lon, one row per requested office.
    """
    coords_path.parent.mkdir(parents=True, exist_ok=True)
    dst = coords_path
    cache = (pd.read_csv(dst) if dst.exists()
             else pd.DataFrame(columns=["wfo", "lat", "lon"]))

    wanted = sorted(set(wfos))
    have = set(cache["wfo"])
    missing = [w for w in wanted if w not in have]

    # ZIP-centroid fallback table, loaded once only when there is work to do.
    zcta = _load_zcta_centroids(geo_dir) if missing else {}

    for wfo in missing:
        url = f"https://api.weather.gov/offices/{wfo}"
        req = urllib.request.Request(url, headers={"User-Agent": "msds692-research"})
        addr = json.load(urllib.request.urlopen(req, timeout=10))["address"]
        lat, lon = _geocode_address(addr, zcta)
        # Persist after each success so a later failure never discards completed
        # work and a re-run resumes from the cache.
        cache = pd.concat([cache, pd.DataFrame([{"wfo": wfo, "lat": lat, "lon": lon}])],
                          ignore_index=True)
        cache.sort_values("wfo").to_csv(dst, index=False)

    return cache[cache["wfo"].isin(wanted)].reset_index(drop=True)


def load_events(clean_dir: Path) -> pd.DataFrame:
    """Load and prepare the cleaned events table.

    Parses issue/expire as UTC datetimes and adds year_month and month
    convenience columns used throughout the analysis notebooks. Also derives
    `false_alarm`, the false-alarm-ratio (FAR) outcome: the integer complement of
    `verify` (1 = the warning did not verify, i.e. it was a false alarm). The FAR
    models fit `false_alarm` directly so the coefficient and odds ratio are on the
    false-alarm scale that the metric is named for; `verify` is left intact for any
    use that wants the verification scale.

    Args:
        clean_dir: Path to the data/03_cleaning/ directory.

    Returns:
        DataFrame with one row per warning event, datetime columns parsed and the
        `false_alarm` outcome added.
    """
    df = pd.read_csv(
        clean_dir / "events.csv",
        parse_dates=["issue", "expire"],
    )
    df["issue"]      = pd.to_datetime(df["issue"],  utc=True)
    df["expire"]     = pd.to_datetime(df["expire"], utc=True)
    # FAR outcome: 1 when the warning did not verify (a false alarm), the complement
    # of verify. Integer 0/1 so the logistic FAR fit consumes it like the other outcomes.
    df["false_alarm"] = (1 - df["verify"]).astype(int)
    # tz-naive before to_period: a monthly period carries no tz, and converting
    # in place avoids pandas' UserWarning about dropping tz information
    df["year_month"] = df["issue"].dt.tz_localize(None).dt.to_period("M")
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
    # tz-naive before to_period: a monthly period carries no tz, and converting
    # in place avoids pandas' UserWarning about dropping tz information
    df["year_month"] = df["valid"].dt.tz_localize(None).dt.to_period("M")
    return df
