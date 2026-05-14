# NWS Staffing Analysis — COW Data Collector
# Developed with assistance from Claude Code (Anthropic)
#
# Orchestrates the full data collection run: iterates all WFOs across all
# years, delegates API calls to COWClient, and writes one JSON file per
# WFO-year to the output directory. Already-collected files are skipped so
# the collection can be safely interrupted and resumed.

import json
import logging
import time
from pathlib import Path

from .cow import COWClient
from .wfo import WFORegistry

log = logging.getLogger(__name__)


class COWCollector:
    """Orchestrates collection of COW data for all WFOs across a range of years.

    Iterates every WFO-year combination, skips files already on disk,
    and writes one JSON file per WFO-year to the output directory.
    Output files are named {WFO}_{YEAR}.json (e.g. GLD_2024.json).
    """

    def __init__(
        self,
        registry: WFORegistry,
        client: COWClient,
        output_dir: Path,
        years: list[int],
        rate_limit: float = 0.3,
    ):
        """
        Args:
            registry:   WFORegistry providing the list of offices to collect.
            client:     COWClient used to fetch data from the API.
            output_dir: Directory where JSON files will be written.
            years:      List of calendar years to collect. Caller is responsible
                        for defining the analysis window (e.g. 2020–2025).
            rate_limit: Seconds to pause between API requests to avoid
                        overwhelming the IEM server.
        """
        self.registry = registry
        self.client = client
        self.output_dir = Path(output_dir)
        self.years = years
        self.rate_limit = rate_limit

    def collect(self) -> dict:
        """Run the full collection loop over all WFOs and years.

        Skips any WFO-year file that already exists on disk, making this
        safe to re-run after interruptions without duplicate requests.

        Returns:
            Summary dict with keys 'wrote', 'skipped', and 'failed'.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        wrote = skipped = failed = 0

        for wfo in self.registry.codes:
            for year in self.years:
                out_path = self.output_dir / f"{wfo}_{year}.json"

                if out_path.exists():
                    skipped += 1
                    continue

                log.info(f"Fetching {wfo} {year} ...")
                try:
                    data = self.client.fetch(wfo, year)
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                    wrote += 1
                    log.info(f"Wrote {out_path.name}")
                except Exception as e:
                    log.error(f"Failed {wfo} {year}: {e}")
                    failed += 1

                time.sleep(self.rate_limit)

        summary = {"wrote": wrote, "skipped": skipped, "failed": failed}
        log.info(f"Collection complete — {summary}")
        return summary

    def __repr__(self) -> str:
        return (
            f"COWCollector("
            f"{len(self.registry)} WFOs, "
            f"years={self.years[0]}-{self.years[-1]}, "
            f"output={self.output_dir})"
        )
