#!/usr/bin/env python3
"""Write the agent-owned dimension rubric to a manifest.

`dimensions` is the one theme-level field the analyst owns. This sets it without
touching anything else.

Usage:
    python set_dimensions.py {theme}/manifest.json dimensions.json [--dry-run]

dimensions.json: a list of {"name": str, "description": str}.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("dimensions")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    manifest_path = Path(args.manifest)
    try:
        manifest = json.loads(manifest_path.read_text())
        dims = json.loads(Path(args.dimensions).read_text())
    except FileNotFoundError as exc:
        sys.exit(f"error: {exc}")
    except json.JSONDecodeError as exc:
        sys.exit(f"error: invalid JSON: {exc}")

    if not isinstance(dims, list) or not all(
        isinstance(d, dict) and d.get("name") for d in dims
    ):
        sys.exit("error: dimensions must be a list of objects each with a 'name'")

    # normalize to {name, description}
    clean = [{"name": d["name"], "description": d.get("description", "")} for d in dims]

    if args.dry_run:
        print(f"[dry-run] would set {len(clean)} dimension(s): "
              f"{', '.join(d['name'] for d in clean)}")
        return 0

    manifest["dimensions"] = clean
    tmp = manifest_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    tmp.replace(manifest_path)
    print(f"set {len(clean)} dimension(s) in {manifest_path}: "
          f"{', '.join(d['name'] for d in clean)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
