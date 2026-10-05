"""OpenAlex adapter — searches works via the OpenAlex REST API.

OpenAlex returns abstracts as an inverted index; we reconstruct plain text.
Open-access PDF URLs (when present) are surfaced for download. Passing
``mailto`` (via the shared client) opts into the faster "polite pool".
"""

from __future__ import annotations

from ..idutil import make_bibtex, normalize_arxiv_id, normalize_doi
from ..models import DateWindow, RawHit, Record
from .base import SourceAdapter, SourceError

_API = "https://api.openalex.org/works"


class OpenAlexAdapter(SourceAdapter):
    name = "openalex"

    def search(self, query: str, date_window: DateWindow) -> list[RawHit]:
        filters = []
        since, until = date_window.since_date, date_window.until_date
        if since:
            filters.append(f"from_publication_date:{since.isoformat()}")
        if until:
            filters.append(f"to_publication_date:{until.isoformat()}")

        hits: list[RawHit] = []
        per_page = min(200, self.max_results)
        cursor = "*"
        while len(hits) < self.max_results:
            params = {
                "search": query,
                "per_page": per_page,
                "cursor": cursor,
            }
            if filters:
                params["filter"] = ",".join(filters)
            try:
                resp = self.client.get(_API, params=params)
            except RuntimeError as exc:
                raise SourceError(f"OpenAlex search failed: {exc}") from exc
            if resp.status_code != 200:
                raise SourceError(f"OpenAlex returned status {resp.status_code}")

            payload = resp.json()
            results = payload.get("results", [])
            if not results:
                break
            for work in results:
                hits.append(RawHit(source=self.name, raw=work, query=query))
                if len(hits) >= self.max_results:
                    break
            cursor = (payload.get("meta") or {}).get("next_cursor")
            if not cursor:
                break
        return hits

    def normalize(self, hit: RawHit) -> Record:
        r = hit.raw
        doi = normalize_doi(r.get("doi"))
        title = r.get("title") or r.get("display_name") or ""
        year = r.get("publication_year")
        authors = [
            (a.get("author") or {}).get("display_name", "")
            for a in r.get("authorships", [])
            if (a.get("author") or {}).get("display_name")
        ]
        venue = _venue(r)
        abstract = _reconstruct_abstract(r.get("abstract_inverted_index"))
        arxiv_id = _arxiv_from_locations(r)
        url = (r.get("doi") or r.get("id") or "")
        pdf_url, is_oa = _best_pdf(r)
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
            source_native_id=r.get("id", ""),
            title=title,
            authors=authors,
            year=year,
            venue_or_repo=venue,
            abstract=abstract,
            url=url,
            doi=doi,
            arxiv_id=arxiv_id,
            bibtex=bibtex,
            pdf_available=bool(pdf_url),
            pdf_url=pdf_url or None,
        )


def _venue(work: dict) -> str:
    loc = work.get("primary_location") or {}
    src = loc.get("source") or {}
    return src.get("display_name") or work.get("type") or "OpenAlex"


def _best_pdf(work: dict):
    for key in ("best_oa_location", "primary_location"):
        loc = work.get(key) or {}
        pdf = loc.get("pdf_url")
        if pdf:
            return pdf, bool(loc.get("is_oa"))
    oa = work.get("open_access") or {}
    if oa.get("oa_url") and oa.get("oa_url", "").lower().endswith(".pdf"):
        return oa["oa_url"], bool(oa.get("is_oa"))
    return "", bool(oa.get("is_oa"))


def _arxiv_from_locations(work: dict):
    for loc in work.get("locations", []) or []:
        src = loc.get("source") or {}
        name = (src.get("display_name") or "").lower()
        landing = loc.get("landing_page_url") or ""
        if "arxiv" in name or "arxiv.org" in landing.lower():
            ax = normalize_arxiv_id(landing) or normalize_arxiv_id(loc.get("pdf_url") or "")
            if ax:
                return ax
    return None


def _reconstruct_abstract(inverted) -> str:
    """OpenAlex stores abstracts as ``{token: [positions...]}``; invert it."""
    if not inverted or not isinstance(inverted, dict):
        return ""
    positions: list[tuple[int, str]] = []
    for token, idxs in inverted.items():
        for i in idxs:
            positions.append((i, token))
    positions.sort(key=lambda p: p[0])
    return " ".join(tok for _, tok in positions)
