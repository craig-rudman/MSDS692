# NWS Staffing Analysis — WFO Registry
# Developed with assistance from Claude Code (Anthropic)
#
# Loads the list of NWS Weather Forecast Offices (WFOs) from a CSV file
# and provides access to office codes and metadata for use by the
# collection pipeline.

import csv
from pathlib import Path


class WFORegistry:
    """Represents the set of NWS Weather Forecast Offices to collect data for.

    Reads from a CSV file with columns: wfo, name, state, region.
    Provides the office codes used as API parameters and the full records
    for metadata enrichment downstream.
    """

    def __init__(self, wfo_file: Path):
        """
        Args:
            wfo_file: Path to the CSV file containing WFO metadata.
        """
        self.wfo_file = Path(wfo_file)
        self._wfos: list[dict] = []
        self._load()

    def _load(self) -> None:
        """Read the CSV file and store all rows that have a wfo value."""
        if not self.wfo_file.exists():
            raise FileNotFoundError(f"WFO file not found: {self.wfo_file}")
        with open(self.wfo_file, newline="", encoding="utf-8") as f:
            self._wfos = [row for row in csv.DictReader(f) if row.get("wfo")]

    @property
    def codes(self) -> list[str]:
        """WFO call sign codes (e.g. 'GLD', 'OUN') used as API query parameters."""
        return [row["wfo"].strip() for row in self._wfos]

    @property
    def records(self) -> list[dict]:
        """Full WFO records including name, state, and region."""
        return self._wfos

    def __len__(self) -> int:
        return len(self._wfos)

    def __repr__(self) -> str:
        return f"WFORegistry({len(self)} offices from {self.wfo_file.name})"
