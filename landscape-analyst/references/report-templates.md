# Report templates

Two core deliverables, plus an Update delta block — and an optional third,
decision-maker-facing **Final Report** (see §4 and
`references/final-report-template.md`). The two core reports must be **traceable**
(every claim maps to a curated resource by canonical id), contain **no
fabrication** (nothing absent from the manifest), and be **PDF-grounded**
(QR-7): a resource with `pdf_available: false` is never curated and may appear
only in the Full Report's Dropped table — never cited in either report's body.
The mechanical checks live in `scripts/check_reports.py`; these templates are
the structure to fill.

References use the canonical id in brackets, e.g. `[arXiv:2301.00001]`, so the
checker (and the reader) can trace any statement back to the manifest.

---

## 1. Full Report

Purpose: the complete, consistent record. Same dimensions, same order, for
**every curated resource**, grouped by cluster (QR-3).

```markdown
# Landscape Analysis — {theme}

_{description}_
Generated {date} · run {run_id} · {N curated} of {M collected} resources curated.

## Dimensions
{numbered list of rubric dimensions with their descriptions}

## Cluster map
- **{cluster-id}** — {one-line characterization} ({k} resources)
- ...

## {Cluster A label}

### Overview
{2–4 sentences: what unifies this cluster, where the action is.}

### Comparison table
| Resource | {Dim 1} | {Dim 2} | ... | {Dim n} |
|----------|---------|---------|-----|---------|
| {title short} [{id}] | ... | ... | ... | ... |

### Resources
**{Title}** [{id}] · {authors, year, venue_or_repo} · {relevance_score}
{2–4 sentence summary grounded in abstract/PDF. State each dimension value;
write "not stated" where the source is silent. Note cross-links if relevant.}

... (repeat per resource, in a stable order — e.g. by year desc then id) ...

## {Cluster B label}
...

## Dropped (considered, not included)
| Resource | [id] | why dropped |
|----------|------|-------------|
| ... | ... | {one-line rationale} |
```

Rules that the checker enforces, so build them in:
- Every `curated` resource appears exactly once, under its cluster.
- Every resource row lists **all** rubric dimensions in the **same order**.
- A `Dropped` section lists dropped resources with their rationales (shows the
  curation was deliberate, aids Update).

---

## 2. Two-pager (synthesis)

Purpose: what a busy reader needs. Organized **by dimension/cluster, not as a
flat list** (QR-4), ≤2 pages, every claim traceable.

```markdown
# {theme} — Landscape in 2 pages

_{description}_ · {N} curated resources · {date}

## The shape of the field
{One tight paragraph: the major clusters and how they relate. Cite exemplars
[id]. This is synthesis, not a list — tell the reader what's going on.}

## By dimension
**{Dimension 1}.** {What the landscape looks like along this axis — the common
choices, the outliers, the gaps. e.g. "Most models pretrain with MAE
[id][id]; contrastive approaches are rarer [id]. Parameter counts are usually
unreported."}
**{Dimension 2}.** ...
{Cover the dimensions that carry signal; a dimension where everything says
"not stated" is itself worth one sentence as a gap.}

## Clusters at a glance
- **{Cluster}** — {what it is, the 1–2 works to read first [id]}.
- ...

## Gaps & open questions
{3–5 bullets: what's missing, under-evaluated, or contested — drawn only from
what the curated set does/doesn't show.}

## Read-first shortlist
{3–6 resources with [id] and a half-line on why each.}

<!-- CLUSTER PROFILES -->

## Cluster profiles
_One profile per cluster: the full extractions of the cluster's **top-3
representative papers** (reproduced mechanically from the Full Report /
manifest), followed by every other curated paper in the cluster._

### {Cluster label}

**{Representative 1 title}** [{id}] · {authors, year, venue_or_repo} ·
relevance {relevance_score}

{2–4 sentence summary — the same summary as this resource's Full Report entry.}

- **{Dimension 1}:** {value as recorded in the manifest, verbatim}
- ... (all rubric dimensions, in order) ...

... (repeat for the 2nd and 3rd representative papers) ...

**Other papers in this cluster** ({k})
- **{Title}** [{id}] — {half-line: what it adds to the cluster}.
- ... (every other curated resource with this cluster_id — none omitted) ...

... (repeat per cluster, in cluster-map order) ...
```

**Choosing the representative papers.** Pick the top 3 per cluster (fewer only
if the cluster has fewer members) — the works that best exemplify what the
cluster is about: typically the highest-relevance resources, tie-broken by how
much the synthesis leans on them; prefer PDF-grounded over metadata-only when
otherwise equal. Each must be a curated member of that cluster.

Keep the **synthesis body** (everything before the `<!-- CLUSTER PROFILES -->`
marker) to two pages — if it overflows, cut prose, not traceability; merge
dimension paragraphs before you drop citations. The **cluster-profiles section
is mandatory and is not counted toward the 2-page limit** (`check_reports.py`
splits on the marker): each cluster gets its top-3 representative papers' full
manifest extractions (summary + all dimensions, in the same format as the Full
Report entry) and then a list of **every other curated paper in the cluster** —
so a reader sees the exemplars in depth and the cluster's full membership
without opening the Full Report. There is no separate appendix.

Build the profiles mechanically from the manifest after the synthesis is
final — never hand-retype dimension values (that risks drift from the
manifest). The profiles introduce no resource or fact absent from the manifest
(QR-6).

After the 2-pager passes the checks, run `scripts/finalize_two_pager.py` to
produce the two finishing artifacts: it copies every cited resource's PDF into
`{theme}/curated-papers/` and renders `{theme}/two_pager.pdf` (synthesis +
cluster profiles). Note that because the profiles list all curated papers per
cluster, the whole curated set's PDFs travel with the report. So the full
deliverable set is: `full_report.md`, `two_pager.md`, `two_pager.pdf`, and
`curated-papers/`.

---

## 3. Update delta block (Update mode only — QR-5)

Append to / prepend before both reports so a returning reader sees what moved.
Preserve prior curation; only the genuinely-changed items appear here.

```markdown
## Changes since {prior run_id} ({prior date} → {this date})

**Added** ({n})
- **{Title}** [{id}] — {cluster}; {one-line why it's relevant}.

**Dropped** ({n})
- **{Title}** [{id}] — {why now dropped, if a prior decision was revised}.

**Changed by dimension** ({n})
- [{id}] {Dimension}: "{old value}" → "{new value}" ({why}).

**Unchanged:** {count} curated resources retained their prior decisions.
```

If a section is empty, say "none" rather than omitting it — the reader should
see that you checked.

---

## 4. Final Report (optional, decision-maker-facing)

A third deliverable synthesized **from** the finished Full Report and 2-pager: a
bulleted, IEEE-cited **technical assessment** written for a program/leadership
audience deciding what to do about the field. It introduces no new facts (QR-6),
stays PDF-grounded (QR-7), and cites only the subset of curated resources that
carries the argument (typically 10–25), translated from canonical manifest ids
into a clean numbered reference list.

Its defining conventions — bulleted throughout, a bold **Key Take-away:** /
**Section main point:** ending every top-level section, IEEE-numbered citations in
order of first appearance, and a decision-maker framing (opportunity, maturity
gap, risks, oversight) — plus the full annotated section skeleton, the
generation procedure, the citation-numbering rules, and an honesty self-check,
live in **`references/final-report-template.md`**. Produce it only after the two
core reports are final; write it to `{theme}/final_report.md`.
