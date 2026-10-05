"""The manifest — single durable source of truth (`{theme}/manifest.json`).

Responsibilities: load / validate / write; canonical-ID assignment (FR-3); the
set-difference that powers Update (FR-8); and — critically — the field
ownership guard: the tool writes only objective fields and **never** creates or
overwrites agent-owned (judgment) fields on records that already exist.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from .idutil import canonical_id
from .models import (
    AGENT_OWNED_FIELDS,
    MANIFEST_VERSION,
    Record,
    utc_now_iso,
)

log = logging.getLogger("landscape.manifest")


class ManifestError(Exception):
    """Raised when an on-disk manifest is malformed or version-incompatible."""


def assign_canonical_id(record: Record) -> str:
    """Assign and return ``record.id`` using FR-3 precedence."""
    repo = record.source_native_id if record.source == "github" else None
    record.id = canonical_id(
        arxiv_id=record.arxiv_id,
        doi=record.doi,
        repo=repo,
        source=record.source,
        source_native_id=record.source_native_id,
    )
    return record.id


class Manifest:
    """In-memory view of a manifest file with ownership-safe mutations."""

    def __init__(self, path: Path, data: dict):
        self.path = Path(path)
        self.data = data
        self._index: dict[str, dict] = {r["id"]: r for r in data.get("resources", [])}

    # -- construction ------------------------------------------------------ #
    @classmethod
    def load_or_init(
        cls,
        theme_dir: Path,
        theme: str,
        description: str = "",
        dimensions: Optional[list] = None,
    ) -> "Manifest":
        theme_dir = Path(theme_dir)
        path = theme_dir / "manifest.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
            except json.JSONDecodeError as exc:
                raise ManifestError(f"manifest is not valid JSON: {exc}") from exc
            cls._validate(data)
            # description may be refreshed (objective); dimensions are agent-owned.
            if description:
                data["description"] = description
            return cls(path, data)

        theme_dir.mkdir(parents=True, exist_ok=True)
        now = utc_now_iso()
        data = {
            "manifest_version": MANIFEST_VERSION,
            "theme": theme,
            "description": description,
            # agent-owned; tool initializes empty and never touches it again.
            "dimensions": dimensions or [],
            "created": now,
            "last_updated": now,
            "runs": [],
            "resources": [],
        }
        return cls(path, data)

    @staticmethod
    def _validate(data: dict) -> None:
        if "manifest_version" not in data:
            raise ManifestError("manifest missing 'manifest_version'")
        on_disk = str(data["manifest_version"])
        if on_disk.split(".")[0] != MANIFEST_VERSION.split(".")[0]:
            raise ManifestError(
                f"incompatible manifest_version {on_disk!r} "
                f"(tool speaks {MANIFEST_VERSION!r})"
            )
        for key in ("theme", "resources", "runs"):
            if key not in data:
                raise ManifestError(f"manifest missing required key '{key}'")

    # -- queries ----------------------------------------------------------- #
    def record_ids(self) -> set[str]:
        return set(self._index.keys())

    def has(self, canonical: str) -> bool:
        return canonical in self._index

    def records(self) -> list[Record]:
        return [Record.from_dict(r) for r in self.data["resources"]]

    @property
    def dimensions(self) -> list:
        return self.data.get("dimensions", [])

    # -- set-difference for Update (FR-8) ---------------------------------- #
    def partition_new(self, records: list[Record]) -> tuple[list[Record], list[Record]]:
        """Split incoming records into (new, already-present-by-canonical-id)."""
        new, dup = [], []
        for rec in records:
            (dup if self.has(rec.id) else new).append(rec)
        return new, dup

    # -- ownership-safe mutations ------------------------------------------ #
    def add_resource(self, record: Record) -> None:
        """Append a brand-new resource. Caller must ensure the id is new.

        The persisted dict carries the agent-owned fields only at their inert
        defaults (``status='raw'``, etc.) — the agent fills them later.
        """
        if self.has(record.id):
            raise ManifestError(
                f"refusing to overwrite existing resource {record.id!r}; "
                "use merge_cross_links for objective updates"
            )
        d = record.to_dict()
        self._index[record.id] = d
        self.data["resources"].append(d)

    def merge_cross_links(self, canonical: str, links: list[str]) -> None:
        """Merge cross-links into an existing record (objective field only).

        This is the *one* mutation the tool may make to an already-present
        record — and it touches no agent-owned field.
        """
        rec = self._index.get(canonical)
        if rec is None:
            return
        merged = sorted(set(rec.get("cross_links", [])) | set(links) - {canonical})
        rec["cross_links"] = merged

    def assert_no_agent_field_drift(self, before: dict[str, dict]) -> None:
        """Defensive guard: verify no agent-owned field changed on records that
        existed before this run. Raises if drift is detected (a contract bug)."""
        for cid, prior in before.items():
            cur = self._index.get(cid)
            if cur is None:
                continue
            for f in AGENT_OWNED_FIELDS:
                if prior.get(f) != cur.get(f):
                    raise ManifestError(
                        f"tool mutated agent-owned field '{f}' on {cid!r} — "
                        "this violates the manifest contract"
                    )

    def snapshot_agent_fields(self) -> dict[str, dict]:
        """Capture agent-owned fields of all current records (for the guard)."""
        return {
            cid: {f: rec.get(f) for f in AGENT_OWNED_FIELDS}
            for cid, rec in self._index.items()
        }

    # -- runs + persistence ------------------------------------------------ #
    def add_run(self, run: dict) -> None:
        self.data["runs"].append(run)

    def save(self) -> None:
        self.data["last_updated"] = utc_now_iso()
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))
        tmp.replace(self.path)
        log.info("wrote manifest %s (%d resources)", self.path, len(self.data["resources"]))
