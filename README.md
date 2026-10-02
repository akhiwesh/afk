# AFK — Revenue Constraint Diagnostic

AFK helps a B2B service founder work out where revenue is getting stuck. The product combines a structured audit with optional invoice, lead, and transaction exports. It produces a primary constraint, the evidence behind each finding, confidence and missing-data notes, and a treatment path that can be checked again later.

The first commercial offer is a founder-led, two-week diagnostic for agencies and consultancies. AFK is an early-stage instrument, not an industry benchmark or a claim of proven revenue uplift. See the [scope of work](docs/SCOPE_OF_WORK.md) for the proposed engagement.

## What the product does

1. **Collects a revenue audit** across demand, qualification, conversion, pricing, retention, and founder dependency.
2. **Accepts business evidence** such as CRM, invoice, and transaction exports when a founder has them.
3. **Computes a diagnosis** with deterministic scoring and impact-weighted constraint ranking. Findings retain their inputs, rule provenance, confidence, and gaps.
4. **Surfaces contradictions** between self-reported answers and uploaded data instead of silently changing the story.
5. **Tracks treatment and later diagnoses** so a founder can see whether the measured constraint moved.

The public offer page includes a **synthetic sample business**. It is a demo of the workflow, not a customer case study.

## Current evidence status

- The knowledge objects and scoring thresholds are **hypotheses**. They have not been calibrated against a sufficient set of observed businesses.
- The case files in [`knowledge/cases`](knowledge/cases) are explicitly synthetic validation fixtures. They exercise the software and do not establish diagnostic accuracy or business outcomes.
- Calibration requires at least **10 distinct cases explicitly marked as observed** (`synthetic: false`). Synthetic and unclassified cases are excluded from that count and from the observed-case agreement mean.
- AFK does not claim guaranteed revenue growth, industry percentile rankings, or validated causal effects. The [validation protocol](knowledge/validation_protocols/AFK-VAL-0001.yaml) records what must be tested.

## Run locally

Requires Python 3.12. From the repository root:

```bash
python run.py
```

The launcher creates a virtual environment, installs [`backend/requirements.txt`](backend/requirements.txt), and starts FastAPI at `http://127.0.0.1:8000`. Open the page and choose **See sample diagnosis** to explore the synthetic demo. Local demo mode is enabled by default; ordinary new accounts start without demo business data.

For a direct test run after dependencies are installed:

```bash
venv/bin/python -m pytest backend/tests/ -q
venv/bin/python scripts/validate_corpus.py
```

On Windows, use `venv/Scripts/python.exe` in those two commands. The [CI workflow](.github/workflows) checks the knowledge registry, Python tests, app boot, and frontend JavaScript syntax on pushes and pull requests.

Production needs `AFK_SECRET_KEY` and a durable `DATABASE_URL`; see [deployment notes](docs/DEPLOY.md). This README does not claim that a public deployment is currently reachable.

## Repository map

| Path | Purpose |
|---|---|
| [`backend/app/core/engine.py`](backend/app/core/engine.py) | Audit questions, deterministic scoring, findings, and constraint ranking |
| [`backend/app/bse`](backend/app/bse) | Evidence, metric, inference, treatment, and business-twin pipeline |
| [`backend/app/knowledge_engine`](backend/app/knowledge_engine) | Versioned knowledge registry, provenance, case replay, and validation |
| [`knowledge`](knowledge) | Business-system definitions, rules, questions, treatments, and synthetic fixtures |
| [`frontend`](frontend) | Offer page and authenticated audit, evidence, diagnosis, and twin views |
| [`backend/tests`](backend/tests) | Regression tests for the API, scoring, evidence, knowledge, and outcomes |

AFK's engineering principle is simple: **show the mechanism, show the evidence, and say what is not known yet.**
