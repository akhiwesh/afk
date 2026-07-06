# AFK Knowledge Base
This directory IS AFK's science. Code executes it; this defines it. Authoritative architecture: `/KB_ARCHITECTURE.md`.

## Structure
One YAML file = one knowledge object = one permanent ID (`AFK-<TYPE>-<NNNN>`, never reused, never deleted — only deprecated). Folders by type: `systems/` (business anatomy) · `constraints/` (limitation patterns) · `detection_rules/` (deterministic tests; thresholds carry `threshold_basis`) · `metrics/` (one computation each) · `treatments/` (interventions incl. TODO-marked contraindications) · `confidence_models/` · `questionnaire/` · `evidence_rules/` · `cases/` (real-business observations — **currently empty; this emptiness is the KB's most important fact**) · `schemas/`.

## Adding research (the only way knowledge enters)
1. Copy an existing object of the same type as a template. 2. Assign the next free ID for that prefix. 3. Fill the envelope — `created.reason` is mandatory; gaps become `todos:` entries, never guesses. 4. Enter at `status: hypothesis` (or `draft`). 5. The loader auto-discovers the file at next boot — **zero code changes**. 6. Invalid schema, unknown relationship type, or dangling target = loud startup failure, by design.

## Versioning & validation
Semver per object: PATCH = wording; MINOR = thresholds/added fields (threshold changes require a `threshold_basis`); MAJOR = changed meaning (append `changelog` entry with reason). Ladder: draft → hypothesis → literature_supported → peer_reviewed → observed → validated → canonical (see KB_ARCHITECTURE Part 5). Today all 78 objects are `hypothesis` — the honest status until `cases/` has content.

## How software consumes this
`knowledge_engine/registry.py` loads + validates everything into an immutable in-process registry; read-only APIs under `/api/knowledge/*` (stats, search, object, relationships). The diagnosis engine does not yet consume the registry — a parity test (`test_knowledge.py::test_PARITY...`) proves registry == engine internals until that migration, so the two cannot silently diverge.
