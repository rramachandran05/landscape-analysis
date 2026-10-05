# Eval harness — checking QR-1 … QR-6

Two layers of evaluation, matching the spec's split:

1. **Domain evals (this directory)** — does the analyst curate and characterize
   resources the way a domain expert would? Measured against a **gold set** of
   reference keep/drop labels and ideal dimension rows.
2. **Skill evals (`../landscape-analyst-workspace/`)** — does the *skill* make
   Claude do the right thing end-to-end? Run via the skill-creator's test loop
   (test prompts in `evals.json`, with-skill vs. baseline, human review).

## Domain eval: the gold set (QR-1, QR-2)

Per the spec, build ~20–30 reference resources **per test theme** with
human-verified keep/drop labels and a handful of hand-written ideal dimension
rows. Use `gold/gold.template.json` as the format. The labels must be authored
or signed off by a human — that's the point of a gold set.

Workflow:

```bash
# 1. collect a manifest with the Phase A tool
python -m landscape collect --theme "GeoAI FMs" --query "geospatial foundation model" \
    --since 2023-01 --sources arxiv,github,openalex

# 2. have the analyst skill curate it (sets status / dimensions / clusters)

# 3. score curation agreement against the gold labels
python score_curation.py "GeoAI FMs"/manifest.json gold/geoai-fm.gold.json --threshold 0.9
```

`score_curation.py` reports:
- **curation agreement** = fraction of gold-labeled resources whose decision
  matches the reference (QR-1; default pass ≥ 0.90), with each disagreement
  listed alongside the analyst's rationale so you can see *why* it diverged.
- **dimension spot-check** = match rate on the ideal dimension rows (a QR-2
  sanity check); disagreements are shown so wording differences vs. real errors
  are distinguishable.

## Report checks (QR-2 … QR-6)

The mechanical report checks live in `../scripts/check_reports.py`:

```bash
python ../scripts/check_reports.py "GeoAI FMs"/manifest.json \
    --full-report full_report.md --two-pager two_pager.md
```

It enforces dimension coverage (QR-2), Full-Report completeness (QR-3), 2-pager
length (QR-4), and citation integrity / no fabrication (QR-6). QR-5 (Update
deltas) and the *qualitative* parts — rationale soundness, cluster coherence,
synthesis quality — are judged in the human review loop.

## Regression guard

Re-run both layers on any change to the skill (prompt or flow). Curation
agreement dropping below threshold, or new `check_reports.py` failures, is a
regression to fix before shipping.

## Files

- `gold/gold.template.json` — gold-set format (copy per theme, fill with real labels).
- `score_curation.py` — QR-1 scorer + QR-2 dimension spot-check.
- `evals.json` — skill-creator test prompts (skill-level eval).
