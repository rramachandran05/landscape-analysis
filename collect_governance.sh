#!/usr/bin/env bash
#
# collect_governance.sh
# ---------------------------------------------------------------------------
# Phase A collection batch for the theme "AI Agents for Science Governance".
#
# HOW IT WORKS
#   The tool sends exactly ONE query string to each source per run. To cover a
#   broad keyword strategy we therefore make many runs into the SAME theme
#   manifest: the first run CREATES it, every later run uses --update to merge
#   only new canonical IDs (dedup/cross-link is automatic, agent curation is
#   preserved). Re-running this whole script is safe — if the manifest already
#   exists, every run is an --update.
#
# QUERY SYNTAX NOTE
#   The boolean form  (A OR B) AND (C OR D)  is fully honored only by arXiv.
#   OpenAlex treats the same string as a loose relevance search (still useful
#   for recall; its date filter is applied server-side). A source that dislikes
#   a query is logged and skipped — it never aborts the batch. GitHub code
#   search uses different qualifiers, so it is left out by default (see the
#   optional block at the bottom).
#
#   Every query below is wrapped in SINGLE quotes so zsh/bash never tries to
#   glob-expand the parentheses or split on the spaces/double-quotes inside.
#
# USAGE
#   chmod +x collect_governance.sh
#   ./collect_governance.sh
#   # override any setting inline, e.g.:
#   MAX_RESULTS=50 SOURCES=arxiv ./collect_governance.sh
# ---------------------------------------------------------------------------

set -uo pipefail   # NOT -e: a single failed run should not kill the batch.

# ----- Config (override via environment) -----------------------------------
THEME="${THEME:-AI Agents for Science Governance}"
DESCRIPTION="${DESCRIPTION:-AI/LLM agents in scientific workflows and the governance, standards, open-science principles, engineering practices, registries/protocols, documentation artifacts, evaluation, disclosure/authorship, and human-oversight literature around them.}"
SOURCES="${SOURCES:-arxiv,openalex}"     # add ,semanticscholar (needs S2_API_KEY for good limits)
SINCE="${SINCE:-2023-01}"
UNTIL="${UNTIL:-}"                       # optional YYYY[-MM[-DD]]
MAX_RESULTS="${MAX_RESULTS:-100}"        # per source PER run; lower = politer/faster
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
# Anchor used by generic groups:
#   ("AI agent" OR "LLM agent" OR agentic OR "multi-agent")
#   AND (science OR "scientific discovery" OR "scientific research")
# Self-precise groups (FAIR, protocols, cards, disclosure, policy) use a lighter
# context so their specific terms aren't over-filtered.
# ===========================================================================

# 0) Broad anchor base
run "anchor-base" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent") AND (science OR "scientific discovery" OR "scientific research")'

# 1) Guidance / standards genre
run "guidance-standards" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent") AND (science OR "scientific discovery" OR "scientific research") AND ("best practices" OR guidelines OR "community guidance" OR "community standards" OR recommendations OR "position paper" OR principles OR framework)'

# 2a) Open-science principles (generic — anchored)
run "open-science" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent") AND (science OR "scientific discovery" OR "scientific research") AND (reproducibility OR replicability OR "reproducible research" OR transparency OR accountability OR "research integrity" OR "open science" OR interoperability OR accessibility)'

# 2b) FAIR family (self-precise — light context)
run "fair-principles" \
'("FAIR principles" OR FAIR4RS OR "FAIR for Research Software" OR "FAIR for AI") AND (science OR "research software" OR agent OR data)'

# 3) Prompt -> systematic agent engineering (anchored)
run "agent-engineering" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent") AND (science OR "scientific discovery" OR "scientific research") AND ("prompt engineering" OR "agent engineering" OR "software engineering for AI agents" OR reusability OR modularity OR maintainability OR "reusable agents")'

# 4) Agent architectures (anchored)
run "agent-architectures" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent") AND (science OR "scientific discovery" OR "scientific research") AND ("single-agent" OR "tool use" OR "tool-augmented" OR "function calling" OR "tool learning" OR ReAct OR "multi-agent systems" OR "agent orchestration" OR "agentic workflows" OR "LLM multi-agent")'

# 5a) Registries / hubs / sharing (self-precise — light context)
run "registries-hubs" \
'("agent registry" OR "agent hub" OR "agent marketplace" OR "model registry" OR "model hub" OR "model zoo" OR "agent sharing") AND (science OR "scientific research" OR agent OR LLM)'

# 5b) Interoperability protocols (self-precise — light context)
run "protocols" \
'("Model Context Protocol" OR MCP OR "Agent2Agent" OR A2A OR "agent interoperability") AND (agent OR science OR scientific OR tool)'

# 6) Documentation artifacts: cards, logs, provenance, repro artifacts (self-precise)
run "documentation-artifacts" \
'("model cards" OR "system cards" OR "agent cards" OR "data cards" OR "datasheets for datasets" OR "reproducibility artifacts" OR "artifact evaluation" OR "research artifacts" OR provenance OR "execution traces" OR "agent logging") AND (agent OR science OR "machine learning" OR research)'

# 7) Evaluation / benchmarking (anchored)
run "evaluation-benchmarking" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent") AND (science OR "scientific discovery" OR "scientific research") AND ("agent evaluation" OR "agent benchmark" OR "benchmarking LLM agents" OR "evaluation framework" OR "scientific agent benchmark" OR reliability OR validation)'

# 8) Disclosure / citation / authorship (self-precise — light context)
run "disclosure-authorship" \
'("AI disclosure" OR "disclosure of AI use" OR "AI authorship" OR "citing generative AI" OR "AI use policy" OR attribution) AND (science OR research OR scientific OR academic)'

# 9a) Governance / responsible use / stewardship (anchored)
run "governance-responsible" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent") AND (science OR "scientific discovery" OR "scientific research") AND ("AI governance" OR "responsible AI" OR "trustworthy AI" OR "data governance" OR "data stewardship" OR "research software engineering")'

# 9b) Restricted-data / policy clause (policy-flavored — arXiv coverage is thin;
#     OpenAlex/journals more likely to surface these)
run "restricted-data-policy" \
'("data sovereignty" OR "export control" OR "restricted data governance") AND (AI OR agent OR research OR science)'

# 10) Human oversight & autonomy (anchored)
run "human-oversight" \
'("AI agent" OR "LLM agent" OR agentic OR "multi-agent") AND (science OR "scientific discovery" OR "scientific research") AND ("human-in-the-loop" OR HITL OR "human oversight" OR "human-AI collaboration" OR "human-AI teaming" OR "levels of autonomy" OR "AI accountability")'

# ===========================================================================
# OPTIONAL: add GitHub for the code-heavy slice (registries, MCP/A2A, harnesses).
# GitHub code search uses its own qualifiers, not the boolean above. Uncomment:
#
# SOURCES="github" run "github-protocols" \
#   'model context protocol agent science language:python'
# SOURCES="github" run "github-registries" \
#   'agent registry OR agent hub scientific'
#
# (run() reads $SOURCES at call time, so prefixing the var scopes it to that call.)
# ===========================================================================

echo ""
echo "=================================================================="
echo "Done. Manifest: $MANIFEST"
echo "Inspect:   python -c \"import json;m=json.load(open('$MANIFEST'));print(len(m['resources']),'resources')\""
echo "Next (Phase B): curate with the landscape-analyst skill."
echo "=================================================================="
