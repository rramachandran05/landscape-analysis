#!/usr/bin/env python3
"""Merge agent-owned judgment fields into a manifest — contract-safe.

This is the *only* sanctioned way for the analyst to write the manifest. It
accepts a decisions JSON keyed by canonical id and merges **only** the five
agent-owned fields onto matching resources. Tool-owned (objective) fields are
physically unreachable from here, so the field-ownership contract cannot be
violated from the agent side.

Usage:
    python apply_curation.py {theme}/manifest.json decisions.json [--dry-run]

decisions.json:
    { "<canonical id>": { "status": "curated", "relevance_score": 0.9,
        "relevance_rationale": "...", "dimensions": {...}, "cluster_id": "..." },
      ... }
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AGENT_FIELDS = {
    "status",
    "relevance_score",
    "relevance_rationale",
    "dimensions",
    "cluster_id",
}
VALID_STATUS = {"raw", "curated", "dropped"}


def _load(path: Path):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        sys.exit(f"error: file not found: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"error: {path} is not valid JSON: {exc}")


def apply_decisions(manifest: dict, decisions: dict) -> dict:
    index = {r["id"]: r for r in manifest.get("resources", [])}
    stats = {"updated": 0, "skipped_unknown": [], "ignored_fields": set(), "errors": []}

    for cid, fields in decisions.items():
        rec = index.get(cid)
        if rec is None:
            stats["skipped_unknown"].append(cid)
            continue
        if not isinstance(fields, dict):
            stats["errors"].append(f"{cid}: decision must be an object")
            continue

        status = fields.get("status", rec.get("status", "raw"))
        if status not in VALID_STATUS:
            stats["errors"].append(f"{cid}: invalid status {status!r}")
            continue
        if status != "raw" and not (fields.get("relevance_rationale") or rec.get("relevance_rationale")):
            stats["errors"].append(f"{cid}: status {status!r} requires a relevance_rationale")
            continue

        for key, value in fields.items():
            if key not in AGENT_FIELDS:
                stats["ignored_fields"].add(key)
                continue
            rec[key] = value
        stats["updated"] += 1

    return stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("decisions")
    ap.add_argument("--dry-run", action="store_true", help="validate without writing")
    args = ap.parse_args(argv)

    manifest_path = Path(args.manifest)
    manifest = _load(manifest_path)
    decisions = _load(Path(args.decisions))
    if not isinstance(decisions, dict):
        sys.exit("error: decisions file must be a JSON object keyed by canonical id")

    stats = apply_decisions(manifest, decisions)

    if stats["errors"]:
        print("VALIDATION ERRORS (no changes written):", file=sys.stderr)
        for e in stats["errors"]:
            print(f"  - {e}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"[dry-run] would update {stats['updated']} resource(s)")
    else:
        tmp = manifest_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        tmp.replace(manifest_path)
        print(f"updated {stats['updated']} resource(s) in {manifest_path}")

    if stats["skipped_unknown"]:
        print(f"warning: {len(stats['skipped_unknown'])} unknown id(s) skipped: "
              f"{', '.join(stats['skipped_unknown'][:5])}"
              f"{'…' if len(stats['skipped_unknown']) > 5 else ''}", file=sys.stderr)
    if stats["ignored_fields"]:
        print(f"note: ignored non-agent field(s): {', '.join(sorted(stats['ignored_fields']))} "
              "(objective fields are owned by the tool)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
