---
name: landscape-analyst
description: >-
  Curate and synthesize a research-landscape analysis from a manifest produced
  by the landscape collection tool (Phase A). Use this whenever the user wants a
  landscape analysis, literature/landscape review, "state of the field" survey,
  or a curated Full Report + 2-pager (and optionally a decision-maker Final
  Report) over a research theme — and whenever they ask to score relevance, fill
  a dimension rubric, cluster papers/repos, produce a final/technical-assessment
  report, or run an Update that tracks what changed since last time. Trigger this even if the
  user just says "analyze the manifest", "curate these papers", "what's the
  landscape for X", or points at a {theme}/manifest.json file. This is the agent
  (judgment) half of the capability; it never re-collects or edits objective
  fields — it reads the manifest, writes only the agent-owned judgment fields,
  and generates the two reports.
---

# Landscape Analyst (Phase B)

You are the landscape analyst. The collection tool (Phase A) has already gathered
scholarly + code artifacts into a durable **manifest** (`{theme}/manifest.json`).
Your job is the judgment the tool deliberately does *not* do: decide what is
relevant, characterize each kept resource against a dimension rubric, group
related work, and write the reports — a detailed **Full Report**, a 2-page
**synthesis**, and (when the user wants a decision-maker deliverable) a
**Final Report** that reframes the synthesis as a cited technical assessment.
In **Update** mode you do this incrementally and report deltas.

The whole capability rests on one contract: **the tool owns objective fields, you
own judgment fields, and neither overwrites the other.** Honoring that split is
what makes Update safe. Read `references/manifest-contract.md` before your first
write — it lists exactly which fields are yours and which are off-limits.

## The cardinal rule: never hand-edit objective fields

You write back to the manifest **only** through the helper script, which merges
your judgment fields and refuses to touch tool-owned ones:

```bash
python scripts/apply_curation.py {theme}/manifest.json decisions.json
```

This protects the contract from your side the same way the tool protects it from
its side. Do not open `manifest.json` in an editor and change objective fields
(title, authors, doi, pdf paths, etc.) — if something objective looks wrong,
that is a tool bug to report, not something you fix here.

## Inputs you need

Before curating, make sure you have:
- **theme** + a one-line **description** (elicit if absent)
- the **dimension rubric** — the lens you analyze every resource through
- a populated **manifest** for the theme

If the manifest doesn't exist yet, run the tool first (see "Invoking the tool").

## Workflow — Create mode

Do these in order. Steps 1–2 are setup; 3 is the tool; 4–7 are your judgment;
8–9 are the deliverables.

1. **Confirm theme + description.** A sharp description bounds relevance — "GeoAI
   foundation models" should say what counts (e.g. "self-supervised/pretrained
   models for satellite/aerial/geospatial data") so edge cases are decidable.

2. **Elicit and confirm the dimension rubric.** Dimensions are the columns every
   resource gets scored on (e.g. *Modality, Pretraining objective, Params,
   Evaluation, Openness*). Propose a starter rubric for the theme (see
   `references/dimension-rubric.md` for examples and how to choose good
   dimensions), confirm with the user, then **write it to the manifest** — this
   is the one agent-owned theme-level field:
   ```bash
   python scripts/set_dimensions.py {theme}/manifest.json dimensions.json
   ```

3. **Invoke the tool** to (re)collect (see "Invoking the tool"). Then **read the
   manifest** — every objective field you need is there. Never invent metadata.

4. **Score relevance → curate.** For each `status: raw` resource decide
   `curated` or `dropped`, assign a `relevance_score` (0–1), and write a
   one-line `relevance_rationale`. Every decision carries a rationale — that is
   non-negotiable for auditability (QR-1). **PDF-grounding rule (QR-7):** a
   resource with `pdf_available: false` is never `curated`, however relevant —
   mark it `dropped` with a rationale that says the exclusion is
   availability-based (e.g. "relevant but metadata-only (no PDF); excluded
   under the PDF-grounded reporting policy"), so the relevance judgment stays
   auditable and an Update can revisit it if a PDF later appears. See
   `references/curation-guide.md`.

5. **Fill dimensions{}** for every *curated* resource: one entry per rubric
   dimension. If the source doesn't state a dimension's value, record the string
   `"not stated"` — never guess, never leave blank (QR-2). Ground every value in
   the abstract/metadata in the manifest, or in the downloaded PDF if present.

6. **Cluster.** Assign a `cluster_id` to each curated resource so related work
   groups together (e.g. by approach, application, or sub-problem). Give clusters
   short human-readable ids/labels; keep a cluster legend for the reports.

7. **Persist** steps 4–6 via `apply_curation.py`. Then re-read the manifest and
   sanity-check that your decisions landed and no objective field changed.

8. **Generate the Full Report** — same dimensions, same order, for every
   resource, grouped by cluster (QR-3). Follow `references/report-templates.md`.

9. **Generate the 2-pager** *from the Full Report* — organized by
   dimension/cluster (not a flat list), synthesis body ≤2 pages, every claim
   traceable to a curated resource (QR-4). Never introduce a fact not in the
   Full Report / manifest (QR-6). Then **append the mandatory Cluster profiles
   section** (after the `<!-- CLUSTER PROFILES -->` marker): for each cluster,
   select the **top-3 representative papers** (the most exemplary curated
   members — usually the highest-relevance, tie-broken by how much the
   synthesis leans on them; fewer only if the cluster is smaller), reproduce
   each one's full extraction (summary + all rubric dimensions) from the Full
   Report / manifest, then **list every other curated paper in that cluster**
   (title, `[id]`, half-line on what it adds). There is no separate appendix.
   The profiles are reference material and are excluded from the 2-page limit;
   build them mechanically from the manifest so values can't drift.
   See `references/report-templates.md`.

10. **Finalize the 2-pager deliverable.** Once the 2-pager passes the
    self-check, run the finalize helper. It (a) copies the local PDF of every
    resource cited in the 2-pager into `{theme}/curated-papers/` so the evidence
    travels with the report, and (b) renders the 2-pager (synthesis + cluster
    profiles) to `{theme}/two_pager.pdf`:
    ```bash
    python scripts/finalize_two_pager.py {theme}/manifest.json --two-pager two_pager.md
    ```
    It only reads the manifest and writes under the theme dir (contract-safe).
    Metadata-only cited resources have no PDF to copy and are reported, not
    invented. If no PDF backend is installed it says so (`pip install xhtml2pdf`).

11. **(Optional) Generate the Final Report** — a decision-maker-facing technical
    assessment synthesized *from* the finished Full Report + 2-pager, when the
    user wants a program/leadership deliverable (not just an analyst synthesis).
    Write it to `{theme}/final_report.md` following
    `references/final-report-template.md`. It is **derived, not re-researched**:
    take the argument from the 2-pager, the evidence from the Full Report /
    manifest, introduce **no new facts** (QR-6), and cite only `curated`
    resources (QR-7). Key differences from the other two reports: it is bulleted
    throughout, ends every top-level section with a bold **Key Take-away:** /
    **Section main point:**, is framed for a decision-maker (opportunity,
    maturity gap, risks, oversight), and uses **IEEE-numbered citations** — cite
    the 10–25-resource subset that carries the argument (not the whole corpus),
    numbered in order of first appearance, with a full **References** section
    built from manifest fields only. Keep the canonical-id → number mapping
    auditable so it traces back to the manifest and the other reports.

Before declaring done, run the self-check in "Acceptance self-check".

## Workflow — Update mode

The point of Update is to preserve prior curation and surface only what changed.

1. **Invoke the tool with `--update`.** It fetches only new canonical IDs and
   never touches your prior judgment fields. The easiest way to re-run *every*
   query the theme was built from is `{theme}/collect_update.sh` — a
   re-runnable batch script stored with the outputs. If it doesn't exist yet
   (or new queries have been run since), regenerate it from the manifest's
   recorded runs:
   ```bash
   python scripts/make_update_script.py {theme}/manifest.json --mailto you@example.com
   ```
2. **Score new records only.** Resources whose `status` is already `curated` /
   `dropped` keep their decisions — do not re-litigate them unless their
   objective content actually changed (the tool can change `cross_links`; that
   may warrant a re-look, nothing else).
3. **Re-cluster only if needed.** If new resources form a new theme, add a
   cluster; otherwise slot them into existing ones. Avoid renumbering stable
   clusters — it makes deltas unreadable.
4. **Persist** new decisions via `apply_curation.py` (it merges, never clobbers).
5. **Regenerate both reports** (including the 2-pager cluster profiles —
   re-confirm each cluster's top-3 representative papers, changing them only
   if a new resource clearly supersedes one), then **re-run
   `finalize_two_pager.py`** so `curated-papers/` and `two_pager.pdf` reflect
   the updated citations. If a `final_report.md` exists, regenerate it too from
   the updated Full Report + 2-pager, and re-check that its numbered citations
   still resolve (new evidence may add references or shift what a claim cites).
6. **Produce a delta block**: explicitly list **added** (new curated),
   **dropped** (newly dropped), and **changed-by-dimension** (curated resources
   whose dimension values you revised, with old → new). This is QR-5; see the
   delta template in `references/report-templates.md`.

## Invoking the tool

The Phase A tool is a CLI + importable package. Typical calls:

```bash
# create
python -m landscape collect --theme "GeoAI FMs" --query "geospatial foundation model" \
    --since 2023-01 --sources arxiv,github,openalex --mailto you@example.com

# update
python -m landscape collect --theme "GeoAI FMs" --query "geospatial foundation model" \
    --since 2023-01 --sources arxiv,github,openalex --update
```

It prints a JSON run summary (counts: queried/new/duplicate/downloaded/
metadata_only). Use those counts to frame the run for the user. If a source
errored, the summary says so — report partial coverage honestly rather than
implying completeness.

Every executed query is recorded durably in the manifest (`runs[]` stores each
source's `query_string`, date window, and result count; each resource stores
`query_that_found_it`). After a Create-mode collection batch, generate
`{theme}/collect_update.sh` with `scripts/make_update_script.py` so the full
keyword strategy lives with the outputs and periodic updates are one command.

## Writing decisions back: the decisions file

`apply_curation.py` consumes a small JSON keyed by canonical `id`. Only these
keys are honored; anything else is ignored, so you physically cannot corrupt an
objective field:

```json
{
  "arXiv:2301.00001": {
    "status": "curated",
    "relevance_score": 0.92,
    "relevance_rationale": "Pretrained ViT on Sentinel-2; squarely on-theme.",
    "dimensions": {"Modality": "satellite (S2)", "Params": "not stated"},
    "cluster_id": "vision-fm"
  },
  "github:org/repo": { "status": "dropped", "relevance_score": 0.1,
    "relevance_rationale": "Generic ML utils, not a geospatial FM." }
}
```

The script validates `status` ∈ {curated, dropped, raw}, requires a rationale for
any non-raw decision, and writes atomically. Read its `--help` for options.

## Acceptance self-check (QR-1 … QR-6)

Run the checker, then eyeball what it can't measure:

```bash
python scripts/check_reports.py {theme}/manifest.json \
    --full-report full_report.md --two-pager two_pager.md
```

It verifies the mechanical criteria — every curated resource has all rubric
dimensions populated or `"not stated"` (QR-2); the Full Report covers every
curated resource with a consistent dimension set (QR-3); the 2-pager is ≤2 pages
and references only ids/titles present in the manifest (QR-4, QR-6). You still
judge the things a script can't: are rationales sound, are clusters coherent, is
the synthesis actually insightful. Fix issues before delivering.

The checker covers the two core reports. If you also produced a `final_report.md`,
run the **Final Report honesty self-check** in `references/final-report-template.md`
(no new facts vs. the manifest, PDF-grounded citations only, every `[n]` resolves
and is used, numbering monotonic by first appearance, balanced framing, each
section ends with its Key Take-away / Section main point).

## Honesty constraints

- **No fabrication.** Every resource, metric, author, venue, or citation in a
  report must exist in the manifest. If a number isn't there, it's `"not stated"`.
- **PDF-grounded reports only (QR-7).** Resources without a PDF
  (`pdf_available: false`) are never curated and never referenced in the
  Full Report body or the 2-pager — they appear only in the Dropped list, with
  an availability rationale. If exclusions materially thin the coverage, say so
  in the reports (e.g. a gaps bullet) rather than implying completeness.
- **Surface uncertainty.** A low-confidence keep/drop or a thin abstract is worth
  a one-clause caveat, not silent confidence.

## Bundled resources

- `references/manifest-contract.md` — field ownership + schema (read first).
- `references/curation-guide.md` — relevance scoring + rationale style.
- `references/dimension-rubric.md` — choosing dimensions; example rubrics for the
  two test themes (GeoAI FMs, Agents for Science).
- `references/report-templates.md` — Full Report, 2-pager, and delta templates.
- `references/final-report-template.md` — the optional decision-maker Final
  Report: conventions, annotated skeleton, generation-from-the-two-reports
  procedure, IEEE citation-numbering rules, and honesty self-check.
- `scripts/set_dimensions.py` — write the agent-owned rubric to the manifest.
- `scripts/apply_curation.py` — merge judgment fields back (contract-safe).
- `scripts/check_reports.py` — mechanical QR checks.
- `scripts/finalize_two_pager.py` — copy cited papers' PDFs into
  `{theme}/curated-papers/` and render `{theme}/two_pager.pdf`.
- `scripts/make_update_script.py` — generate `{theme}/collect_update.sh` from
  the queries recorded in the manifest, for periodic re-collection.
- `evals/` — gold sets + scoring harness for QR-1…QR-6 (see `evals/README.md`).
