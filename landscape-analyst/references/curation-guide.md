# Curation guide — relevance scoring & rationale

Curation is the highest-leverage judgment you make: it decides what the whole
analysis is *about*. The gold-set agreement target (QR-1, e.g. ≥90% keep/drop
match) is how we know you're calling it the way a domain expert would.

## The relevance question

For each resource ask: **does this materially inform the theme as described?**
Anchor on the theme *description*, not just the title. "GeoAI foundation models"
with the description "self-supervised/pretrained models for satellite, aerial,
or geospatial raster/vector data" makes the edges decidable:

- A ViT pretrained on Sentinel-2 → **keep** (on-theme).
- A general CV foundation model *applied* to one remote-sensing benchmark →
  **borderline**; keep only if foundation-model methodology is central, drop if
  it's an application paper that merely cites RS data.
- A geospatial library with no model → **drop** (tooling, not a FM).

When genuinely unsure, lean on the description's scope words and record the
uncertainty in the rationale rather than silently picking.

## Scores (0–1) — calibrated, not decorative

| score | meaning |
|-------|---------|
| 0.85–1.0 | core to the theme; a review that omitted it would be incomplete |
| 0.6–0.85 | clearly relevant, secondary |
| 0.4–0.6 | borderline; keep with a caveat or drop with a reason |
| < 0.4 | off-theme / tooling / tangential |

Pick the `curated`/`dropped` cut consistently (a sensible default is keep ≥ 0.5).
The score and the status must agree — don't mark something `dropped` at 0.8.

## Rationales — one line, falsifiable

A good rationale states the *evidence* and the *call*, so a reviewer can check
it against the abstract:

- ✅ "Pretrained masked-autoencoder on multispectral RS imagery; canonical GeoAI FM — keep."
- ✅ "Survey of NLP agents with no geospatial content — off-theme, drop."
- ❌ "Relevant." / "Looks good." (no evidence, not checkable)

Keep it to one sentence. If you needed two clauses to justify a borderline call,
that's fine — but if you need a paragraph, the description probably needs
sharpening (raise that with the user).

## Use what's actually in the manifest

Score from `title` + `abstract` + `venue_or_repo` + (if present) the downloaded
PDF at `local_path`. **`pdf_available: false` resources cannot be curated
(QR-7):** score their relevance honestly from the metadata, but set
`status: dropped` with a rationale that names availability as the reason (e.g.
"relevant (0.9) but metadata-only — no PDF; excluded under the PDF-grounded
reporting policy"). Keeping the true relevance score means an Update run can
promote the resource if a PDF becomes available.

## Cross-linked duplicates

If `cross_links` ties a preprint to its published version, curate the pair as one
work: keep the richer record, and give the other the same status/cluster so the
reports don't double-count it. Note the linkage in the rationale if it matters.

## Consistency is the metric

Agreement is measured against reference labels, so the failure mode to avoid is
*drift* — applying a stricter bar at resource 40 than at resource 4. If you find
your bar moving, re-read the description and a few early calls before continuing.
