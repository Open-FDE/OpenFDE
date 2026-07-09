# OpenFDE Specifications v0.1

Two standards OpenFDE wants to make open, because standardizing them is what lets
an ecosystem grow around the Apprentice Loop:

1. the **Judgment Unit Schema** — the artifact
2. the **Elicitation Protocol** — how the artifact is produced

Everything else (moment ranking, the Move library, the stop policy, the
attribution engine) is an *implementation* behind a plugin seam and is out of
scope for the open standard. This document is normative for field names and the
protocol state machine; the reference implementation lives in `openfde/`.

The canonical machine-readable schema is emitted by:

```bash
openfde schema judgment-unit          # JSON Schema (draft 2020-12, via pydantic)
```

---

## 1. Judgment Unit Schema

A **Judgment Unit (JU)** is decision-level procedural memory: a single, versioned,
reusable unit of expert judgment. It is deliberately distinct from a workflow
(AWM), a memory record (Mem0/LangMem) or a temporal fact (Graphiti): a JU is
*a decision plus the tacit reasoning and outcome context around it*.

### 1.1 Required fields

| field | type | meaning |
|-------|------|---------|
| `id` | string | stable id; content-addressed (`ju_<sha1[:12]>`) if unset |
| `version` | int | bumped when a JU with the same id is re-added |
| `status` | enum | `draft \| active \| shadow \| deprecated` |
| `title` | string | short human label |
| `domain` | string | dotted domain, e.g. `sales.qualification` |
| `trigger` | string | the situation in which the judgment applies |
| `decision` | string | what the expert decides/does |

### 1.2 The judgment body

| field | type | meaning |
|-------|------|---------|
| `signals[]` | Signal | what the expert attended to (`name`, `source`, `observation`, `why_it_matters`, `importance`) |
| `preconditions[]` | string | conditions that must hold for the trigger |
| `rationale` | string | **the recovered *why*** — the tacit reasoning made explicit |
| `alternatives[]` | Alternative | options considered (`option`, `considered_because`, `rejected_because`) |
| `reversal_conditions[]` | string | what would flip the decision — the decision boundary |
| `cues_to_watch[]` | string | leading indicators to monitor after acting |

> **Why `reversal_conditions` is mandatory in spirit.** A judgment you cannot
> reverse is a rule, not judgment. The condition under which an expert would
> decide the opposite is the single most transferable — and most omitted — piece
> of expertise. INDUCE SHOULD refuse to mark a JU `active` without it.

### 1.3 Acting on it (graduated autonomy)

| field | type | meaning |
|-------|------|---------|
| `autonomy` | enum | `suggest \| approve \| auto` — the trust tier an agent may act at |
| `action` | ActionSpec | `intent`, optional `tool`/`arguments`/`template`, `guardrails[]` |

Every JU MUST start at `suggest`. Autonomy is **earned** via the ATTRIBUTION
plane, never assigned at induction. The reference promotion policy
(`JudgmentUnit.promote`) requires both confidence and a positive attributed
outcome to advance a tier, and destructive / approval-required connector
operations can never run at `auto` without human approval.

### 1.4 Confidence, evidence, provenance, outcomes

| field | type | meaning |
|-------|------|---------|
| `confidence` | float 0..1 | current belief in the JU |
| `evidence_count` | int | supporting observed episodes |
| `stop_snapshot` | StopSnapshot | the 8-dimension readiness when ELICIT stopped |
| `provenance` | Provenance | `trace_id`, `incident_id`, `elicitation_id`, `expert_id`, `reviewer_id` |
| `outcomes[]` | OutcomeRef | attributed business results (`outcome_id`, `metric`, `credit`, `method`) |
| `supersedes` | string | id of a JU this one replaces |

Every JU is traceable to the real work it came from (`provenance`) and to the
real results it influenced (`outcomes`). Those two links are what make a library
of JUs auditable and improvable rather than a pile of prompts.

### 1.5 The 8 readiness dimensions (`StopSnapshot`)

`cue_coverage`, `rationale_depth`, `alternative_coverage`, `reversal_coverage`,
`consistency`, `novelty_exhaustion`, `expert_confidence`, `corroboration` — each
0..1; `readiness()` is their mean. The *interface* is open and normative; the
tuned scoring is a plugin (moat).

---

## 2. The Elicitation Protocol

ELICIT recovers the *why*. It is a state machine over four sweeps adapted from
the **Critical Decision Method** (Klein, Calderwood & MacGregor, 1989) and
**Cognitive Task Analysis** (Hoffman, Crandall & Shadbolt, 1998).

### 2.1 Phases (sweeps)

```
INCIDENT ──▶ TIMELINE ──▶ DEEPEN ──▶ WHATIF ──▶ (stop)
 bound the    reconstruct  cognitive   hypotheticals /
 moment       the sequence  probes      expert-novice contrast
```

### 2.2 Moves and probes

A **move** is one deliberate question, chosen from a Move Library, carrying:

- `phase` — which sweep
- `probe` — which tacit element it targets, from the open taxonomy:
  `cues`, `knowledge`, `goals`, `options`, `assessment`, `analogues`,
  `expectancy`, `mental_model`, `reversal`, `stakes`, `standard`
- `question` — the wording actually asked
- `answer` — the expert's response (null until answered)
- `extracts_to` — which JU field the answer feeds
- `info_gain` — estimated new information (feeds the stop policy)

### 2.3 Loop

```
while not stop.should_stop(session):
    move = library.next_move(session, incident)   # MoveLibrary plugin
    if move is None: break
    move.answer  = answerer.answer(move, incident) # human expert, or scripted/LLM
    move.info_gain = estimate(move.answer)
    session.add(move)
```

Termination reasons: `saturated` (marginal info gain fell below threshold),
`ready` (8-dim readiness hit target), `max_moves`, `expert_ended`.

### 2.4 Conformance

An implementation conforms if it:

1. represents a session as an ordered list of moves with the fields in §2.2;
2. issues at least one `INCIDENT` and one `DEEPEN` move before stopping;
3. records `info_gain` and a `StopReason`;
4. can render a transcript that INDUCE consumes to populate a JU.

The `MoveLibrary` and `StopCriterion` are pluggable; the open baselines in
`openfde/plugins` are conformant reference implementations.

### 2.5 Who answers

The `AnswerProvider` interface abstracts the responder: a live expert (chat /
voice / trace-replay UI), a `ScriptedAnswerProvider` (offline, tests), or a
model. Per LLMREI (arXiv 2507.02564), an LLM can conduct a competent interview —
but the protocol does not require one.

---

## 3. Versioning

These specs are **v0.1** and expected to change. Breaking field changes bump the
minor version until v1.0. The JSON Schema emitted by the reference implementation
is the source of truth for field-level details; this document is the source of
truth for intent and the protocol state machine.
