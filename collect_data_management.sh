#!/usr/bin/env bash
#
# collect_data_management.sh
# ---------------------------------------------------------------------------
# Phase A collection batch for the theme "AI Agents for Data Management".
#
# HOW IT WORKS
#   The tool sends exactly ONE query string to each source per run. To cover a
#   broad keyword strategy we make many runs into the SAME theme manifest: the
#   first run CREATES it, every later run uses --update to merge only new
#   canonical IDs (dedup/cross-link is automatic, agent curation is preserved).
#   Re-running the whole script is safe — if the manifest already exists, every
#   run is an --update and nothing already downloaded is fetched again.
#
# ANCHOR (this theme's bridge term)
#   ("AI agent" OR "LLM agent" OR agentic OR "multi-agent" OR automated OR automation)
#   automated/automation are folded into the agent axis on purpose: for data
#   management that's the bridge term that catches pre-LLM precedent work.
#   The anchor has NO domain clause, so it is ALWAYS ANDed with a per-stage net
#   below — there is deliberately no bare "anchor-only" run (it would flood with
#   generic automation papers). Self-precise terms (maDMP, PROV-O) run bare.
#
# QUERY SYNTAX NOTE
#   The boolean form  (A OR B) AND (C OR D)  is fully honored only by arXiv.
#   OpenAlex treats the same string as a loose relevance search (still useful
#   for recall; its date filter is applied server-side). A source that dislikes
#   a query is logged and skipped — it never aborts the batch. GitHub code
#   search uses different qualifiers, so it is left out by default (see the
#   optional block at the bottom). Every query is SINGLE-quoted so the shell
#   never glob-expands the parentheses or splits on the spaces/double-quotes.
#
# USAGE
#   chmod +x collect_data_management.sh
#   ./collect_data_management.sh
#   # override any setting inline, e.g.:
#   MAX_RESULTS=40 SINCE=2018-01 SOURCES=arxiv ./collect_data_management.sh
# ---------------------------------------------------------------------------

set -uo pipefail   # NOT -e: a single failed run should not kill the batch.

# ----- Config (override via environment) -----------------------------------
THEME="${THEME:-AI Agents for Data Management}"
DESCRIPTION="${DESCRIPTION:-AI/LLM agents and automation across the data-management lifecycle: data-management planning, ingest/onboarding, curation, metadata management, data quality, provenance/lineage, and governance/compliance.}"
SOURCES="${SOURCES:-arxiv,openalex}"     # add ,semanticscholar (needs S2_API_KEY for good limits)
SINCE="${SINCE:-2015-01}"                # wide: captures pre-LLM automation precedent
UNTIL="${UNTIL:-}"                       # optional YYYY[-MM[-DD]]
MAX_RESULTS="${MAX_RESULTS:-75}"         # per source PER run; lower = politer/faster/less disk
BASE_DIR="${BASE_DIR:-./data}"
MAILTO="${MAILTO:-rramachandran05@gmail.com}"

# ----- Derived: manifest path (mirrors the tool's slugify) ------------------
SLUG="$(printf '%s' "$THEME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
MANIFEST="$BASE_DIR/$SLUG/manifest.json"

if [[ -f "$MANIFEST" ]]; then
  MODE_FLAG="--update"     # manifest already exists -> every run merges
  echo "Manifest exists ($MANIFEST) — all runs will --update."
else
  MODE_FLAG=""             # first run creates; run() flips this to --update after
  echo "No manifest yet — first run creates, the rest --update."
fi

# ----- Runner ---------------------------------------------------------------
run() {
  local label="$1" query="$2"
  echo ""
  echo "=================================================================="
  echo ">>> [$label] ${MODE_FLAG:-create}"
  echo "    query: $query"
  echo "=================================================================="
  python -m landscape collect \
    --theme "$THEME" \
    --description "$DESCRIPTION" \
    --query "$query" \
    --since "$SINCE" \
    ${UNTIL:+--until "$UNTIL"} \
    --sources "$SOURCES" \
    --max-results "$MAX_RESULTS" \
    --base-dir "$BASE_DIR" \
    --mailto "$MAILTO" \
    $MODE_FLAG \
    || echo "!! [$label] run returned non-zero — continuing with next group."
  MODE_FLAG="--update"     # after the first run, always merge
}

# ===========================================================================
# Anchor reused by every generic group:
ANCHOR='("AI agent" OR "LLM agent" OR agentic OR "multi-agent" OR automated OR automation)'
# (kept as a comment for reference; queries below spell it out so each line is
#  copy-pasteable on its own.)
# ===========================================================================

# 1) Data planning (anchored)
run "data-planning" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent" OR automated OR automation) AND ("data management plan" OR DMP OR "machine-actionable DMP" OR maDMP OR "metadata requirements" OR "data policy compliance" OR "funder requirements")'

# 1b) maDMP (self-precise — run bare)
run "madmp-bare" \
'("machine-actionable DMP" OR maDMP OR "machine-actionable data management plan")'

# 2) Ingest / onboarding (anchored)
run "ingest-onboarding" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent" OR automated OR automation) AND ("format detection" OR "file format identification" OR "submission validation" OR "data ingestion" OR "metadata extraction" OR "automated intake" OR "deposit workflow")'

# 3) Curation (anchored)
run "curation" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent" OR automated OR automation) AND ("data curation" OR "digital curation" OR "field normalization" OR "vocabulary mapping" OR crosswalk OR "metadata enrichment" OR "record completeness" OR "data cleaning")'

# 4) Metadata management (anchored)
run "metadata-management" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent" OR automated OR automation) AND ("metadata generation" OR "automated metadata" OR "keyword extraction" OR "ontology mapping" OR "ontology term assignment" OR "semantic annotation" OR "schema validation" OR "metadata quality")'

# 5) Data quality (anchored)
run "data-quality" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent" OR automated OR automation) AND ("data profiling" OR "anomaly detection" OR "outlier detection" OR "missing value" OR "missing data" OR "unit validation" OR "range checking" OR "data validation" OR "data quality assessment")'

# 6) Provenance / lineage (anchored)
run "provenance-lineage" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent" OR automated OR automation) AND (provenance OR "data lineage" OR "workflow provenance" OR "W3C PROV" OR "PROV-O" OR "derived data" OR "transformation capture" OR "workflow reconstruction")'

# 6b) PROV-O / W3C PROV (self-precise — run bare)
run "prov-o-bare" \
'("PROV-O" OR "W3C PROV")'

# 7) Governance / compliance (anchored)
#    NOTE: your message was truncated right at "Governance / compliance", so this
#    net is INFERRED for data management — edit the terms below to match your list.
run "governance-compliance" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent" OR automated OR automation) AND ("data governance" OR "data stewardship" OR "regulatory compliance" OR "access control" OR "data privacy" OR "data protection" OR "policy compliance" OR "data sharing agreement" OR "data retention")'

# ===========================================================================
# OPTIONAL: GitHub for the code-heavy slice (validators, metadata extractors,
# provenance tooling). GitHub code search uses its own qualifiers, not the
# boolean above. Uncomment and adapt:
#
# SOURCES="github" run "github-metadata-tools" \
#   'metadata extraction validation data language:python'
# SOURCES="github" run "github-provenance" \
#   'data provenance lineage PROV'
#
# (run() reads $SOURCES at call time, so prefixing the var scopes it to that call.)
# ===========================================================================

echo ""
echo "=================================================================="
echo "Done. Manifest: $MANIFEST"
echo "Inspect:   python -c \"import json;m=json.load(open('$MANIFEST'));print(len(m['resources']),'resources')\""
echo "Next (Phase B): curate with the landscape-analyst skill."
echo "=================================================================="
