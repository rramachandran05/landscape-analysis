"""Run orchestration (the §4a run flow).

load-or-init manifest → for each source: query → normalize → assign canonical
IDs → dedup against manifest → (Update: keep only new) → download available
PDFs → write records (``status=raw``) + run metadata → emit run summary.

Importable: call :func:`collect`. The CLI is a thin wrapper over it.
"""

from __future__ import annotations

import logging
import re
import uuid
from pathlib import Path
from typing import Optional

from . import dedup
from .http import HttpClient
from .manifest import Manifest, assign_canonical_id
from .models import DateWindow, Record, utc_now_iso
from .sources import DEFAULT_SOURCES, get_adapter
from .sources.base import SourceError

log = logging.getLogger("landscape.pipeline")


def slugify(theme: str) -> str:
    """Filesystem-safe directory slug for a theme (manifest keeps the raw name)."""
    s = re.sub(r"[^A-Za-z0-9]+", "-", theme.strip().lower()).strip("-")
    return s or "theme"


def _new_run_id(timestamp: str) -> str:
    compact = re.sub(r"[^0-9]", "", timestamp)[:14]
    return f"run-{compact}-{uuid.uuid4().hex[:8]}"


def collect(
    *,
    theme: str,
    queries: dict[str, str],
    date_window: DateWindow,
    sources: Optional[list[str]] = None,
    base_dir: str | Path = ".",
    mode: str = "create",
    description: str = "",
    dimensions: Optional[list] = None,
    mailto: Optional[str] = None,
    max_results: int = 200,
    cache_dir: Optional[str | Path] = None,
    run_id: Optional[str] = None,
) -> dict:
    """Run one collection (``create`` or ``update``) and return a run summary.

    ``queries`` maps source name -> query string; a ``"*"`` key provides a
    default for any source without its own entry.
    """
    sources = list(sources or DEFAULT_SOURCES)
    base_dir = Path(base_dir)
    slug = slugify(theme)
    theme_dir = base_dir / slug
    raw_dir = base_dir / f"{slug}-raw"
    if cache_dir is None:
        cache_dir = base_dir / ".landscape-cache"

    timestamp = utc_now_iso()
    run_id = run_id or _new_run_id(timestamp)

    client = HttpClient(cache_dir=Path(cache_dir), mailto=mailto)
    manifest = Manifest.load_or_init(theme_dir, theme, description, dimensions)

    # Snapshot for the agent-field-drift guard, and the cross-link universe.
    agent_snapshot = manifest.snapshot_agent_fields()
    existing_records = manifest.records()

    # 1) Query + normalize each source independently.
    collected: list[Record] = []
    source_runs: list[dict] = []
    for source in sources:
        query = queries.get(source) or queries.get("*") or ""
        adapter = get_adapter(source, client)
        adapter.max_results = max_results
        try:
            recs = adapter.collect(query, date_window)
            status = "ok"
        except SourceError as exc:
            log.warning("source %s failed, continuing: %s", source, exc)
            recs = []
            status = f"error: {exc}"
        for rec in recs:
            assign_canonical_id(rec)
            rec.retrieved_on = timestamp
            rec.run_id_first_seen = run_id
        collected.extend(recs)
        source_runs.append(
            {
                "source": source,
                "query_string": query,
                "date_window": date_window.to_dict(),
                "result_count": len(recs),
                "status": status,
            }
        )

    queried_count = len(collected)

    # 2) Dedup within the batch (across sources), then set-difference vs manifest.
    dd = dedup.merge_duplicates(collected)
    new_records, dup_existing = manifest.partition_new(dd.records)
    duplicate_count = dd.duplicates_collapsed + len(dup_existing)

    # 3) Cross-links: index new + existing; reciprocal links land on both.
    dedup.assign_cross_links(new_records, existing=existing_records)

    # 4) Download available PDFs (new records only).
    downloaded, metadata_only = (0, 0)
    if new_records:
        from .fetch import download_pdfs  # local import keeps requests optional at import

        downloaded, metadata_only = download_pdfs(new_records, raw_dir, client)

    # 5) Persist: append new resources, merge cross-link updates onto existing.
    for rec in new_records:
        manifest.add_resource(rec)
    for er in existing_records:
        if er.cross_links:
            manifest.merge_cross_links(er.id, er.cross_links)

    # 6) Record run metadata (FR-7) and verify the ownership contract held.
    manifest.add_run(
        {
            "run_id": run_id,
            "timestamp": timestamp,
            "mode": mode,
            "sources": source_runs,
        }
    )
    manifest.assert_no_agent_field_drift(agent_snapshot)
    manifest.save()

    # 7) Machine-readable run summary (FR-10).
    summary = {
        "run_id": run_id,
        "timestamp": timestamp,
        "mode": mode,
        "theme": theme,
        "manifest_path": str(manifest.path),
        "raw_dir": str(raw_dir),
        "counts": {
            "queried": queried_count,
            "new": len(new_records),
            "duplicate": duplicate_count,
            "downloaded": downloaded,
            "metadata_only": metadata_only,
        },
        "per_source": [
            {"source": s["source"], "result_count": s["result_count"], "status": s["status"]}
            for s in source_runs
        ],
        "total_resources": len(manifest.data["resources"]),
    }
    return summary
