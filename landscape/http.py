"""Polite HTTP client: per-host rate limiting, exponential backoff, on-disk
response cache, and a contact User-Agent / ``mailto`` (FR-9).

Shared by all source adapters and by ``fetch`` so politeness policy lives in
one place. Network access is funnelled through :class:`HttpClient` so tests can
substitute a fake.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests


log = logging.getLogger("landscape.http")

DEFAULT_USER_AGENT = "landscape-analysis/0.1 (reproducible research tool)"

# Conservative per-host minimum seconds between requests. arXiv explicitly asks
# for >=3s; the others tolerate faster but we stay polite by default.
DEFAULT_MIN_INTERVALS = {
    "export.arxiv.org": 3.0,
    "arxiv.org": 3.0,
    "api.openalex.org": 0.2,
    "api.github.com": 1.0,
    "api.semanticscholar.org": 1.0,
}


@dataclass
class HttpResponse:
    status_code: int
    text: str
    url: str
    from_cache: bool = False

    def json(self):
        return json.loads(self.text)


@dataclass
class HttpClient:
    """A small, cache-backed, rate-limited wrapper over ``requests``."""

    cache_dir: Optional[Path] = None
    mailto: Optional[str] = None
    user_agent: str = DEFAULT_USER_AGENT
    max_retries: int = 4
    timeout: float = 30.0
    min_intervals: dict = field(default_factory=lambda: dict(DEFAULT_MIN_INTERVALS))
    default_min_interval: float = 1.0
    _last_request_at: dict = field(default_factory=dict)
    _session: Optional[requests.Session] = None

    def __post_init__(self):
        if self.cache_dir is not None:
            self.cache_dir = Path(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._session = requests.Session()
        ua = self.user_agent
        if self.mailto:
            ua = f"{ua} mailto:{self.mailto}"
        self._session.headers.update({"User-Agent": ua})

    # -- public API -------------------------------------------------------- #
    def get(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        use_cache: bool = True,
    ) -> HttpResponse:
        """GET with cache + rate-limit + backoff. Raises on exhausted retries."""
        cache_path = self._cache_path(url, params) if (use_cache and self.cache_dir) else None
        if cache_path is not None and cache_path.exists():
            log.debug("cache hit: %s", url)
            cached = json.loads(cache_path.read_text())
            return HttpResponse(
                status_code=cached["status_code"],
                text=cached["text"],
                url=cached["url"],
                from_cache=True,
            )

        host = urllib.parse.urlparse(url).netloc
        resp = self._request_with_backoff(url, params=params, headers=headers, host=host)

        if cache_path is not None and 200 <= resp.status_code < 300:
            cache_path.write_text(
                json.dumps(
                    {"status_code": resp.status_code, "text": resp.text, "url": resp.url}
                )
            )
        return resp

    def download(self, url: str, dest: Path, headers: Optional[dict] = None) -> bool:
        """Stream a binary resource (e.g. a PDF) to ``dest``.

        Returns True on success, False on any non-2xx / network error (callers
        treat a failed download as "metadata-only", never a hard failure).
        """
        host = urllib.parse.urlparse(url).netloc
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(self.max_retries):
            self._respect_rate_limit(host)
            try:
                with self._session.get(
                    url, stream=True, timeout=self.timeout, headers=headers
                ) as r:
                    self._mark_request(host)
                    if r.status_code == 429 or 500 <= r.status_code < 600:
                        self._sleep_backoff(attempt, r)
                        continue
                    if not (200 <= r.status_code < 300):
                        log.warning("download non-2xx %s: %s", r.status_code, url)
                        return False
                    tmp = dest.with_suffix(dest.suffix + ".part")
                    with open(tmp, "wb") as fh:
                        for chunk in r.iter_content(chunk_size=65536):
                            if chunk:
                                fh.write(chunk)
                    tmp.replace(dest)
                    return True
            except requests.RequestException as exc:
                log.warning("download error (attempt %d) %s: %s", attempt + 1, url, exc)
                self._sleep_backoff(attempt, None)
        return False

    # -- internals --------------------------------------------------------- #
    def _request_with_backoff(self, url, params, headers, host) -> HttpResponse:
        last_exc = None
        for attempt in range(self.max_retries):
            self._respect_rate_limit(host)
            try:
                r = self._session.get(
                    url, params=params, headers=headers, timeout=self.timeout
                )
                self._mark_request(host)
                if r.status_code == 429 or 500 <= r.status_code < 600:
                    log.warning("retryable status %s for %s", r.status_code, url)
                    self._sleep_backoff(attempt, r)
                    continue
                return HttpResponse(status_code=r.status_code, text=r.text, url=r.url)
            except requests.RequestException as exc:
                last_exc = exc
                log.warning("request error (attempt %d) %s: %s", attempt + 1, url, exc)
                self._sleep_backoff(attempt, None)
        raise RuntimeError(f"GET failed after {self.max_retries} attempts: {url} ({last_exc})")

    def _respect_rate_limit(self, host: str) -> None:
        interval = self.min_intervals.get(host, self.default_min_interval)
        last = self._last_request_at.get(host)
        if last is not None:
            wait = interval - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)

    def _mark_request(self, host: str) -> None:
        self._last_request_at[host] = time.monotonic()

    def _sleep_backoff(self, attempt: int, resp) -> None:
        retry_after = None
        if resp is not None:
            ra = resp.headers.get("Retry-After")
            if ra:
                try:
                    retry_after = float(ra)
                except ValueError:
                    retry_after = None
        delay = retry_after if retry_after is not None else min(2.0 ** attempt, 30.0)
        time.sleep(delay)

    def _cache_path(self, url: str, params: Optional[dict]) -> Path:
        key = url
        if params:
            key += "?" + urllib.parse.urlencode(sorted(params.items()))
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
        return self.cache_dir / f"{digest}.json"
