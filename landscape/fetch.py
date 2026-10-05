"""PDF fetching (FR-5, FR-6).

Downloads PDFs *only* where openly available, into ``{theme}-raw/``. A missing
or failed download is never an error: the record stays ``pdf_available=False``
with ``local_path=None`` (metadata-only). No paywall circumvention — if a source
gave us no open PDF URL, we simply do not have a PDF.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from .http import HttpClient
from .models import Record

log = logging.getLogger("landscape.fetch")


def _safe_filename(record: Record) -> str:
    """Deterministic, filesystem-safe basename derived from the canonical id."""
    base = record.id or record.source_native_id or record.title or "resource"
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("_")
    return f"{base}.pdf"


def download_pdfs(
    records: list[Record], raw_dir: Path, client: HttpClient
) -> tuple[int, int]:
    """Download available PDFs for ``records`` into ``raw_dir``.

    Mutates each record's ``local_path`` / ``pdf_available`` to reflect reality.
    Returns ``(downloaded_count, metadata_only_count)``.
    """
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    metadata_only = 0

    for rec in records:
        pdf_url = getattr(rec, "pdf_url", None)
        if not rec.pdf_available or not pdf_url:
            rec.pdf_available = False
            rec.local_path = None
            metadata_only += 1
            continue

        dest = raw_dir / _safe_filename(rec)
        if dest.exists() and dest.stat().st_size > 0:
            rec.local_path = str(dest)
            downloaded += 1
            continue

        ok = client.download(pdf_url, dest)
        if ok and dest.exists() and dest.stat().st_size > 0:
            rec.local_path = str(dest)
            downloaded += 1
        else:
            # available-but-unreachable degrades cleanly to metadata-only
            log.info("PDF unavailable for %s (%s)", rec.id, pdf_url)
            rec.pdf_available = False
            rec.local_path = None
            metadata_only += 1

    return downloaded, metadata_only
