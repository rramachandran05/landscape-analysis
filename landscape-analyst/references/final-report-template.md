# Final Report template

The **Final Report** is the third, optional deliverable: a decision-maker-facing
**technical assessment** synthesized *from* the already-finished Full Report and
2-pager. Where the Full Report is the exhaustive per-resource record and the
2-pager is a dense analyst synthesis, the Final Report is written for a
**program/leadership audience** deciding *what to do about the field* — where it
adds value, what it can't yet be trusted to do, and how to adopt it responsibly.

It introduces **no new facts**: every claim must already be supported in the Full
Report / manifest (QR-6), and it stays **PDF-grounded** (QR-7) — it only ever
cites resources that were `curated`. What it adds over the 2-pager is *framing
and judgment for a reader who will act on it*, plus a clean numbered reference
list instead of canonical manifest ids.

The worked exemplar this template is modeled on is the "AI Agents for the NASA
Science Enterprise" assessment (`data/agents4science/`): Full Report + 2-pager →
a bulleted, cited program assessment.

---

## Defining conventions (what makes it a *Final Report*, not a longer 2-pager)

1. **Audience is a decision-maker, not an analyst.** Frame everything around
   consequences, adoption posture, and oversight — "what should a program manager
   do with this," not "here is the taxonomy."
2. **Bulleted throughout.** The body is bullets, not prose paragraphs. Bold
   lead-ins for enumerated capabilities/categories/risks
   (e.g. **Provenance and artifact management** — …).
3. **Every major section ends with a one-sentence bold summary.** Use
   **Key Take-away:** for the Executive Summary and Purpose/Scope sections, and
   **Section main point:** for every other top-level section. This is the
   skimmable spine of the document.
4. **IEEE-numbered citations, not canonical ids.** The body cites `[1]`, `[2]`,
   grouped as `[1]–[3]`, and ends with a numbered **References** section carrying
   full bibliographic entries. Numbers are assigned in **order of first
   appearance**. (The 2-pager and Full Report keep canonical ids like
   `[arXiv:2408.06292]`; the Final Report translates the cited subset into a
   clean numbered list — see "Citation numbering," below.)
5. **Cite the subset that carries the argument, not the whole corpus.** A Final
   Report cites the representative systems plus the specific papers backing
   load-bearing quantitative claims — typically 10–25 references, not all N
   curated. Breadth lives in the Full Report; the Final Report earns each
   citation.
6. **Grounded and honest.** No number, system, or claim that isn't in the
   manifest / Full Report. Surface gaps and uncertainty explicitly (an
   underrepresented capability, an evaluation the corpus can't support) rather
   than implying completeness.

---

## Annotated section skeleton

The section arc below is the recommended default (it is the NASA exemplar's
structure). Keep the spine — Executive Summary → Scope/Method → Define the domain
→ Landscape → Capability assessment → Evaluation & maturity → Risks →
Implications for {org} → Conclusion → References — and adapt section *titles* to
the theme. Sub-section names in `### ` are illustrative; drive them from the
actual clusters/capabilities in the Full Report.

```markdown
# {Topic} for the {Organization / Enterprise}

## Technical Assessment for {Audience}
*{One-line status/provenance tagline, italic — e.g. "Condensed assessment,
citations grounded in the reviewed corpus."}*

## Executive Summary
- {6–10 bullets that stand alone: what the field is, the diverse approaches
  (cite exemplars [1]–[3]), the central capability, the central limitation,
  the strongest quantitative evidence for the headline judgment [n], the
  uneven-maturity picture, the human-oversight requirement, the risk beyond the
  obvious, and the near-term posture for {audience}.}
**Key Take-away:** {one sentence — the single thing the reader must remember.}

## Purpose, Scope, and Review Method
- {Who it's for and what decision it supports; that it assesses the landscape,
  not an implementation plan.}
- {Time window and what the window captures [4].}
- {Scope boundary — what counts as in-scope vs excluded.}
- {How the corpus was built: honestly disclose the collection + curation method
  (AI-assisted, PDF-grounded, N of M curated), and that expert judgment selected
  representative systems. This mirrors the report's own provenance ethic.}
- {What evidence forms were weighed; that a demo ≠ repeatable performance.}
- {Limitations of the evidence base.}
**Key Take-away:** {one sentence on what this report is and isn't.}

## Defining {the domain concept}
- {Working definition; what the key term does and does not imply.}
- {Distinctions from adjacent things.}

### Major {X} Capabilities
- **{Capability}** — {one-line characterization; risk or caveat} [n].
- ... (bold-lead bullets, one per capability) ...

### Operational Categories of {X}
- **{Category}** — {what it does; its dominant dependency/risk} [n].
- ...
**Section main point:** {one sentence.}

## Technical Landscape and Representative Architectures
- {The N broad architectural patterns, each with an exemplar cite [n].}
- {Common components shared across architectures.}

### {Representative system / pattern 1}
- {What it is and what it demonstrates} [n].
- {Its documented failure modes / limits} [n].

### {Representative system / pattern 2}
...
**Section main point:** {one sentence.}

## Capability Assessment Across the {Workflow / Domain}
- {The organizing claim: capability is uneven; strongest where …, weakest where …}

### {Capability area 1}
- {What agents/systems can do here; where it's defensible; where it fails} [n].
- {What {org}-relevant use looks like, and its guardrails.}

### {Capability area 2}
...
**Section main point:** {one sentence.}

## Evaluation Evidence and Maturity Assessment
- {The evaluation dimensions this report judges against (e.g. technical
  performance / scientific quality / operational evidence).}
- {The maturity ladder used — define it as a report-local descriptive framework,
  not a certification scheme. Exemplar used exploratory → emerging →
  conditionally supportable → operationally supported.}

### Evidence from {category}
- {Concrete, cited evidence — the quantitative results that anchor the
  judgments} [n].

### Evaluation Gaps
- {What the corpus is thin on; what claims are therefore under-supported.}

### Overall Maturity Assessment
- **{Capability area}** — **{maturity level}**, {one-clause condition} [n].
- ...
**Section main point:** {one sentence.}

## Cross-Cutting Risks and Failure Modes
- {The dominant risk framed once, up top.}
- **{Risk class}** — {how it manifests; what control addresses it} [n].
- ... (bold-lead risk bullets) ...
**Section main point:** {one sentence.}

## Implications for the {Organization}
- {Why this matters to {org} specifically; the opportunity and the concern.}

### {Implication area — e.g. Integrity & Accountability}
- ...
### {Implication area — e.g. Provenance & Reproducibility}
- ...
### Differentiating Appropriate Uses
- **Lower-consequence** uses — {observable, reversible, inspectable} …
- **Higher-consequence** uses — {not supported by current evidence} [n]–[n].
### Enabling Responsible Use
- ...
**Section main point:** {one sentence.}

## Conclusion
- {5–8 bullets restating the arc: what the field can do, the maturity gap, the
  pivotal control point, the oversight standard, the posture for {audience}.}
**Section main point:** {one sentence.}

## References
[1] {Author(s), "Title," venue / arXiv id, year, doi.}
[2] ...
```

---

## How to generate it (from the Full Report + 2-pager)

The Final Report is **derived, not re-researched**. Produce it only after the
Full Report and 2-pager are final.

1. **Take the argument from the 2-pager.** The shape-of-the-field paragraph,
   by-dimension synthesis, gaps, and read-first shortlist already contain the
   judgments. The Final Report re-expresses them for a decision-maker and adds
   the Risks / Implications-for-{org} framing.
2. **Take the evidence from the Full Report / manifest.** Every quantitative
   claim (benchmark scores, failure rates, evaluation numbers) must trace to a
   curated resource's entry. Do not restate a number that isn't there.
3. **Select the citation subset.** Cite the representative systems (one per
   architectural pattern / cluster) plus the specific papers backing each
   load-bearing claim. Aim for 10–25 references; breadth stays in the Full
   Report.
4. **Assign section main points last.** Write each section, then distill its
   one-sentence summary.
5. **Self-check against the honesty constraints** before delivering (see below).

### Citation numbering

The Final Report translates canonical manifest ids into a clean IEEE list:

- Assign `[1], [2], …` in **order of first appearance** in the body.
- Give the **core representative systems the low numbers** (they appear first and
  are cited most); append **supporting papers** in the order their claims first
  appear. In the exemplar this produced 9 core + 11 supporting = 20, with the
  supporting refs [10]–[20] cited monotonically.
- Build each **References** entry from manifest objective fields only — authors,
  title, venue or `arXiv:id`, year, doi. Never invent bibliographic detail.
- Keep the mapping auditable: if useful, record a `final_report_citation_map`
  (canonical id → number) alongside the deliverable, or a comment block, so the
  numbered list stays traceable back to the manifest and the other two reports.
- Grouped ranges (`[1]–[3]`, `[7], [8]`) are fine and encouraged for readability.

### Naming & placement

Write to `{theme}/final_report.md` (snake_case, consistent with
`full_report.md` / `two_pager.md`). It is markdown-only by default; if a PDF is
wanted, render it the same way the 2-pager is rendered.

---

## Honesty self-check (Final Report)

Before declaring done, confirm:

- **No new facts.** Every claim, number, system, and citation is present in the
  Full Report / manifest (QR-6). Spot-check each quantitative claim against the
  cited resource's manifest entry.
- **PDF-grounded (QR-7).** Only `curated` resources are cited; nothing
  metadata-only appears in the body or References.
- **Every reference is cited, every citation resolves.** No `[n]` in the body
  without an entry; no entry without at least one inline use; numbering is
  monotonic by first appearance.
- **Framing is balanced.** Where a source reports a favorable result, state it
  before the caveat — don't cherry-pick only the negative (or only the positive).
- **Every top-level section ends with its Key Take-away / Section main point.**
- **Gaps are surfaced**, not papered over — if the corpus can't support a claim
  the audience will care about, say so.
