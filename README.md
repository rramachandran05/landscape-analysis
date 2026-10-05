# Landscape Analysis — Phase A (deterministic collection tool)

The **tool** half of the Landscape Analysis capability. Given a research theme,
it collects scholarly + code artifacts from reproducible structured sources
(arXiv, GitHub, OpenAlex, optionally Semantic Scholar) into a single durable
manifest — the source of truth that the agent layer (Phase B) later curates.

This tool is **deterministic** and does **no judgment**: it writes only
objective fields. Relevance, dimensions, and clustering are agent-owned and are
never created or overwritten here. That field-ownership split is what makes
Update safe and the two phases independently buildable.

## Install

```bash
pip install -e .          # or: pip install -r requirements.txt
```

Python ≥ 3.10. Only runtime dependency is `requests`.

> **Invocation:** all examples below call the tool as a Python module —
> `python -m landscape ...`. This works as soon as the package is importable
> and does not depend on a console script being on your `PATH`. (`pip install -e .`
> also installs a `landscape` console script, but the module form is the
> portable invocation and is what the Phase B skill uses.)

## Usage

```bash
python -m landscape collect \
    --theme "GeoAI FMs" \
    --query "geospatial foundation model" \
    --since 2023-01 \
    --sources arxiv,github,openalex
```

Update an existing theme (fetches only new canonical IDs; preserves all agent
curation):

```bash
python -m landscape collect --theme "GeoAI FMs" --query "geospatial foundation model" \
    --since 2023-01 --sources arxiv,github,openalex --update
```

Key flags:

| flag | meaning |
|------|---------|
| `--theme` | research theme (also the manifest key) |
| `--query` | base query applied to every source |
| `--source-query NAME=QUERY` | per-source query override (repeatable) |
| `--since` / `--until` | date window, `YYYY[-MM[-DD]]` |
| `--sources` | comma list: `arxiv,github,openalex,semanticscholar` |
| `--update` | Update mode (set-difference vs. existing manifest) |
| `--base-dir` | directory holding `{theme}/` and `{theme}-raw/` |
| `--mailto` | contact email for polite API pools (OpenAlex) |
| `--max-results` | cap per source |

Per-source query example:

```bash
python -m landscape collect --theme "GeoAI FMs" \
  --source-query arxiv='abs:"foundation model" AND cat:cs.CV' \
  --source-query github='geospatial foundation model language:python' \
  --since 2023-01 --sources arxiv,github
```

## Querying with multiple keywords

Each source receives **exactly one query string per run**, sent verbatim to its
API. That string *is* the source's native query syntax, so multiple keywords and
boolean operators belong inside it — there is no separate "keyword list" flag.
Three distinct cases:

**1. Multiple keywords / boolean in one `--query`.** Combine terms with the
source's own operators. arXiv supports `AND` / `OR` / `ANDNOT` and field
prefixes (`abs:`, `ti:`, `cat:`); GitHub uses code-search qualifiers
(`language:python`, `stars:>100`); OpenAlex and Semantic Scholar have their own.
Space-separated words use each API's default (arXiv ANDs them).

```bash
# implicit AND across words
python -m landscape collect --theme T --query "geospatial foundation model" --sources arxiv

# explicit boolean + field prefixes
python -m landscape collect --theme T \
  --query 'abs:"foundation model" OR abs:"diffusion model"' --sources arxiv
```

The exact string that surfaced each resource is stored per-resource in
`query_that_found_it`, so you can always trace why something is in the manifest.

**2. A different query per source in one run** — repeat `--source-query`
(keyed by source name); `--query` supplies the default for any source without an
override:

```bash
# --query is the fallback for any source without its own --source-query (here: openalex)
python -m landscape collect --theme "GeoAI FMs" \
  --query "geospatial foundation model" \
  --source-query arxiv='abs:"foundation model" AND cat:cs.CV' \
  --source-query github='geospatial foundation model language:python' \
  --sources arxiv,github,openalex
```

**3. Several *independent* searches against the *same* source.** This is **not**
a single invocation — each source runs once, and a repeated `--query` /
`--source-query NAME=` just overwrites. Two ways to do it:

- **OR them into one string** (when the source supports it):
  `--query 'abs:"foundation model" OR abs:"world model"'`.
- **Run sequentially with `--update`** — the first run creates the manifest, each
  later run merges only new canonical IDs into the same theme and dedups overlaps
  automatically. Each resource keeps the specific query that found it:

  ```bash
  python -m landscape collect --theme "GeoAI FMs" --query "geospatial foundation model" --sources arxiv
  python -m landscape collect --theme "GeoAI FMs" --query "remote sensing pretraining" --sources arxiv --update
  ```

A machine-readable run summary (JSON) is printed to stdout (FR-10):

```json
{
  "run_id": "run-20260101120000-ab12cd34",
  "mode": "create",
  "counts": {"queried": 42, "new": 38, "duplicate": 4, "downloaded": 20, "metadata_only": 18},
  "per_source": [{"source": "arxiv", "result_count": 20, "status": "ok"}],
  "total_resources": 38
}
```

## Importable API

```python
from landscape import DateWindow
from landscape.pipeline import collect

summary = collect(
    theme="Agents for Science",
    queries={"*": "autonomous research agents"},
    date_window=DateWindow(since="2023-01"),
    sources=["arxiv", "openalex"],
    base_dir="./data",
    mode="create",
    mailto="you@example.com",
)
```

## Outputs

```
{base-dir}/
  {theme-slug}/manifest.json     # source of truth
  {theme-slug}-raw/*.pdf         # openly-available PDFs only
  .landscape-cache/              # on-disk HTTP response cache (politeness)
```

## The manifest contract (frozen schema)

`manifest.json` holds theme metadata, an append-only `runs` list, and a
`resources` list. Every resource field is owned by exactly one side:

- **Tool-owned (objective):** `id`, `source`, `source_native_id`, `title`,
  `authors`, `year`, `venue_or_repo`, `abstract`, `url`, `doi`, `arxiv_id`,
  `retrieved_on`, `run_id_first_seen`, `query_that_found_it`, `bibtex`,
  `pdf_available`, `local_path`, `cross_links`.
- **Agent-owned (judgment):** `status`, `relevance_score`,
  `relevance_rationale`, `dimensions`, `cluster_id`. The tool initializes these
  to inert defaults (`status="raw"`) on first sight and **never** touches them
  again — enforced at runtime by `Manifest.assert_no_agent_field_drift`.

Canonical IDs (FR-3) are assigned by precedence: arXiv → DOI → `owner/repo` →
source-native fallback, type-prefixed (`arXiv:`, `doi:`, `github:`).

## Design notes

- **Sources** (`landscape/sources/`): one adapter each, exposing
  `search(query, date_window) -> [RawHit]` and `normalize(RawHit) -> Record`.
- **Dedup** (`landscape/dedup.py`): collapses same-canonical-ID records across
  sources; cross-links only on *shared concrete identifiers* (never fuzzy
  titles) so results stay deterministic.
- **Politeness** (`landscape/http.py`): per-host rate limiting, exponential
  backoff with `Retry-After`, on-disk response cache, contact `User-Agent` /
  `mailto`.
- **Failure handling:** a source outage is logged and skipped (partial run
  recorded); zero results is a valid empty run; a malformed record is skipped,
  not fatal. No paywall circumvention — items without an open PDF stay
  `pdf_available=false`, metadata-only.

Optional API keys (env vars, raise rate limits): `GITHUB_TOKEN`, `S2_API_KEY`.

## Tests

```bash
python -m pytest
```

The suite is fully offline (a fake adapter stands in for the network) and
covers ID normalization, dedup/cross-linking, manifest ownership + the
drift guard, and an end-to-end create → curate → update cycle.

## Scope boundaries

On-demand (not a monitor); named structured sources only (not a web crawler);
English-language v1; convenience cross-links (not citation-graph analytics);
the tool performs no summarization or judgment — that is solely the agent's job.
```
