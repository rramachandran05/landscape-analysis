"""GitHub adapter — searches repositories via the REST Search API.

Repos have no PDF, so ``pdf_available`` is always False. An optional
``GITHUB_TOKEN`` env var (read by the pipeline and passed through the client
headers) raises the rate limit; without it the API allows ~10 search req/min.
"""

from __future__ import annotations

import os

from ..idutil import make_bibtex, normalize_repo
from ..models import DateWindow, RawHit, Record
from .base import SourceAdapter, SourceError

_API = "https://api.github.com/search/repositories"


class GitHubAdapter(SourceAdapter):
    name = "github"

    def _headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def search(self, query: str, date_window: DateWindow) -> list[RawHit]:
        # Encode the date window as a GitHub `created:` qualifier so the API
        # does the filtering (created date is the natural "when did this land").
        q = query
        since, until = date_window.since_date, date_window.until_date
        if since and until:
            q += f" created:{since.isoformat()}..{until.isoformat()}"
        elif since:
            q += f" created:>={since.isoformat()}"
        elif until:
            q += f" created:<={until.isoformat()}"

        hits: list[RawHit] = []
        per_page = min(100, self.max_results)
        page = 1
        while len(hits) < self.max_results:
            params = {
                "q": q,
                "sort": "stars",
                "order": "desc",
                "per_page": per_page,
                "page": page,
            }
            try:
                resp = self.client.get(_API, params=params, headers=self._headers())
            except RuntimeError as exc:
                raise SourceError(f"GitHub search failed: {exc}") from exc
            if resp.status_code == 403:
                raise SourceError(
                    "GitHub rate limit hit (set GITHUB_TOKEN to raise it)"
                )
            if resp.status_code != 200:
                raise SourceError(f"GitHub returned status {resp.status_code}")

            items = resp.json().get("items", [])
            if not items:
                break
            for item in items:
                hits.append(RawHit(source=self.name, raw=item, query=query))
                if len(hits) >= self.max_results:
                    break
            if len(items) < per_page:
                break
            page += 1
        return hits

    def normalize(self, hit: RawHit) -> Record:
        r = hit.raw
        full_name = r.get("full_name", "")
        repo = normalize_repo(full_name)
        owner = (r.get("owner") or {}).get("login", "")
        created = r.get("created_at", "")
        year = int(created[:4]) if created[:4].isdigit() else None
        url = r.get("html_url", "")
        bibtex = make_bibtex(
            entry_type="misc",
            authors=[owner] if owner else [],
            year=year,
            title=full_name,
            venue_or_repo="GitHub",
            url=url,
        )
        return Record(
            source=self.name,
            source_native_id=full_name or str(r.get("id", "")),
            title=full_name,
            authors=[owner] if owner else [],
            year=year,
            venue_or_repo="GitHub",
            abstract=r.get("description") or "",
            url=url,
            doi=None,
            arxiv_id=None,
            bibtex=bibtex,
            pdf_available=False,
        )
