# OpenFDE Agent v0.1: teach an agent to learn an expert's judgment on the job

> *Observation gives you the what; elicitation recovers the why.*

We've open-sourced the first version of **OpenFDE Agent** — not another agent
framework, but the layer every agent framework is missing: a way for an AI to
learn a domain expert's tacit judgment *in situ*, act on it under governance, and
be measured against real business outcomes.

Code (MIT): **https://github.com/Open-FDE/OpenFDE** → `agent/`.
Run the whole thing offline in 30 seconds:

```bash
git clone https://github.com/Open-FDE/OpenFDE && cd OpenFDE/agent
pip install -e .
openfde loop --example sales-qualification
```

---

## The uncomfortable premise: enterprise AI mostly fails for non-model reasons

Frontier models get better every month, but enterprises can't move them into core
workflows nearly as fast. The 2024–2026 evidence points at the org, not the model:

- MIT's NANDA *State of AI in Business 2025* reports ~95% of GenAI pilots produced
  "little to no measurable impact on P&L," blaming a **learning gap** — generic
  tools "don't learn from or adapt to workflows." *(This number is widely cited
  and methodologically disputed — narrow success definition, small interview base.
  Treat it as a signal, not a fact.)*
- Gartner predicts **>40% of agentic-AI projects will be canceled by end of 2027**
  on unclear value, cost, and weak controls.
- McKinsey finds the thing that actually correlates with EBIT impact is **workflow
  redesign** — and only ~21% of orgs have redesigned any workflow.

The bottleneck isn't how smart the model is; it's whether it actually grows into
*this company's* way of working. And the scarcest, least-captured asset in every
deployment is the tacit judgment of the person who's already good at the job — the
signals they read, why they decide, and the condition under which they'd decide the
opposite. As the cognitive-science line goes: **experts know more than they can
tell.** A copilot that records *what* an expert did but not *why* can't transfer
the judgment.

## The reframing: enterprises don't need a copilot, they need an apprentice

How does a good apprentice actually learn? They sit next to the expert on real
work; they ask *why* at the moments that matter ("what did you notice, what were
you going for, when would you not do this?"); they distill it; they act with
supervision first and earn autonomy; and they're judged on real results.

OpenFDE turns that into a protocol — the **Apprentice Loop**:

```
   DEPLOY plane  (in-situ: connectors · auth · audit)
        │
   OBSERVE → ELICIT → INDUCE → ACT → EVOLVE
        ▲                               │
   ATTRIBUTION plane  ◀─────────────────┘
   (which judgment actually moved the result?)
```

Five steps loop; two planes are the infrastructure. The five steps learn from the
expert and from outcomes; the planes let the agent actually live on-site and tie
each judgment back to the business.

## The primitive: a Judgment Unit

If the goal is to move *judgment*, the thing you store has to carry judgment.
Existing primitives don't:

- Mem0 / LangMem / Graphiti manage **memory** (facts, preferences, context) — but a
  fact isn't a decision.
- AWM induces reusable **workflows** — the *how*, not the *why-and-when*.

So OpenFDE defines a **Judgment Unit**: a decision, the signals that trigger it, the
elicited rationale, the alternatives considered, the **reversal conditions**, the
graduated autonomy an agent may act at (suggest → approve → auto), and the real
outcome it's later attributed to. A library of these is the auditable, reusable
asset a deployment leaves behind — closer to a Palantir-style ontology, but scoped
to *judgments* rather than data objects, and cheap enough for a small team to
accrue.

## What v0.1 actually ships (it runs)

Not a deck — a Python package (`openfde`) that runs the whole 5+2 loop **offline
and deterministically** on a synthetic, desensitized B2B sales-qualification
scenario. Here's the INDUCE output — a Judgment Unit compiled from an expert's
trace plus one Critical-Decision-Method interview:

```
INDUCE — Judgment Unit · "qualify as an Enterprise land-and-expand deal"
 WHEN     an inbound lead where the immediate team is small but the parent
          company is large, and there's a hard deadline
 SIGNALS  40-person team vs 600-person company mismatch; a hard 6-week deadline;
          a fast, specific first reply
 DO       qualify as Enterprise land-and-expand; push for a scoping call this week,
          overriding the seat-count auto-routing
 WHY      a small team inside a big company + a deadline is almost always a
          beachhead — land the pilot, then expand; the deadline means they'll
          actually buy, not just browse
 REVERSE  if the parent company were actually small, or there were no deadline and
          the reply were vague → route to SMB self-serve
 autonomy=approve · confidence=0.85
```

That **REVERSE** line — "if the parent were small / no deadline, route to
self-serve" — appears in *no* log and *no* trace. It exists only in the expert's
head, and you only get it by asking. That's exactly the piece that decides whether
judgment can be taught to a new hire, or to an agent.

Then ACT compiles it into a **governed** agent config (the CRM write op is marked
`requires_approval`, so nothing runs it at `auto` without a human). A synthetic
closed-deal outcome flows through the ATTRIBUTION ledger, credits the judgment
`+1.0`, and EVOLVE promotes it from `suggest` to `approve` — **trust is earned, not
assigned.** CI runs the suite on Python 3.9 / 3.11 / 3.12, green.

## Open core, and where the boundary is

The rule: **open the protocols and algorithms; keep the assets and signals that
compound with every engagement.** It's not a slogan — it's four plugin seams in the
code, each shipping a working open baseline:

| seam | open baseline | the moat behind the same interface |
|------|---------------|------------------------------------|
| MomentRanker | cue-count heuristic | attribution-fed, cross-client moment ranking |
| StopCriterion | coverage + marginal-info | tuned real-time 8-dimension stop policy |
| MoveLibrary | CDM sweep templates | tuned Move library (wording, order, adaptivity) |
| AttributionEngine | recency-weighted heuristic | delayed/noisy long-horizon credit + incrementality |

What isn't copyable was never the code — it's the expert Moves, the industry
judgment structures, and the real outcome-attribution signal accumulated across
deployments.

## Sit above the runtimes; don't rebuild them

Connectivity (MCP, Composio, Temporal), execution (LangGraph, CrewAI, ADK, Pydantic
AI) and optimization (GEPA, DSPy) are already strong. The core vendors **no**
third-party code — it targets their verified public APIs through optional, lazy
adapters (EVOLVE→GEPA, ACT→Pydantic AI, INDUCE storage→Graphiti/Mem0,
OBSERVE→Langfuse/OTel). OpenFDE only adds the layer nobody standardized:
observe → elicit → induce → act → evolve, with the Judgment Unit at the center.

## What v0.1 deliberately is and isn't

**Is:** a runnable, offline, deterministic reference implementation of the loop and
two proposed standards — the Judgment Unit Schema and the Elicitation Protocol
(`SPEC.md`) — with an open baseline for every moat seam and honest adapters.

**Isn't:** a production runtime, a hosted control plane, or a replacement for
LangGraph/ADK. Honest limits: the offline INDUCE extractor is rule-based (an LLM is
optional and only raises the ceiling — it's a quality lever, not the mechanism);
the ranker/stop/attribution baselines are intentionally simple placeholders for the
closed layer. The point of v0.1 is to make the *protocol* concrete and correct.

If the interesting problem to you is "how does an agent learn judgment from a human
and get graded on real outcomes," that's the layer this is trying to standardize.
Issues and PRs — a Move library, a connector, your own domain scenario — welcome.

- Design rationale, with sources: `agent/DESIGN.md`
- The two standards: `agent/SPEC.md`
- Repo: https://github.com/Open-FDE/OpenFDE
