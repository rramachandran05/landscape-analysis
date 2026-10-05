#!/usr/bin/env python3
"""Mechanical acceptance checks for the landscape reports (the parts of
QR-2 … QR-6 a script can verify objectively).

What it checks:
  QR-2  every curated resource has a value for every rubric dimension
        (a concrete value or the literal "not stated").
  QR-3  the Full Report references every curated resource (by canonical id).
  QR-4  the 2-pager synthesis body is <= ~2 pages (word-count heuristic;
        the cluster-profiles section — or a legacy appendix — is excluded).
  QR-6  every [canonical-id] cited in either report exists in the manifest;
        warns if a 2-pager citation points at a dropped resource.
  QR-7  reports are PDF-grounded: no resource with pdf_available false is
        curated, cited in the 2-pager, or cited in the Full Report outside
        its Dropped section.

It does NOT judge rationale soundness, cluster coherence, or synthesis quality —
those need a human. Exit code is non-zero if any hard check fails.

Usage:
    python check_reports.py {theme}/manifest.json \
        --full-report full_report.md --two-pager two_pager.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ID_RE = re.compile(r"\[([A-Za-z][A-Za-z0-9]*:[^\]\s][^\]]*)\]")
WORDS_PER_PAGE = 500
TWO_PAGER_MAX_PAGES = 2.0
# The 2-pager carries a cluster-profiles section (top-3 representative-paper
# extractions + full membership per cluster); older reports carried an appendix.
# The ≤2-page limit (QR-4) applies to the *synthesis body* only, so we split on
# the first such marker before counting words. Citation checks (QR-6) still run
# over the whole file.
APPENDIX_RE = re.compile(
    r"^<!--\s*(APPENDIX|CLUSTER PROFILES)\s*-->\s*$|^#{1,6}\s+(Appendix|Cluster profiles)\b",
    re.IGNORECASE | re.MULTILINE,
)


def synthesis_body(text: str) -> str:
    """The 2-pager content before the cluster-profiles/appendix marker."""
    m = APPENDIX_RE.search(text)
    return text[: m.start()] if m else text


def _load_json(path):
    return json.loads(Path(path).read_text())


def _read(path):
    return Path(path).read_text() if path else ""


def cited_ids(text: str) -> set[str]:
    return {m.group(1).strip() for m in ID_RE.finditer(text)}


def check(manifest: dict, full_report: str, two_pager: str) -> dict:
    resources = manifest.get("resources", [])
    by_id = {r["id"]: r for r in resources}
    all_ids = set(by_id)
    dropped_ids = {r["id"] for r in resources if r.get("status") == "dropped"}
    curated = [r for r in resources if r.get("status") == "curated"]
    dim_names = [d["name"] for d in manifest.get("dimensions", [])]

    failures, warnings = [], []

    # QR-2: dimension coverage on curated resources
    if not dim_names:
        warnings.append("manifest has no dimensions set — cannot check QR-2 coverage")
    for r in curated:
        dims = r.get("dimensions") or {}
        missing = [d for d in dim_names if not str(dims.get(d, "")).strip()]
        if missing:
            failures.append(
                f"QR-2: curated {r['id']} missing dimension value(s): {', '.join(missing)} "
                "(use a concrete value or \"not stated\")"
            )

    # QR-3: Full Report covers every curated resource
    if full_report:
        fr_ids = cited_ids(full_report)
        uncovered = [r["id"] for r in curated if r["id"] not in fr_ids
                     and r["id"] not in full_report]
        if uncovered:
            failures.append(
                f"QR-3: Full Report does not reference {len(uncovered)} curated "
                f"resource(s): {', '.join(uncovered[:8])}"
                f"{'…' if len(uncovered) > 8 else ''}"
            )

    # QR-4: 2-pager length (synthesis body only; the appendix is excluded)
    pages = None
    if two_pager:
        words = len(synthesis_body(two_pager).split())
        pages = words / WORDS_PER_PAGE
        if pages > TWO_PAGER_MAX_PAGES:
            failures.append(
                f"QR-4: 2-pager is ~{pages:.1f} pages ({words} words) — exceeds 2 pages"
            )

    # QR-6: no fabricated citations
    for label, text in (("Full Report", full_report), ("2-pager", two_pager)):
        if not text:
            continue
        for cid in cited_ids(text):
            if cid not in all_ids:
                failures.append(f"QR-6: {label} cites unknown id [{cid}] (not in manifest)")
    # QR-4/6 nuance: 2-pager claims should trace to *curated* resources
    if two_pager:
        for cid in cited_ids(two_pager):
            if cid in dropped_ids:
                warnings.append(f"2-pager cites a dropped resource [{cid}] — claims should rest on curated work")

    # QR-7: PDF-grounded reports — metadata-only resources never curated/cited
    no_pdf_ids = {r["id"] for r in resources if not r.get("pdf_available")}
    for r in curated:
        if r["id"] in no_pdf_ids:
            failures.append(
                f"QR-7: curated {r['id']} has no PDF (pdf_available false) — "
                "metadata-only resources must be dropped, not curated"
            )
    if two_pager:
        for cid in sorted(cited_ids(two_pager) & no_pdf_ids):
            failures.append(f"QR-7: 2-pager cites metadata-only resource [{cid}] (no PDF)")
    if full_report:
        # metadata-only ids may appear in the Dropped table, but nowhere before it
        m = re.search(r"^#{1,6}\s+Dropped\b", full_report, re.MULTILINE)
        fr_body = full_report[: m.start()] if m else full_report
        for cid in sorted(cited_ids(fr_body) & no_pdf_ids):
            failures.append(
                f"QR-7: Full Report cites metadata-only resource [{cid}] outside the Dropped section"
            )

    return {
        "failures": failures,
        "warnings": warnings,
        "summary": {
            "resources": len(resources),
            "curated": len(curated),
            "dropped": len(dropped_ids),
            "dimensions": dim_names,
            "two_pager_pages_est": round(pages, 2) if pages is not None else None,
        },
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("--full-report")
    ap.add_argument("--two-pager")
    ap.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = ap.parse_args(argv)

    result = check(_load_json(args.manifest), _read(args.full_report), _read(args.two_pager))

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        s = result["summary"]
        print(f"resources={s['resources']} curated={s['curated']} dropped={s['dropped']} "
              f"dimensions={len(s['dimensions'])}")
        if s["two_pager_pages_est"] is not None:
            print(f"2-pager ≈ {s['two_pager_pages_est']} pages")
        for w in result["warnings"]:
            print(f"WARN  {w}")
        for f in result["failures"]:
            print(f"FAIL  {f}")
        if not result["failures"]:
            print("OK — all mechanical checks passed (human judgment still required)")

    return 1 if result["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
