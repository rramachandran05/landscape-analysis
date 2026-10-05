"""Semantic Scholar adapter (optional) — Graph API paper search.

Optional per the spec; S2 has tight unauthenticated rate limits. An
``S2_API_KEY`` env var (read by the pipeline) raises them. Not in
``DEFAULT_SOURCES`` — opt in with ``--sources ...,semanticscholar``.
"""

from __future__ import annotations

import os

from ..idutil import make_bibtex, normalize_arxiv_id, normalize_doi
from ..models import DateWindow, RawHit, Record
from .base import SourceAdapter, SourceError

_API = "https://api.semanticscholar.org/graph/v1/paper/search"
_FIELDS = (
    "title,abstract,year,authors,venue,externalIds,url,"
    "openAccessPdf,publicationDate"
)


class SemanticScholarAdapter(SourceAdapter):
    name = "semanticscholar"

    def _headers(self) -> dict:
        key = os.environ.get("S2_API_KEY")
        return {"x-api-key": key} if key else {}

    def search(self, query: str, date_window: DateWindow) -> list[RawHit]:
        hits: list[RawHit] = []
        limit = min(100, self.max_results)
        offset = 0
        while len(hits) < self.max_results:
            params = {"query": query, "fields": _FIELDS, "limit": limit, "offset": offset}
            since, until = date_window.since_date, date_window.until_date
            if since or until:
                lo = since.isoformat() if since else ""
                hi = until.isoformat() if until else ""
                params["publicationDateOrYear"] = f"{lo}:{hi}"
            try:
                resp = self.client.get(_API, params=params)
            except RuntimeError as exc:
                raise SourceError(f"Semantic Scholar search failed: {exc}") from exc
            if resp.status_code == 429:
                raise SourceError("Semantic Scholar rate limit hit (set S2_API_KEY)")
            if resp.status_code != 200:
                raise SourceError(f"Semantic Scholar returned status {resp.status_code}")

            payload = resp.json()
            data = payload.get("data", [])
            if not data:
                break
            for paper in data:
                hits.append(RawHit(source=self.name, raw=paper, query=query))
                if len(hits) >= self.max_results:
                    break
            nxt = payload.get("next")
            if nxt is None:
                break
            offset = nxt
        return hits

    def normalize(self, hit: RawHit) -> Record:
        r = hit.raw
        ext = r.get("externalIds") or {}
        doi = normalize_doi(ext.get("DOI"))
        arxiv_id = normalize_arxiv_id(ext.get("ArXiv"))
        title = r.get("title") or ""
        year = r.get("year")
        authors = [a.get("name", "") for a in r.get("authors", []) if a.get("name")]
        venue = r.get("venue") or "Semantic Scholar"
        url = r.get("url", "")
        pdf = (r.get("openAccessPdf") or {}).get("url", "")
        bibtex = make_bibtex(
            entry_type="article",
            authors=authors,
            year=year,
            title=title,
            venue_or_repo=venue,
            doi=doi,
            url=url,
            arxiv_id=arxiv_id,
        )
        return Record(
            source=self.name,
            source_native_id=r.get("paperId", ""),
            title=title,
            authors=authors,
            year=year,
            venue_or_repo=venue,
            abstract=r.get("abstract") or "",
            url=url,
            doi=doi,
            arxiv_id=arxiv_id,
            bibtex=bibtex,
            pdf_available=bool(pdf),
            pdf_url=pdf or None,
        )
