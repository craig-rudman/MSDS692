# NWS Staffing Analysis - UGC County Extraction
# Developed with assistance from Claude Code (Anthropic)
#
# Reads raw COW JSON files and writes events_ugc.csv: one row per
# (product_id, ugc) pair, giving the county-level footprint of every
# warning event.  Join to events.csv on product_id.

import json
import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)


def extract_ugc(cow_dir: Path, out_path: Path) -> pd.DataFrame:
    """Extract per-county warning footprints from raw COW JSON files.

    For each warning event, ar_ugc lists the FIPS-style county codes
    (format: {state}{C}{number}, e.g. OKC057) and ar_ugcname lists the
    corresponding human-readable names.  This function fans each event out
    to one row per county.

    Args:
        cow_dir: Path to data/01_collection/COW/ directory.
        out_path: Destination path for the output CSV.

    Returns:
        DataFrame with columns: product_id, wfo, year, phenomena, ugc,
        ugc_name, state_code, county_fips.
    """
    rows = []
    files = sorted(cow_dir.glob("*.json"))
    log.info("Processing %d COW JSON files", len(files))

    for path in files:
        with open(path) as f:
            data = json.load(f)

        for feat in data["events"]["features"]:
            p = feat["properties"]
            wfo       = p["wfo"]
            year      = p["year"]
            phenomena = p["phenomena"]
            eventid   = p["eventid"]
            # Compact key matches events.csv: {year}{wfo}{eventid}{phenomena}W1
            product_id = f"{year}{wfo}{eventid}{phenomena}W1"
            ugc_codes  = p["ar_ugc"]
            ugc_names  = p["ar_ugcname"]

            for ugc, name in zip(ugc_codes, ugc_names):
                # ugc format: {2-letter state}{C}{3-digit number}
                # e.g. OKC057 → state=OK, fips suffix=057
                state_code   = ugc[:2]
                county_fips  = ugc[3:]
                rows.append({
                    "product_id":   product_id,
                    "wfo":          wfo,
                    "year":         year,
                    "phenomena":    phenomena,
                    "ugc":          ugc,
                    "ugc_name":     name,
                    "state_code":   state_code,
                    "county_fips":  county_fips,
                })

    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    log.info("Wrote %d rows to %s", len(df), out_path)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    repo_root = Path(__file__).resolve().parents[2]
    cow_dir   = repo_root / "data" / "01_collection" / "COW"
    out_path  = repo_root / "data" / "03_cleaning" / "events_ugc.csv"
    df = extract_ugc(cow_dir, out_path)
    print(f"events_ugc.csv: {len(df):,} rows  "
          f"({df['product_id'].nunique():,} unique events, "
          f"{df['ugc'].nunique():,} unique counties)")
    print(df.head(10).to_string(index=False))
