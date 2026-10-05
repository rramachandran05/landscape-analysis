"""Dedup (FR-4): collapse same-artifact records by canonical ID (within and
across sources) and record cross-links (arXiv ↔ DOI ↔ repo) when detectable.

Cross-linking is deliberately conservative — it links only on *shared concrete
identifiers* (arXiv id / DOI / repo), never on fuzzy title matching, so the
result is deterministic and never falsely merges distinct artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Record

# When merging duplicate records of the same artifact, prefer fields from the
# higher-priority source first (paper sources before code).
_SOURCE_PRIORITY = {"arxiv": 0, "openalex": 1, "semanticscholar": 2, "github": 3}


@dataclass
class DedupResult:
    records: list[Record]
    duplicates_collapsed: int  # how many records were merged away within the batch


def merge_duplicates(records: list[Record]) -> DedupResult:
    """Collapse records sharing a canonical ``id`` into one merged record."""
    groups: dict[str, list[Record]] = {}
    order: list[str] = []
    for rec in records:
        if rec.id not in groups:
            groups[rec.id] = []
            order.append(rec.id)
        groups[rec.id].append(rec)

    merged: list[Record] = []
    collapsed = 0
    for cid in order:
        group = groups[cid]
        if len(group) == 1:
            merged.append(group[0])
            continue
        collapsed += len(group) - 1
        merged.append(_merge_group(group))
    return DedupResult(records=merged, duplicates_collapsed=collapsed)


def _merge_group(group: list[Record]) -> Record:
    ordered = sorted(group, key=lambda r: _SOURCE_PRIORITY.get(r.source, 99))
    base = ordered[0]
    for other in ordered[1:]:
        _fill_blanks(base, other)
    # Union of the queries that surfaced this artifact, for traceability.
    queries = [r.query_that_found_it for r in ordered if r.query_that_found_it]
    if queries:
        base.query_that_found_it = " | ".join(dict.fromkeys(queries))
    return base


def _fill_blanks(base: Record, other: Record) -> None:
    for f in ("title", "abstract", "venue_or_repo", "url", "doi", "arxiv_id", "bibtex"):
        if not getattr(base, f) and getattr(other, f):
            setattr(base, f, getattr(other, f))
    if not base.authors and other.authors:
        base.authors = other.authors
    if base.year is None and other.year is not None:
        base.year = other.year
    if not base.pdf_available and other.pdf_available:
        base.pdf_available = True
        base.pdf_url = other.pdf_url


def assign_cross_links(
    records: list[Record], existing: list[Record] | None = None
) -> None:
    """Populate ``cross_links`` in place.

    A record is cross-linked to every *other* canonical ID that shares one of
    its concrete identifiers. ``existing`` (prior manifest records) are included
    in the index so new records link to artifacts already collected; reciprocal
    links are added back onto those existing records too (objective field).
    """
    universe = list(records) + list(existing or [])
    index: dict[tuple[str, str], set[str]] = {}
    for rec in universe:
        for key in _identifier_keys(rec):
            index.setdefault(key, set()).add(rec.id)

    for rec in universe:
        linked: set[str] = set()
        for key in _identifier_keys(rec):
            linked |= index.get(key, set())
        linked.discard(rec.id)
        if linked:
            rec.cross_links = sorted(set(rec.cross_links) | linked)


def _identifier_keys(rec: Record) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    if rec.arxiv_id:
        keys.append(("arxiv", rec.arxiv_id.lower()))
    if rec.doi:
        keys.append(("doi", rec.doi.lower()))
    if rec.source == "github" and rec.source_native_id:
        keys.append(("repo", rec.source_native_id.lower()))
    return keys
