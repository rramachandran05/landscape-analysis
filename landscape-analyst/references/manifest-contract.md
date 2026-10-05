# The manifest contract — field ownership

`{theme}/manifest.json` is the single source of truth shared between the
collection tool (Phase A) and you (Phase B). The split below is the whole game:
**the tool writes objective fields; you write judgment fields; neither side
overwrites the other.** Update mode relies on it — if you scribble on objective
fields, a re-collection can't safely reconcile, and if the tool touched your
fields, your curation would evaporate on every update.

## Theme level

| field | owner | notes |
|-------|-------|-------|
| `manifest_version`, `theme`, `description` | tool | description is objective; you may *propose* better wording but the tool persists it |
| `dimensions` | **you** | the rubric: a list of `{name, description}`. Set it with `set_dimensions.py` |
| `created`, `last_updated` | tool | timestamps |
| `runs[]` | tool | append-only run log (run_id, timestamp, mode, per-source query/window/counts/status) |

## Resource level

Each entry in `resources[]`:

**Tool-owned (objective) — read these, never write them:**
`id` (canonical), `source`, `source_native_id`, `title`, `authors[]`, `year`,
`venue_or_repo`, `abstract`, `url`, `doi`, `arxiv_id`, `retrieved_on`,
`run_id_first_seen`, `query_that_found_it`, `bibtex`, `pdf_available`,
`local_path`, `cross_links[]`.

**Agent-owned (judgment) — these are yours:**

| field | type | meaning |
|-------|------|---------|
| `status` | `raw` \| `curated` \| `dropped` | `raw` = tool just collected it, undecided. You move it to `curated` or `dropped` |
| `relevance_score` | float 0–1 | your confidence it belongs in the analysis |
| `relevance_rationale` | string | one line; *why* kept or dropped. Required for any non-`raw` status |
| `dimensions` | object | rubric dimension name → value, or the literal `"not stated"` |
| `cluster_id` | string | grouping key; related resources share one |

## Canonical IDs

`id` is type-prefixed and stable: `arXiv:2301.00001`, `doi:10.1145/x`,
`github:owner/repo`, or `<source>:<native>`. Use it as the key when writing
decisions. `cross_links[]` lists the canonical ids of the *same artifact*
elsewhere (e.g. an arXiv preprint and its published DOI) — treat cross-linked
records as one work when curating, and avoid double-counting them in reports.

## Practical implications

- **Read fully, write narrowly.** You consume the whole record but only ever
  emit the five judgment fields (plus theme-level `dimensions`).
- **`raw` is your TODO list.** Anything still `raw` after a run is uncurated.
- **Dropped ≠ deleted.** Dropped resources stay in the manifest (with your
  rationale) so Update can see they were considered and rejected.
- **Trust objective fields; flag, don't fix.** If a title is mangled or a DOI is
  wrong, note it for a tool fix — editing it here breaks the contract.
