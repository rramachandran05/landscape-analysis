#!/usr/bin/env python3
"""Score an analyst's curation against a gold set (QR-1, and a QR-2 spot-check).

Given a curated manifest and a gold file of reference keep/drop labels (plus a
few ideal dimension rows), this measures:

  * curation agreement — fraction of gold-labeled resources whose agent decision
    (curated→keep / dropped→drop) matches the reference label. This is the QR-1
    metric; the default pass threshold is 0.90.
  * dimension match (spot-check) — for resources with ideal dimension rows in the
    gold set, the fraction of dimension values that match (normalized), with
    disagreements listed so you can see whether they're real errors or wording.

Usage:
    python score_curation.py {theme}/manifest.json gold/geoai-fm.gold.json \
        [--threshold 0.9] [--json]

See gold/gold.template.json for the gold-set format.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _norm(v) -> str:
    return " ".join(str(v).strip().lower().split())


def _agent_label(status: str) -> str | None:
    if status == "curated":
        return "keep"
    if status == "dropped":
        return "drop"
    return None  # still raw == undecided


def score(manifest: dict, gold: dict, threshold: float) -> dict:
    by_id = {r["id"]: r for r in manifest.get("resources", [])}
    gold_res = gold.get("resources", {})

    decided = 0
    matches = 0
    disagreements = []
    undecided = []

    for cid, ref in gold_res.items():
        ref_label = ref.get("label")
        rec = by_id.get(cid)
        if rec is None:
            disagreements.append({"id": cid, "issue": "missing from manifest", "gold": ref_label})
            decided += 1
            continue
        agent = _agent_label(rec.get("status", "raw"))
        if agent is None:
            undecided.append(cid)
            continue
        decided += 1
        if agent == ref_label:
            matches += 1
        else:
            disagreements.append({
                "id": cid, "gold": ref_label, "agent": agent,
                "rationale": rec.get("relevance_rationale", ""),
            })

    agreement = (matches / decided) if decided else 0.0

    # Dimension spot-check on gold rows that include ideal dimensions.
    dim_total = dim_match = 0
    dim_disagreements = []
    for cid, ref in gold_res.items():
        ideal = ref.get("dimensions")
        rec = by_id.get(cid)
        if not ideal or rec is None:
            continue
        got = rec.get("dimensions") or {}
        for dim, ideal_val in ideal.items():
            dim_total += 1
            if _norm(got.get(dim, "")) == _norm(ideal_val):
                dim_match += 1
            else:
                dim_disagreements.append({
                    "id": cid, "dimension": dim,
                    "gold": ideal_val, "agent": got.get(dim, "<missing>"),
                })
    dim_rate = (dim_match / dim_total) if dim_total else None

    return {
        "curation": {
            "labeled": len(gold_res),
            "decided": decided,
            "undecided": undecided,
            "matches": matches,
            "agreement": round(agreement, 4),
            "threshold": threshold,
            "passed": agreement >= threshold and not undecided,
            "disagreements": disagreements,
        },
        "dimensions": {
            "checked": dim_total,
            "match_rate": round(dim_rate, 4) if dim_rate is not None else None,
            "disagreements": dim_disagreements,
        },
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest")
    ap.add_argument("gold")
    ap.add_argument("--threshold", type=float, default=0.90)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    manifest = json.loads(Path(args.manifest).read_text())
    gold = json.loads(Path(args.gold).read_text())
    result = score(manifest, gold, args.threshold)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        c = result["curation"]
        print(f"QR-1 curation agreement: {c['agreement']:.1%} "
              f"({c['matches']}/{c['decided']} decided; threshold {c['threshold']:.0%}) "
              f"-> {'PASS' if c['passed'] else 'FAIL'}")
        if c["undecided"]:
            print(f"  {len(c['undecided'])} gold resource(s) still 'raw' (undecided): "
                  f"{', '.join(c['undecided'][:5])}")
        for d in c["disagreements"]:
            print(f"  DISAGREE {d.get('id')}: gold={d.get('gold')} agent={d.get('agent', d.get('issue'))}")
        dm = result["dimensions"]
        if dm["match_rate"] is not None:
            print(f"dimension spot-check: {dm['match_rate']:.1%} match on {dm['checked']} value(s)")
            for d in dm["disagreements"]:
                print(f"  DIM {d['id']} [{d['dimension']}]: gold={d['gold']!r} agent={d['agent']!r}")

    return 0 if result["curation"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
