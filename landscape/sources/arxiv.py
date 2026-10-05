"""arXiv adapter — queries the public arXiv Atom API and filters by date.

API: ``http://export.arxiv.org/api/query``. Results are sorted by submission
date (descending) and filtered to the date window client-side, paginating until
results fall before ``since`` (the API's native date filtering is unreliable).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ..idutil import make_bibtex, normalize_arxiv_id, normalize_doi
from ..models import DateWindow, RawHit, Record
from .base import SourceAdapter, SourceError

_API = "http://export.arxiv.org/api/query"
_ATOM = "{http://www.w3.org/2005/Atom}"
_ARXIV_NS = "{http://arxiv.org/schemas/atom}"


class ArxivAdapter(SourceAdapter):
    name = "arxiv"

    def search(self, query: str, date_window: DateWindow) -> list[RawHit]:
        hits: list[RawHit] = []
        page_size = min(100, self.max_results)
        start = 0
        since = date_window.since_date
        while len(hits) < self.max_results:
            params = {
                "search_query": query,
                "start": start,
                "max_results": page_size,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
            try:
                resp = self.client.get(_API, params=params)
            except RuntimeError as exc:
                raise SourceError(f"arXiv search failed: {exc}") from exc
            if resp.status_code != 200:
                raise SourceError(f"arXiv returned status {resp.status_code}")

            try:
                root = ET.fromstring(resp.text)
            except ET.ParseError as exc:
                raise SourceError(f"arXiv returned unparseable XML: {exc}") from exc

            entries = root.findall(f"{_ATOM}entry")
            if not entries:
                break

            stop = False
            for entry in entries:
                published = _text(entry.find(f"{_ATOM}published"))
                if not date_window.contains(published):
                    # descending order -> once we pass below `since` we can stop
                    if since is not None:
                        stop = True
                    continue
                hits.append(RawHit(source=self.name, raw=_entry_to_dict(entry), query=query))
                if len(hits) >= self.max_results:
                    break

            if stop or len(entries) < page_size:
                break
            start += page_size
        return hits

    def normalize(self, hit: RawHit) -> Record:
        r = hit.raw
        arxiv_id = normalize_arxiv_id(r.get("id"))
        doi = normalize_doi(r.get("doi"))
        published = r.get("published", "")
        year = _year_from(published)
        authors = r.get("authors", [])
        primary_cat = r.get("primary_category")
        venue = f"arXiv ({primary_cat})" if primary_cat else "arXiv"
        url = r.get("id", "")
        pdf_url = r.get("pdf_url", "")
        bibtex = make_bibtex(
            entry_type="misc",
            authors=authors,
            year=year,
            title=r.get("title", ""),
            venue_or_repo=venue,
            doi=doi,
            url=url,
            arxiv_id=arxiv_id,
        )
        return Record(
            source=self.name,
            source_native_id=arxiv_id or url,
            title=r.get("title", ""),
            authors=authors,
            year=year,
            venue_or_repo=venue,
            abstract=r.get("summary", ""),
            url=url,
            doi=doi,
            arxiv_id=arxiv_id,
            bibtex=bibtex,
            pdf_available=bool(pdf_url),
            pdf_url=pdf_url or None,
        )


def _entry_to_dict(entry: ET.Element) -> dict:
    authors = [
        _text(a.find(f"{_ATOM}name"))
        for a in entry.findall(f"{_ATOM}author")
        if _text(a.find(f"{_ATOM}name"))
    ]
    pdf_url = ""
    for link in entry.findall(f"{_ATOM}link"):
        if link.get("title") == "pdf" or link.get("type") == "application/pdf":
            pdf_url = link.get("href", "")
            break
    primary = entry.find(f"{_ARXIV_NS}primary_category")
    return {
        "id": _text(entry.find(f"{_ATOM}id")),
        "title": _clean(_text(entry.find(f"{_ATOM}title"))),
        "summary": _clean(_text(entry.find(f"{_ATOM}summary"))),
        "published": _text(entry.find(f"{_ATOM}published")),
        "updated": _text(entry.find(f"{_ATOM}updated")),
        "authors": authors,
        "doi": _text(entry.find(f"{_ARXIV_NS}doi")),
        "primary_category": primary.get("term") if primary is not None else None,
        "pdf_url": pdf_url,
    }


def _text(el) -> str:
    return el.text.strip() if el is not None and el.text else ""


def _clean(s: str) -> str:
    return " ".join(s.split())


def _year_from(published: str):
    if published and len(published) >= 4 and published[:4].isdigit():
        return int(published[:4])
    return None
