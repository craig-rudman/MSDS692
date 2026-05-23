# NWS Staffing Analysis - COW API Client
# Developed with assistance from Claude Code (Anthropic)
#
# Handles communication with the IEM Convective Outlook Warning (COW) API.
# The COW API returns warning verification statistics and event-level data
# for a given WFO and time window, including POD, FAR, CSI, lead times,
# warned/unwarned storm reports, and warning polygon geometry.
#
# API documentation: https://mesonet.agron.iastate.edu/api/1/docs#/default/cow_handler_api_1_cow_json_get

import logging
import time

import requests

log = logging.getLogger(__name__)


class COWClient:
    """Fetches COW data from the IEM API for a single WFO and calendar year.

    Handles HTTP session reuse, configurable retries with exponential backoff,
    and phenomena filtering. Supports use as a context manager to ensure the
    underlying session is closed after collection.
    """

    def __init__(
        self,
        phenomena: list[str],
        base_url: str,
        timeout: int = 30,
        retries: int = 3,
        retry_delay: float = 2.0,
    ):
        """
        Args:
            phenomena:   List of VTEC phenomena codes to filter (e.g. ['TO', 'SV', 'FF']).
                         Passed to both the 'phenomena' and 'lsrtype' API parameters so
                         that warnings and storm reports are filtered consistently.
            base_url:    IEM COW API endpoint URL.
            timeout:     HTTP request timeout in seconds.
            retries:     Number of attempts before raising an error.
            retry_delay: Base delay in seconds between retries (multiplied by attempt number).
        """
        self.phenomena = phenomena
        self.base_url = base_url
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self._session = requests.Session()

    def fetch(self, wfo: str, year: int) -> dict:
        """Fetch COW data for one WFO and calendar year.

        Queries the full calendar year (Jan 1 00:00Z to Jan 1 00:00Z of the
        following year) to ensure complete coverage with no boundary overlap.

        Args:
            wfo:  WFO call sign (e.g. 'GLD').
            year: Four-digit calendar year (e.g. 2024).

        Returns:
            Parsed JSON response containing 'params', 'stats', 'events',
            and 'stormreports' keys.

        Raises:
            RuntimeError: If all retry attempts fail.
        """
        # IEM COW API requires repeated params (phenomena=TO&phenomena=SV),
        # not comma-joined strings (phenomena=TO,SV), to filter multiple phenomena.
        params = (
            [("wfo", wfo)]
            + [("phenomena", p) for p in self.phenomena]
            + [("lsrtype", p) for p in self.phenomena]
            + [
                ("begints", f"{year}-01-01T00:00Z"),
                ("endts", f"{year + 1}-01-01T00:00Z"),
            ]
        )

        for attempt in range(1, self.retries + 1):
            try:
                r = self._session.get(self.base_url, params=params, timeout=self.timeout)
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                log.warning(f"{wfo} {year} attempt {attempt}/{self.retries} failed: {e}")
                if attempt < self.retries:
                    time.sleep(self.retry_delay * attempt)

        raise RuntimeError(f"Failed to fetch {wfo} {year} after {self.retries} attempts")

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __repr__(self) -> str:
        return f"COWClient(phenomena={self.phenomena}, url={self.base_url})"
