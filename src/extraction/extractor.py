# NWS Staffing Analysis - COW Data Extractor
# Developed with assistance from Claude Code (Anthropic)
#
# Reads raw COW JSON files collected by COWCollector and extracts two
# tables representing the direct, uncleaned content of the source data:
#
#   events       - one row per warning event issued by a WFO
#   stormreports - one row per Local Storm Report (LSR) linked to the
#                  events table via the 'events' foreign key column
#
# Geometry fields are excluded; the analysis is statistical, not spatial.
# Output is written as CSV to data/02_extraction/, an immutable checkpoint
# of the flattened source data before any cleaning decisions are applied.

import json
import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)


class COWExtractor:
    """Extracts events and stormreports tables from raw COW JSON files.

    Reads every {WFO}_{YEAR}.json file in the raw data directory, flattens
    the GeoJSON feature properties into rows, and adds wfo and year columns
    derived from the filename. Geometry is dropped because the analysis is
    statistical, not spatial.

    Output is written to the extracted directory, which serves as an
    immutable checkpoint before cleaning. Cleaning decisions are applied
    separately in 03_cleaning.ipynb and written to data/03_cleaning/.
    """

    def __init__(self, raw_dir: Path, extracted_dir: Path):
        """
        Args:
            raw_dir:       Directory containing raw {WFO}_{YEAR}.json files.
            extracted_dir: Directory where extracted CSV files will be written.
                           Serves as an immutable checkpoint before cleaning.
        """
        self.raw_dir = Path(raw_dir)
        self.extracted_dir = Path(extracted_dir)

    def extract_events(self) -> pd.DataFrame:
        """Extract warning events from all raw JSON files.

        Each row represents one warning event issued by a WFO. Properties
        are taken directly from the GeoJSON feature properties; geometry
        is excluded. The wfo and year columns are added from the filename.

        Returns:
            DataFrame with one row per warning event across all WFO-years.
        """
        frames = []

        for path in sorted(self.raw_dir.glob("*_*.json")):
            wfo, year_str = path.stem.rsplit("_", 1)
            year = int(year_str)
            log.info(f"Extracting events from {path.name} ...")

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            features = data["events"]["features"]
            if not features:
                log.warning(f"{path.name}: no events found, skipping")
                continue

            rows = [feat["properties"] for feat in features]
            df = pd.DataFrame(rows)
            # Drop API-supplied wfo/year and use filename-derived values as
            # the authoritative source to ensure consistency across all files.
            df.drop(columns=["wfo", "year"], errors="ignore", inplace=True)
            df.insert(0, "wfo", wfo)
            df.insert(1, "year", year)
            frames.append(df)

        if not frames:
            log.warning("No event data found in raw directory.")
            return pd.DataFrame()

        events = pd.concat(frames, ignore_index=True)
        log.info(f"Extracted {len(events):,} events from {len(frames)} files.")
        return events

    def extract_stormreports(self) -> pd.DataFrame:
        """Extract Local Storm Reports (LSRs) from all raw JSON files.

        Each row represents one storm report. The 'warned' column indicates
        whether a warning was in effect at the time of the report; 'events'
        is a foreign key linking warned reports back to the events table.
        Unwarned reports have a null 'events' value. Geometry is excluded.

        Returns:
            DataFrame with one row per storm report across all WFO-years.
        """
        frames = []

        for path in sorted(self.raw_dir.glob("*_*.json")):
            wfo, year_str = path.stem.rsplit("_", 1)
            year = int(year_str)
            log.info(f"Extracting stormreports from {path.name} ...")

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            features = data["stormreports"]["features"]
            if not features:
                log.warning(f"{path.name}: no stormreports found, skipping")
                continue

            rows = [feat["properties"] for feat in features]
            df = pd.DataFrame(rows)
            # Drop API-supplied wfo/year and use filename-derived values as
            # the authoritative source to ensure consistency across all files.
            df.drop(columns=["wfo", "year"], errors="ignore", inplace=True)
            df.insert(0, "wfo", wfo)
            df.insert(1, "year", year)
            frames.append(df)

        if not frames:
            log.warning("No stormreport data found in raw directory.")
            return pd.DataFrame()

        stormreports = pd.concat(frames, ignore_index=True)
        log.info(f"Extracted {len(stormreports):,} stormreports from {len(frames)} files.")
        return stormreports

    def save(self, df: pd.DataFrame, filename: str) -> Path:
        """Write a DataFrame to CSV in the extracted directory.

        Args:
            df:       DataFrame to save.
            filename: Output filename (e.g. 'events.csv').

        Returns:
            Path to the written file.
        """
        self.extracted_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.extracted_dir / filename
        df.to_csv(out_path, index=False)
        log.info(f"Saved {len(df):,} rows to {out_path}")
        return out_path

    def __repr__(self) -> str:
        return (
            f"COWExtractor("
            f"raw={self.raw_dir}, "
            f"extracted={self.extracted_dir})"
        )
