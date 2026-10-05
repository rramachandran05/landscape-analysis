"""Frozen schema — the contract between tool (Phase A) and agent (Phase B).

Field ownership is part of the contract:

* **Tool-owned (objective)** fields are written by this package.
* **Agent-owned (judgment)** fields are written only by the agent layer.

Update mode must never let the tool touch agent-owned fields. The two field
sets below are the single source of truth for that guard (see
``landscape.manifest``).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


MANIFEST_VERSION = "1.0"

# Allowed values for the agent-owned ``status`` field. The tool only ever sets
# ``raw``; ``curated`` / ``dropped`` are agent decisions.
STATUS_RAW = "raw"
STATUS_CURATED = "curated"
STATUS_DROPPED = "dropped"
VALID_STATUSES = (STATUS_RAW, STATUS_CURATED, STATUS_DROPPED)

# --- Field ownership (the keystone split) --------------------------------- #
TOOL_OWNED_FIELDS = (
    "id",
    "source",
    "source_native_id",
    "title",
    "authors",
    "year",
    "venue_or_repo",
    "abstract",
    "url",
    "doi",
    "arxiv_id",
    "retrieved_on",
    "run_id_first_seen",
    "query_that_found_it",
    "bibtex",
    "pdf_available",
    "local_path",
    "cross_links",
)

AGENT_OWNED_FIELDS = (
    "status",
    "relevance_score",
    "relevance_rationale",
    "dimensions",
    "cluster_id",
)

# Carried in-memory only (adapter -> pipeline); never written to the manifest.
TRANSIENT_FIELDS = ("pdf_url",)


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp (seconds precision, ``Z`` suffix)."""
    return (
        _dt.datetime.now(_dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


@dataclass
class DateWindow:
    """A half-open-ish publication date window, bound by month/day strings.

    ``since`` / ``until`` accept ``YYYY``, ``YYYY-MM`` or ``YYYY-MM-DD``.
    Either bound may be ``None`` (unbounded).
    """

    since: Optional[str] = None
    until: Optional[str] = None

    @property
    def since_date(self) -> Optional[_dt.date]:
        return _parse_date_bound(self.since, end=False) if self.since else None

    @property
    def until_date(self) -> Optional[_dt.date]:
        return _parse_date_bound(self.until, end=True) if self.until else None

    def contains(self, value: Any) -> bool:
        """True if ``value`` (a date / datetime / ISO string / year int) falls
        inside the window. Unparseable values are treated as inside (the tool
        does not silently drop records it cannot date)."""
        d = _coerce_date(value)
        if d is None:
            return True
        lo, hi = self.since_date, self.until_date
        if lo is not None and d < lo:
            return False
        if hi is not None and d > hi:
            return False
        return True

    def to_dict(self) -> dict:
        return {"since": self.since, "until": self.until}


def _parse_date_bound(s: str, end: bool) -> _dt.date:
    """Parse a partial date string into a concrete bound.

    ``end=False`` snaps to the earliest matching day, ``end=True`` to the
    latest (e.g. ``"2023-02"`` -> ``2023-02-01`` or ``2023-02-28``).
    """
    s = s.strip()
    parts = s.split("-")
    year = int(parts[0])
    if len(parts) == 1:
        return _dt.date(year, 12, 31) if end else _dt.date(year, 1, 1)
    month = int(parts[1])
    if len(parts) == 2:
        if end:
            return _last_day_of_month(year, month)
        return _dt.date(year, month, 1)
    day = int(parts[2])
    return _dt.date(year, month, day)


def _last_day_of_month(year: int, month: int) -> _dt.date:
    if month == 12:
        nxt = _dt.date(year + 1, 1, 1)
    else:
        nxt = _dt.date(year, month + 1, 1)
    return nxt - _dt.timedelta(days=1)


def _coerce_date(value: Any) -> Optional[_dt.date]:
    if value is None:
        return None
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    if isinstance(value, int):
        # bare year
        try:
            return _dt.date(value, 1, 1)
        except ValueError:
            return None
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return None
        # ISO-ish; tolerate trailing Z and time component
        v = v.replace("Z", "").strip()
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                return _dt.datetime.strptime(v[: len(fmt) + 6], fmt).date()
            except ValueError:
                continue
        # last resort: leading 4 digits as year
        if len(v) >= 4 and v[:4].isdigit():
            try:
                return _dt.date(int(v[:4]), 1, 1)
            except ValueError:
                return None
    return None


@dataclass
class RawHit:
    """A single raw result from a source adapter's ``search`` call.

    ``raw`` holds the source-native payload (dict). ``source`` names the adapter
    and ``query`` records the exact query string that produced the hit (so the
    normalized record can be stamped with ``query_that_found_it``).
    """

    source: str
    raw: dict
    query: str = ""


@dataclass
class Record:
    """A normalized resource record. Mirrors the manifest ``resources[]`` schema.

    Tool-owned fields are populated by adapters / the pipeline. Agent-owned
    fields carry inert defaults here (``status='raw'``) and are owned by the
    agent thereafter.
    """

    # --- tool-owned (objective) --- #
    id: str = ""
    source: str = ""
    source_native_id: str = ""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    venue_or_repo: str = ""
    abstract: str = ""
    url: str = ""
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    retrieved_on: str = ""
    run_id_first_seen: str = ""
    query_that_found_it: str = ""
    bibtex: str = ""
    pdf_available: bool = False
    local_path: Optional[str] = None
    cross_links: list[str] = field(default_factory=list)

    # --- agent-owned (judgment) — inert defaults, never edited by the tool --- #
    status: str = STATUS_RAW
    relevance_score: Optional[float] = None
    relevance_rationale: Optional[str] = None
    dimensions: dict[str, Any] = field(default_factory=dict)
    cluster_id: Optional[str] = None

    # --- transient (not persisted) — adapter -> pipeline download hint --- #
    pdf_url: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        for transient in TRANSIENT_FIELDS:
            d.pop(transient, None)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Record":
        known = {k: v for k, v in d.items() if k in cls.__dataclass_fields__}
        return cls(**known)
