# AFK Scientific Knowledge Base — Architecture Specification
**Version 1.0 · 4 July 2026 · Author: Founding CTO · Status: For founder review**

This document is the permanent blueprint for how AFK's scientific knowledge is stored, versioned, validated, related, and consumed by software. It is infrastructure only: no new business science is defined here. Design horizon: 10 years, 100,000 knowledge objects. Implementation horizon: start with ~50.

---

## Part 0 — Governing design decisions

Five decisions shape everything below; each is chosen for determinism, traceability, and longevity.

**D1. Knowledge lives as files in Git, not rows in a database.** Every knowledge object is one human-readable YAML file in a versioned repository (`afk-knowledge`). Rationale: Git already solves — perfectly and verifiably — versioning, diff, rollback, blame (who/when/why), branching for research-in-progress, and tamper-evident history. Rebuilding those in a database is years of work to get a worse answer. Databases appear downstream, as *compiled artifacts*, never as the source of truth.

**D2. A deterministic Compiler turns the repo into immutable Knowledge Releases.** `afk-kbc` (knowledge base compiler) validates every file against schema, checks every relationship, enforces validation-status gates, and emits a single versioned artifact (SQLite file + JSON index) called a **Knowledge Release** (e.g., `AFK-KR 2026.07`). Software loads Releases, never raw files. A given Release is immutable and reproducible byte-for-byte from a Git tag.

**D3. Stable identifiers, ICD-style.** Every object gets a permanent, meaning-free ID at birth: `AFK-<TYPE>-<NNNN>` (e.g., `AFK-CON-0007` for a constraint, `AFK-TRT-0012` for a treatment). IDs are never reused, never renamed, never deleted — objects are deprecated, not destroyed. Names can change; IDs cannot.

**D4. Knowledge objects vs. runtime instances are strictly separated.** A Constraint is knowledge; a Finding ("this business has this constraint, at this confidence, on this date") is a runtime instance produced by the product, stored in the product database, and *referencing* knowledge IDs + Release version. The KB never contains customer data; the product DB never contains science. This boundary is absolute — it is also the privacy boundary.

**D5. The validation ladder is machine-enforced.** The compiler refuses to include an object in the `production` channel of a Release unless its validation status clears the bar its consumers require. Never-invent becomes a build-time guarantee, not a norm.

---

## Part 1 — Overall architecture

```
┌────────────────────────────────────────────────────────────┐
│  LAYER 1 · afk-knowledge (Git repository)                  │
│  YAML objects · citations · validation records · schemas   │
└──────────────────────────┬─────────────────────────────────┘
                           │  afk-kbc compile (deterministic)
┌──────────────────────────▼─────────────────────────────────┐
│  LAYER 2 · Knowledge Release (immutable artifact)          │
│  AFK-KR YYYY.MM · SQLite + JSON index · signed manifest    │
└──────────────────────────┬─────────────────────────────────┘
                           │  loaded read-only at boot
┌──────────────────────────▼─────────────────────────────────┐
│  LAYER 3 · Knowledge Runtime API (in product backend)      │
│  get / query / trace / diff — no writes, ever              │
└─────┬──────────────────┬───────────────────┬───────────────┘
      ▼                  ▼                   ▼
 Diagnosis Engine    The Analyst        Product UI
 (deterministic)     (LLM, cites KB)    (renders provenance)
      │
      ▼
 Runtime instances (Findings, Diagnoses, Recommendations)
 → product DB, tagged with KR version + object IDs used
      │
      ▼  anonymized observations flow BACK as
 Validation Records / Case Studies → Layer 1 (via review)
```

**Dependency rules (the "never reference upward" law):**
- Layer 3 depends on Layer 2 depends on Layer 1. Nothing in Layer 1 may reference a Release, a runtime instance, or any customer identifier.
- Within Layer 1: *Diagnostic* objects may reference *Structural* objects; *Interventional* objects may reference *Diagnostic* + *Structural*; *Epistemic* objects (citations, validation records) may be referenced by anything but reference only each other and external sources. Concretely: a Metric never references a Constraint; a Constraint never references a Treatment (Treatments declare which Constraints they treat — the arrow points from intervention to diagnosis, mirroring medicine: the drug references the disease, never the reverse).
- Runtime instances reference knowledge by `(object_id, version, release)` triplet — never by name.

**Ownership vs. reference:** the repo *owns* all knowledge objects (one file = one object = one owner path). Objects *reference* each other only through typed Relationship declarations (Part 3). No object embeds another object's content — composition by reference only, so a change has exactly one home.

---

## Part 2 — The object catalog

### 2.0 The Base Envelope (shared by every object)

Every knowledge object, regardless of type, carries this envelope. Defining it once prevents twenty divergent schemas.

```yaml
id: AFK-CON-0007            # permanent, assigned at creation, never reused
type: constraint             # one of the registered types below
name: "Pricing Leakage"      # human name, may change across versions
version: "1.2.0"             # semver (Part 4)
status: hypothesis           # validation ladder position (Part 5)
owner: chief_pattern_scientist   # role, not person (Part 13)
created: {by: "A. Kumar", date: 2026-07-04, reason: "Initial import from research batch 1"}
changelog:                   # every version bump appends an entry
  - {version: "1.2.0", date: ..., by: ..., reason: "Threshold recalibrated after case AFK-CAS-0003"}
citations: [AFK-CIT-0031, AFK-CIT-0044]        # Part 7
validation_records: [AFK-VAL-0009]              # Part 5
relationships:                                   # typed edges, Part 3
  - {type: causes, target: AFK-CON-0011, confidence: hypothesized}
tags: [pricing, monetization]
supersedes: null             # or an object id this replaces
deprecated_by: null
notes: ""                    # free text, never machine-consumed
```

**Envelope rules:** `id, type, name, version, status, owner, created` are required. An object with zero citations cannot pass `literature_supported` or above. `notes` is the only field the compiler ignores — everything else is validated.

### 2.1 Structural objects (the anatomy)

**BusinessSystem** (`AFK-SYS-`) — a functional subsystem of a business (Demand, Qualification, Conversion, Monetization, Retention, Operations…). *Purpose:* the anatomical map everything else attaches to. *Required:* definition, boundary (what it includes/excludes), inputs, outputs, parent_system (nullable → hierarchy). *May be referenced by:* everything. *Must never reference:* constraints, treatments, or anything diagnostic — anatomy doesn't know about disease. *Owner:* Chief Ontologist. *Lifecycle:* near-permanent; changes are major events.

**Metric** (`AFK-MET-`) — a measurable quantity with exactly one computation. *Required:* definition, unit, computation (formula in a restricted expression grammar over canonical evidence fields — the same canonical vocabulary M3.1 established), evidence_fields_required, interpretation_direction (higher-is-better / lower-is-better / contextual), quality_requirements. *Referenced by:* DetectionRules, MonitoringRules, PhysiologyPatterns. *Never references:* rules or constraints. *Note:* M3.2's `avg_discount_pct`, `repeat_customer_rate` etc. become the first Metric objects — their Python implementations become generated/verified against these definitions.

**BusinessPrinciple** (`AFK-PRN-`) — a foundational assertion of AFK Business Science ("Revenue is a system with constraints"). *Required:* statement, scope, falsifiability_note (what observation would weaken it — mandatory; unfalsifiable principles are flagged `philosophical` and may never be cited by DetectionRules). *Owner:* Chief Epistemologist.

### 2.2 Diagnostic objects (the pathology)

**Constraint** (`AFK-CON-`) — a named, recurring limitation pattern ("Pricing Leakage", "Founder Dependency"). *Required:* definition, affected_systems (→ BusinessSystem), mechanism (how it limits revenue, prose + causal edges), typical_presentation, differential (constraints it is confused with), detection_rules (→ DetectionRule ids). *Optional:* prevalence_notes, severity_model. *Referenced by:* Treatments, Findings (runtime). *Never references:* Treatments. *Owner:* Chief Pattern Scientist.

**DetectionRule** (`AFK-DET-`) — one deterministic test suggesting a constraint. *Required:* constraint_id, logic (restricted boolean expression over Metrics and QuestionnaireItems — no free code), thresholds (each with a `threshold_basis`: where the number came from — this is where "15% discount" stops being folklore), evidence_map (Part 9), confidence_contribution, contradiction_behavior. *Versioning note:* threshold changes are minor versions but *always* require a ValidationRecord or explicit `basis: operator_judgment` flag — the compiler blocks silent recalibration.

**EvidenceRule** (`AFK-EVR-`) — what counts as valid evidence of a given kind: required fields, freshness window, minimum rows, quality gates. M3.2's data-quality logic becomes these objects.

**ConfidenceModel** (`AFK-CFM-`) — a named, versioned formula for combining evidence into confidence (the 40%-questionnaire-ceiling model becomes `AFK-CFM-0001 v1.0`). *Required:* formula, inputs, rationale, worked_example. Only ONE ConfidenceModel is active per Release — plurality of confidence math is how trust dies.

**PhysiologyPattern** (`AFK-PHY-`) — a described dynamic between systems ("discount pressure rises as qualification weakens"), i.e., accepted causal knowledge. *Required:* systems_involved, dynamic_description, direction, observable_signature (which Metrics move), causal edges. This is where the Physiology research lands as discrete, testable units rather than essays.

**QuestionnaireItem** (`AFK-QUE-`) — one audit question. *Required:* text, answer_type, options, evidence_class (`self_report` — permanently; a questionnaire answer can never be promoted to measured evidence), dimensions_informed. The M2 audit's 28 questions become the first 28 objects.

**DiagnosticMethodology** (`AFK-DGM-`) — the ordered procedure the engine follows (Part 8 pipeline as data). One active per Release.

### 2.3 Interventional objects (the pharmacology)

**Treatment** (`AFK-TRT-`) — full schema in Part 10.

**MonitoringRule** (`AFK-MON-`) — full schema in Part 11.

**DecisionRule** (`AFK-DEC-`) — tie-breaking and sequencing logic ("if two constraints score equally, prioritize the one upstream in the causal graph"). Explicit objects so prioritization is never buried in code.

### 2.4 Epistemic objects (the literature)

**Citation** (`AFK-CIT-`) — Part 7. **Hypothesis** (`AFK-HYP-`) — a claim under investigation: statement, predicted_observation, test_design, status (open/supported/refuted/abandoned). Refuted hypotheses are *kept* — negative results are knowledge. **ValidationRecord** (`AFK-VAL-`) — Part 5; the object that moves things up the ladder. **CaseStudy** (`AFK-CAS-`) — one anonymized real-business observation: business profile shape, evidence summary, diagnosis produced, treatment applied, outcome, KR version used. The BenchmarkSample architecture from M3.2 feeds these. **ResearchPaper** (`AFK-RSP-`) — an internal research artifact (the Grok/ChatGPT outputs) with review history; papers are *sources for* knowledge objects, never directly machine-consumed.

### 2.5 Runtime instances (NOT knowledge — product database)

**Finding, Diagnosis, Recommendation, TreatmentPlan, MonitoringResult** — produced by the engine for one business at one moment. Schema requirement: every instance stores `(kb_release, object_ids_used[], engine_version, evidence_dataset_ids[])` so any diagnosis ever produced can be exactly reproduced and audited. These never enter the knowledge repo; anonymized *summaries* of them return as CaseStudies through review.

---

## Part 3 — The relationship model

All edges are declared in the `relationships` block of the *source* object, as `{type, target, confidence, citations?, notes?}`.

**Registered edge types** (closed vocabulary — new types require a schema version bump):

| Category | Types | Semantics |
|---|---|---|
| Causal | `causes`, `increases`, `decreases`, `creates_pressure_on` | Directed. Each edge carries its own validation confidence (`hypothesized` / `observed` / `validated`) — a *canonical constraint may have a merely hypothesized causal edge*, and the UI must render the difference. |
| Structural | `part_of`, `parent_of` (hierarchy) | Strict tree per object type; compiler rejects cycles. |
| Evidential | `supports`, `contradicts`, `derived_from` | Links claims ↔ citations/case studies. `contradicts` edges are first-class and never deleted — disagreement is data. |
| Dependency | `requires`, `detects`, `treats`, `monitors`, `informs` | The machine-consumption edges (rule→metric, treatment→constraint…). |
| Lineage | `supersedes`, `deprecated_by`, `variant_of`, `related_to` | Version and family lineage. |

**Graph rules enforced at compile time:**
1. Every `target` must exist (no dangling edges).
2. Structural hierarchies are acyclic. **Causal edges MAY form cycles** — feedback loops are real business physiology (churn → revenue pressure → discounting → margin loss → underinvestment → churn) — but any causal cycle must be explicitly annotated `loop: acknowledged` with a note, or the build fails. Unacknowledged cycles are usually modeling errors; acknowledged ones are insight.
3. Layer discipline from Part 1 (anatomy never points at pathology, etc.).
4. Every edge with confidence `validated` must cite ≥1 ValidationRecord.

The compiled Release materializes the full graph as an adjacency index so the product can answer "show me everything downstream of Inventory Mismatch" in one query, deterministically.

---

## Part 4 — Versioning

**Per-object semantic versioning:**
- **PATCH (x.y.Z)** — wording, notes, citation additions, typo fixes. No machine-consumed field changes. Auto-approvable.
- **MINOR (x.Y.0)** — threshold recalibration, added optional fields, added relationships, expanded evidence maps. Requires review + (for thresholds) a ValidationRecord or explicit operator-judgment flag. Backward compatible: software consuming v1.1 logic behaves sanely on v1.4.
- **MAJOR (X.0.0)** — changed definition, changed detection logic semantics, changed required evidence, changed causal direction. Requires full review chain (Part 13) and a migration note describing what happens to Findings produced under the old major.

**Release versioning:** Knowledge Releases are calendar-versioned (`AFK-KR 2026.07`, `2026.07.1` for hotfixes) and pin exact object versions — like an OS release pinning package versions. **Software pins to a Release** and upgrades deliberately; two Releases can be installed side-by-side for diffing. Old Releases remain loadable forever (they're immutable files), so yes — software can keep using older knowledge, and re-audits can be run under the original Release for honest before/after comparison.

**Deprecation:** an object is never deleted. `status: deprecated` + `deprecated_by: <id>` + a sunset note. The compiler excludes deprecated objects from new Releases' production channel but keeps them resolvable for provenance (a 2026 Finding citing a constraint deprecated in 2028 must still render correctly in 2030).

---

## Part 5 — Validation framework

The ladder, with machine-enforced gates:

| Level | Criteria | Required to promote | Who signs |
|---|---|---|---|
| `draft` | Exists, schema-valid | — | author |
| `hypothesis` | Complete definition + falsifiability note + predicted observation | self-review checklist | owner role |
| `literature_supported` | ≥2 independent external citations of tier A/B (Part 7) that *support* the claim | citation review | Chief Historian |
| `peer_reviewed` | Written review artifact addressing the Skeptic checklist (confounds, alternative explanations, measurement validity) | review record attached | Chief Skeptic |
| `observed` | ≥1 CaseStudy from a real business where the predicted signature appeared | ValidationRecord w/ case link | Chief Pattern Scientist |
| `validated` | ≥N CaseStudies (N=3 initial, rising with library maturity) across ≥2 business types, with pre-registered predictions | N ValidationRecords | Skeptic + owner |
| `canonical` | Validated + survived ≥1 attempted refutation + stable ≥6 months | refutation attempt on record | full chain |
| `deprecated` / `archived` | Superseded or refuted | demotion record with reason | Chief Skeptic can demote unilaterally |

**Demotion rules:** any level can fall. A `contradicts` edge from a new CaseStudy automatically flags the object for Skeptic review; two contradicting cases force demotion to `hypothesis` pending investigation. The Skeptic can demote; nobody can promote their own object past `hypothesis`.

**Consumption gates (D5):** the Diagnosis Engine's production channel loads objects at `observed`+ for *display-as-diagnosis*; `hypothesis`/`peer_reviewed` objects may run in **shadow mode** (computed, logged, shown to the founder-scientist only, never to customers) — this is how new science earns promotion without ever violating never-invent in front of a user. The UI must render validation status on every conclusion. **Honest current state: as of today, zero objects can stand above `peer_reviewed`, because AFK has zero CaseStudies. The ladder's upper half is empty until Patient Zero.**

---

## Part 6 — Provenance

Three reinforcing layers, nothing exists without all three:
1. **Envelope provenance** — `created{by, date, reason}` + append-only `changelog` with a mandatory `reason` per version. The compiler rejects a version bump without a reason.
2. **Git provenance** — every change is a commit by an identified author through a pull request; history is tamper-evident. "Who changed the discount threshold, when, and what did the diff look like" is `git log -p` — solved, forever.
3. **Epistemic provenance** — `citations` + `validation_records` answer "why do we believe this," distinct from "who typed it."

A Release's manifest records the exact Git commit it was compiled from: every number the product ever shows is traceable to a commit, an author, a reason, and its supporting evidence, in under a minute.

---

## Part 7 — Citation architecture

**Citation object (`AFK-CIT-`):** source_type (`academic_paper | book | industry_report | government_data | afk_case_study | founder_interview | operational_data | internal_research`), full reference, locator (DOI/ISBN/URL/internal id), retrieved_date, archived_copy (path in repo — link rot is real; tier A/B sources are snapshotted), summary_of_relevance, quality_tier:
- **A** — peer-reviewed research, government statistics
- **B** — reputable books, named industry reports
- **C** — practitioner writing, credible blogs
- **D** — internal AI-research syntheses (the Grok/ChatGPT papers) — *explicitly the lowest external tier; D-only support can never carry an object past `hypothesis`*
- **E** — AFK's own CaseStudies — tier E is *internal empirical* and is what the upper ladder runs on; it outranks everything for validation but cannot substitute for external literature at `literature_supported`.

Claims reference citations with a stance: `{cite: AFK-CIT-0031, stance: supports | contradicts | contextualizes}`.

---

## Part 8 — Diagnostic consumption (deterministic pipeline)

The engine is a pure function: `diagnose(evidence_bundle, audit_answers, KR) → Diagnosis`. Same inputs + same Release = identical output, forever. The pipeline (itself data: the active DiagnosticMethodology object):

```
load KR (pinned)                       # immutable artifact
 → resolve active DiagnosticMethodology
 → load QuestionnaireItems             # interpret audit answers
 → load EvidenceRules                  # validate & grade evidence bundle
 → compute Metrics                     # only those whose required fields exist
 → evaluate DetectionRules             # restricted expression language, no code
 → assemble candidate Findings         # constraint + evidence + rule versions
 → apply ConfidenceModel               # one model, versioned
 → apply DecisionRules                 # ranking, tie-breaks, causal upstream priority
 → attach Treatments                   # via `treats` edges, contraindications checked
 → attach MonitoringRules
 → emit Diagnosis{KR, object_ids+versions, evidence_ids, engine_version}
```

No LLM appears anywhere in this path. The Analyst sits *beside* the pipeline: it receives the Diagnosis and may explain, contextualize, and cross-examine — it may never add a Finding, alter a score, or cite anything without a KB id. Rule logic lives in a restricted expression grammar (comparisons, boolean ops, arithmetic over named Metrics/answers) — powerful enough for every rule we have, weak enough to be provably deterministic and diffable.

---

## Part 9 — Evidence mapping (on every DetectionRule)

```yaml
evidence_map:
  required:   [{kind: invoices, fields: [amount, discount], min_rows: 20, max_age_months: 12}]
  optional:   [{kind: leads, fields: [status], effect: "raises confidence_contribution to 0.9"}]
  quality_gates: {min_quality_score: 0.6, on_fail: "rule runs, output flagged low_quality"}
  missing_behavior: "rule does not fire; contributes to missing_evidence guidance with this text: ..."
  contradictory_evidence: [{signal: "...", effect: "suppress finding, emit contradiction instead"}]
  freshness_decay: "confidence_contribution × 0.8 if newest record > 6 months old"
  priority: primary   # primary | corroborating
```

This generalizes exactly what M3.2 hard-coded — the migration path is extraction, not invention.

---

## Part 10 — Treatment library schema

**Treatment (`AFK-TRT-`)** required fields: definition · mechanism (why it works, with causal edges into the graph) · treats (→ Constraint ids) · preconditions (evidence that must exist before recommending) · **contraindications** (business states where this treatment harms — e.g., "raise prices" is contraindicated during an active churn spiral) · evidence_level (its own validation status — a canonical constraint may have only hypothesis-level treatments, and the UI must show that gap honestly) · expected_outcome (which Metrics move, direction, rough magnitude *with basis*) · expected_timeframe · effort_estimate · required_monitoring (→ MonitoringRule ids) · failure_criteria (what observation means it isn't working) · re_diagnosis_trigger · citations.

The M2 "playbook" entries become the first ~6 Treatment objects at `hypothesis` status — which is the honest label for what they are.

---

## Part 11 — Monitoring framework

**MonitoringRule (`AFK-MON-`):** metric_id · role (`leading | lagging`) · expected_trajectory (direction + window: "discount % should fall within 2 invoice cycles") · checkpoint_schedule · re_diagnosis_triggers (metric regression past threshold; new contradiction; evidence staleness; treatment failure_criteria met) · confidence_degradation (evidence older than its freshness window automatically decays diagnosis confidence — a 9-month-old diagnosis must not present as current truth) · recovery_curve (expected shape, honestly marked `hypothesized` until cases exist).

This part is deliberately thin: real recovery curves require real treated businesses. Designing elaborate monitoring before one exists would be theory-crafting — the schema reserves the space; cases will fill it.

---

## Part 12 — Research lifecycle (how knowledge enters)

```
Research artifact (Grok/ChatGPT/human)  → committed as ResearchPaper (tier-D citation)
 → Extraction: discrete claims become draft objects (one claim = one object; essays don't compile)
 → PR opened against afk-knowledge (schema-checked by CI automatically)
 → Review chain per object type (Part 13) → merge = `hypothesis`
 → Literature pass → `literature_supported` → Skeptic pass → `peer_reviewed`
 → Shadow-mode deployment in next Release (runs silently on real audits)
 → Real-business observation → CaseStudy + ValidationRecord → `observed` → … → `canonical`
 → Every real diagnosis feeds anonymized outcomes back as future CaseStudies
```

The unit of scientific progress is the **pull request**. Nothing enters by conversation, memory, or vibe.

---

## Part 13 — Separation of responsibilities

Honesty before org charts: **today every one of these roles is Ak, assisted by AIs.** The roles are still worth defining now — as review *hats* with checklists, so that one person is forced to change perspective, and so the structure survives future hiring. Rule that makes this real rather than theater: **no object is authored and validated under the same hat**, and the Skeptic hat must be worn by a different session/context than the author.

| Role | Creates | Reviews | Approves | Can demote |
|---|---|---|---|---|
| Chief Ontologist | Systems, vocabulary | structural edges | anatomy changes (all major) | — |
| Chief Pattern Scientist | Constraints, DetectionRules | detection logic | `observed` promotions | own objects |
| Chief Business Physiologist | PhysiologyPatterns, causal edges | mechanism claims | causal-edge upgrades | — |
| Chief Historian | Citations, archives | citation quality, link integrity | `literature_supported` | citations |
| Chief Skeptic | refutation attempts, Hypotheses | EVERYTHING at `peer_reviewed`+ | nothing (deliberately) | **anything** |
| Chief Epistemologist | Principles, ConfidenceModels, ladder itself | validation methodology | ladder/criteria changes | — |
| Chief Systems Scientist | DecisionRules, Methodology | pipeline coherence, loop annotations | Release sign-off | — |
| Founder/CEO | — | — | final arbiter on disputes; owns Release cadence | — |

Version history is owned by nobody — that's the point of Git.

---

## Part 14 — Software requirements (what the runtime must do)

Search & query (by type/status/tag/text; graph traversal "everything downstream of X") · load-only-validated via channels (`production` = observed+, `shadow` = all) · version pinning per deployment · **diff** any two Releases ("what changed between the diagnosis you got in July and today's") — this diff is itself a founder-facing feature · full audit (Release manifest → commit → PR → author → reason) · rollback = load previous Release file (minutes, not migrations) · reproduce any historical Diagnosis exactly (instance stores its Release) · serve all of it through deterministic read-only APIs · run the complete diagnostic path with zero LLM calls. Storage math: 100k YAML objects ≈ 200–400 MB repo, compiled Release ≈ tens of MB SQLite — laptop-scale for a decade; no distributed-systems engineering warranted or wanted.

---

## Part 15 — Self-challenge (mandatory honesty)

1. **The ladder's top half is aspirational fiction today.** Zero CaseStudies exist; nothing can pass `observed`. The architecture is sound but empty above the waterline. *Mitigation:* Patient Zero (Vintech) within weeks, not quarters; treat the first 3 real audits as the founding dataset of the discipline.
2. **"Peer review" without external peers.** The current chain is one human + LLMs trained on the same internet — correlated errors will sail through. *Mitigation:* the hat-separation rule above, plus a standing goal of one external domain reviewer (a real distributor, a real CA/accountant) per quarter; their signed review is a tier-B citation.
3. **Over-engineering risk is real and I've bounded it.** Designed for 100k objects; the correct build for the next 6 months is the envelope schema, the compiler with validation gates, IDs, and ~50 objects extracted from M2/M3.2 code. Everything else in this spec is *format*, not software to write now. If we spend a month on knowledge tooling before the first CaseStudy exists, this document has failed.
4. **Single-human governance bottleneck.** Every hat on one head means throughput ≈ one careful person; also a bus-factor of 1. Git mitigates knowledge loss; nothing mitigates judgment concentration until there's a second scientist.
5. **Causal-graph maintenance is the long-term cost center.** Edges will outnumber objects 5:1; contradicting edges will accumulate. The Skeptic's demotion power + `contradicts`-is-permanent are the immune system, but expect graph gardening to become a real recurring chore by ~1,000 objects.
6. **Schema ossification.** A wrong required field hurts forever. *Mitigation:* schema itself is versioned (`envelope/v1`), and the first 90 days run in `schema-beta` where breaking schema changes are allowed by decree.
7. **The restricted expression grammar will feel confining** the first time a rule wants something clever. That confinement is the feature — the day we allow arbitrary code in DetectionRules is the day determinism and diffability die. Escape hatch: a clever rule becomes a new named Metric (reviewed, versioned) instead.
8. **Failure mode to watch:** knowledge theater — beautifully versioned, richly cited objects describing patterns no business has exhibited. The tell is the ratio of Epistemic objects to CaseStudies. If that ratio exceeds ~20:1 after Q3 2026, stop writing science and go observe businesses.

**Recommended build order when implementation is authorized:** (1) envelope schema + ID registry + repo layout, (2) compiler with schema/relationship/status gates, (3) extraction of existing M2/M3.2 logic into ~50 objects at their honest statuses (mostly `hypothesis`), (4) engine consumes Release instead of hard-coded rules, (5) shadow channel. Estimated as one sub-milestone (M3.3a), because 80% of the "knowledge" already exists — in Python, waiting to be liberated into science.

— End of specification —
