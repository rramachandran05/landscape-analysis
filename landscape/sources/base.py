"""Base class + shared contract for source adapters."""

from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING

from ..models import DateWindow, RawHit, Record

if TYPE_CHECKING:
    from ..http import HttpClient


class SourceError(Exception):
    """Raised on an unrecoverable source outage. The pipeline catches this,
    records a partial run, and continues with other sources (§4a failure
    handling)."""


class SourceAdapter(abc.ABC):
    """One adapter per structured source.

    Subclasses implement :meth:`search` (query -> raw hits) and
    :meth:`normalize` (raw hit -> common :class:`Record`). The pipeline does the
    canonical-ID assignment, dedup, download, and persistence — adapters only
    talk to their source and map fields.
    """

    #: CLI / manifest name for this source.
    name: str = "base"

    def __init__(self, client: "HttpClient", max_results: int = 200):
        self.client = client
        self.max_results = max_results
        self.log = logging.getLogger(f"landscape.sources.{self.name}")

    @abc.abstractmethod
    def search(self, query: str, date_window: DateWindow) -> list[RawHit]:
        """Return raw hits for ``query`` within ``date_window``."""

    @abc.abstractmethod
    def normalize(self, hit: RawHit) -> Record:
        """Map a raw hit to a common :class:`Record` (objective fields only)."""

    def collect(self, query: str, date_window: DateWindow) -> list[Record]:
        """Convenience: search then normalize, skipping malformed records
        (FR: malformed record -> skip + log, don't abort)."""
        records: list[Record] = []
        for hit in self.search(query, date_window):
            try:
                rec = self.normalize(hit)
            except Exception as exc:  # noqa: BLE001 - defensive per spec
                self.log.warning("skipping malformed %s record: %s", self.name, exc)
                continue
            if not rec.title and not rec.url:
                self.log.warning("skipping empty %s record", self.name)
                continue
            rec.query_that_found_it = query
            records.append(rec)
        return records
