# Dimension rubric — choosing the lens

Dimensions are the columns every curated resource is scored on. They are the
backbone of both reports: the Full Report is a table over them, and the 2-pager
is *organized by* them. A good rubric makes resources comparable at a glance and
makes gaps visible ("nobody reports parameter counts").

## What makes a good dimension

- **Discriminating** — resources actually differ on it. "Is it about ML?" is
  useless if everything is; "Pretraining objective" separates MAE from
  contrastive from supervised.
- **Extractable** — answerable from an abstract/README most of the time.
  Otherwise you'll write `"not stated"` everywhere and learn nothing.
- **Orthogonal** — each dimension carries distinct information; avoid two columns
  that always co-vary.
- **Stable** — the same set applies across the whole theme and survives Updates.
  Adding a dimension mid-stream forces re-curation of everything.

Aim for **5–8 dimensions**. Fewer loses signal; more turns the table into a
spreadsheet nobody reads. Always include a couple that capture *what kind of
contribution* it is (e.g. method vs. benchmark vs. application) and *openness*
(weights/code/data available?), since those drive a landscape's usefulness.

## Writing the rubric to the manifest

Each dimension is `{ "name": ..., "description": ... }`. The description tells
future-you (and the gold set) exactly what value the column should hold:

```json
[
  {"name": "Modality", "description": "Input data type(s): optical, SAR, multispectral, vector, etc."},
  {"name": "Pretraining objective", "description": "MAE / contrastive / supervised / multi-task / n.a."},
  {"name": "Scale", "description": "Parameter count and/or pretraining dataset size if stated."},
  {"name": "Evaluation", "description": "Downstream tasks / benchmarks used to validate."},
  {"name": "Openness", "description": "Are weights / code / data released? note which."},
  {"name": "Contribution type", "description": "model | benchmark | survey | application | toolkit."}
]
```

Persist with `python scripts/set_dimensions.py {theme}/manifest.json dimensions.json`.

## Example rubric — GeoAI Foundation Models

| dimension | what to record |
|-----------|----------------|
| Modality | optical / SAR / multispectral / hyperspectral / vector / multi |
| Pretraining objective | MAE, contrastive (e.g. DINO/SimCLR), supervised, multi-task, n.a. |
| Scale | params + pretraining corpus size if stated, else "not stated" |
| Spatial/temporal handling | how it treats resolution, geolocation, time series |
| Evaluation | downstream tasks/benchmarks (segmentation, classification, change detection…) |
| Openness | weights / code / data release status |
| Contribution type | model / benchmark / survey / application / toolkit |

## Example rubric — Agents for Science

| dimension | what to record |
|-----------|----------------|
| Scientific domain | biology, chemistry, materials, physics, general… |
| Agent architecture | single-agent, multi-agent, tool-augmented LLM, RL, etc. |
| Autonomy level | assistive / human-in-the-loop / fully autonomous |
| Capabilities | hypothesis gen, experiment design, lab control, literature synthesis… |
| Evaluation | benchmark, real wet-lab, simulation, case study |
| Openness | code / weights / data / environment released? |
| Contribution type | system / benchmark / survey / position / application |

## Filling values during curation

For each curated resource, write one value per dimension. Use `"not stated"`
(the literal string) when the source doesn't say — this is itself a finding
(it tells the 2-pager "openness is rarely reported"). Keep values terse and
comparable (a few words), not prose; the per-resource summary in the Full Report
is where nuance goes.
