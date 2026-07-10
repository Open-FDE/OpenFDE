# What kind of FDE Agent do enterprise customers actually need?

*Design rationale for OpenFDE Agent v0.1. Written from the 5+2 thesis in
`OpenFDE_5plus2_论文与开源生态佐证汇总.docx`, cross-checked against 2024–2026
external evidence. Sources are linked inline; disputed figures are flagged.*

---

## 1. Start from why deployments fail, not from what models can do

The temptation is to build a better copilot. The evidence says the copilot is not
the bottleneck.

- **The failure is a *learning gap*, not a capability gap.** MIT's NANDA *State of
  AI in Business 2025* found ~95% of GenAI pilots produced "little to no
  measurable impact on P&L," attributing it to tools that "don't learn from or
  adapt to workflows." *(Widely cited but methodologically disputed — narrow
  success definition, small interview base — so treat the number as a signal, not
  a fact.* [Fortune](https://fortune.com/2025/08/18/mit-report-95-percent-generative-ai-pilots-at-companies-failing-cfo/) · [critique](https://www.marketingaiinstitute.com/blog/mit-study-ai-pilots)*)*
- **Independent corroboration:** Gartner predicts **>40% of agentic-AI projects
  will be canceled by end of 2027** on unclear value, cost, and weak risk
  controls — and that only ~130 of thousands of "agentic" vendors are real
  ([Gartner](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027)).
- **The bottleneck is workflow redesign.** McKinsey's *State of AI 2025*: 88% of
  orgs use AI, but only ~6% are high performers; **fundamental workflow redesign
  correlates most with EBIT impact — yet only 21% have redesigned any workflow**
  ([McKinsey](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai-how-organizations-are-rewiring-to-capture-value)).
- **The killers are organizational:** production data access can take 6–12 months;
  **73% of failed projects had no agreed definition of success** (quantified-metric
  projects succeeded 54% vs 12%) ([Institute PM](https://www.institutepm.com/knowledge-hub/why-enterprise-ai-pilots-fail)).

**Implication.** An FDE Agent must be built to *close the learning gap on-site*:
it has to embed in the real workflow, adapt to it, and be measured against an
agreed business metric from day one. That is precisely the shape of the
Forward-Deployed Engineer model — and why the loop, not the model, is the product.

## 2. The scarcest input is tacit judgment — so the agent must *elicit*, not just observe

- Cognitive Task Analysis exists because watching an expert does not reveal how
  they decide: you need "their interpretations, their goals, the ways they frame
  problems," not just observable actions ([Global Cognition](https://www.globalcognition.org/cognitive-task-analysis/)).
- The **Critical Decision Method** recovers the *why* by retrospectively probing
  hard past incidents — famously surfacing the subtle skin-tone/temperature cues
  paramedics use, which then became teachable to novices ([Hoffman, Crandall &
  Shadbolt 1998](https://journals.sagepub.com/doi/10.1518/001872098779480442)).
- An LLM can competently run such interviews (LLMREI, [arXiv 2507.02564](https://arxiv.org/abs/2507.02564)),
  but the *protocol* — which moments to probe, which cognitive elements to target,
  when to stop — is what's missing from the open ecosystem.

**Implication.** Observation tooling (Langfuse, rrweb, OTel) records *what
happened*; none of it recovers *why*. This is the emptiest open-source category
and OpenFDE's sharpest wedge. Hence **ELICIT** as a first-class step and the
**Elicitation Protocol** as a standard — and hence the design line:

> *Observation gives you the what; elicitation recovers the why.*

## 3. The unit of value is a Judgment Unit, not a workflow or a memory

If the goal is transferable judgment, the artifact must carry the judgment. The
existing primitives don't:

- **Memory layers** (Mem0, LangMem, Graphiti) store facts, preferences, and
  temporal context — useful, but a fact is not a decision.
- **Workflow induction** (AWM, [arXiv 2409.07429](https://arxiv.org/abs/2409.07429))
  abstracts *reusable action routines* — the *how*, not the *why-and-when*.
- **Coding-agent memory** (ProjectMem, MIT) is the closest cousin: append-only
  typed events + decisions + failed attempts. OpenFDE borrows its event-sourced
  discipline but raises the object from "what the agent did" to "what the expert
  judged."

So OpenFDE defines the **Judgment Unit**: a decision, its triggering signals, the
elicited rationale, the alternatives, the **reversal conditions**, the autonomy it
may act at, and its attributed outcome. A library of JUs is the auditable,
reusable asset a forward-deployed engagement leaves behind — the closest thing to
a Palantir "ontology," but scoped to *judgments* rather than objects, and cheap
enough for a small team to accrue.

## 4. Enterprises grant autonomy only against governance and proof — build both in

- **Governance is the precondition, not an afterthought:** risk-tiered autonomy
  (observe → recommend → approval-gated → post-hoc review → scoped autonomy),
  immutable audit trails, escalation on financial/PII/external-impact events, and
  a kill switch are the norm; agents "graduate" only after meeting error
  thresholds (e.g. <2% for 30 days) ([enterprise agent governance](https://thinking.inc/en/blue-ocean/agentic/enterprise-agent-governance/)).
  Yet a 2026 Forrester survey found **71% of enterprises lack a formal governance
  framework** even as 64% plan to increase autonomy — a gap, not a solved problem.
- **Proof is financial, not anecdotal:** only ~29% of executives can confidently
  measure AI ROI ([IBM, via ROI framework](https://agility-at-scale.com/ai/strategy/roi-and-success-metrics/));
  isolating AI's causal contribution from noise is genuinely hard; CFOs trust hard,
  verifiable numbers, not demo accuracy. Deloitte reports 42% of companies
  abandoned ≥1 AI initiative in 2025 (avg sunk cost ~$7.2M).

**Implication.** Two things must be *structural*, not optional:

1. **Graduated autonomy** — every JU declares `suggest / approve / auto`, and ACT
   compiles that into an approval policy a runtime enforces (destructive ops never
   auto-run without a human). Trust is earned, per-judgment.
2. **An attribution/audit ledger** — an append-only record linking each judgment
   and action to the real outcome it influenced. It is simultaneously the CFO's
   proof, the auditor's trail, and EVOLVE's reward signal:

   > *GEPA gives you the optimizer; ATTRIBUTION gives you the golden feedback.*

## 5. Sit above the runtimes; don't rebuild them

The FDE role is rising precisely because integration — not model quality — is the
moat: a16z calls FDEs "the hottest job in startups" and argues AI companies must
"trade margin for moat" ([a16z](https://a16z.com/services-led-growth/)); the role
originated at Palantir and is now copied by OpenAI and others ([Pragmatic
Engineer](https://newsletter.pragmaticengineer.com/p/forward-deployed-engineers)).
The open-source ecosystem already covers connectivity (MCP, Composio, Temporal),
execution (LangGraph, CrewAI, ADK, Agents SDK, Pydantic AI), and optimization
(GEPA, DSPy). Rebuilding any of them is wasted motion.

**Implication.** OpenFDE is an **FDE layer above** these runtimes. It
orchestrates them through thin, verified adapters and contributes the one layer
nobody has standardized: observe → elicit → induce → act → evolve, with the
Judgment Unit at the center.

---

## The requirements, mapped to the loop

| Enterprise reality (evidence) | Loop answer |
|---|---|
| Pilots fail on a *learning gap*, not model quality (§1) | the whole loop learns on-site and adapts to the workflow |
| Value needs workflow redesign, done by someone embedded (§1) | the FDE-shaped, in-situ **DEPLOY** plane |
| Expertise is tacit; observation misses the *why* (§2) | **ELICIT** + the open Elicitation Protocol (CDM/CTA) |
| A fact/workflow isn't a decision (§3) | **INDUCE** → the **Judgment Unit** (with reversal conditions) |
| No autonomy without governance; 71% lack it (§4) | **ACT** compiles **graduated autonomy** + guardrails a runtime enforces |
| Only ~29% can prove ROI; proof must be financial (§4) | **ATTRIBUTION** ledger = audit trail + reward signal |
| Optimizers lack high-value feedback (§4) | **EVOLVE** optimizes against attributed outcomes, not demos |
| Integration is the moat; don't rebuild runtimes (§5) | thin, optional adapters to MCP / LangGraph / GEPA / Graphiti / … |

## Open-core boundary (why this is defensible)

Open the **protocols and algorithms** so an ecosystem forms around them; keep the
**assets and signals** that compound with every engagement. In code, the boundary
is four plugin seams (`openfde/plugins`), each with a working open baseline:

| open (standard + baseline) | closed (compounding moat) |
|---|---|
| Judgment Unit Schema, Elicitation Protocol, Connector Spec, thin ACT compiler, GEPA adapter | tuned Move library, real-time 8-dim stop policy, attribution-fed moment ranking, industry judgment structures, cross-client outcome models |

What is not copyable is not the code — it is the expert Moves, the industry
judgment structures, and the real business-outcome attribution accumulated across
deployments. That is the thing OpenFDE is designed to accrue.

## What v0.1 deliberately is and isn't

**Is:** a runnable, offline, deterministic reference implementation of the loop and
the two flagship standards, with one synthetic end-to-end example, an open baseline
for every moat seam, and honest adapters to real ecosystem projects.

**Isn't:** a production runtime, a hosted control plane, a managed attribution
engine, or a claim to replace LangGraph/ADK/Agents SDK. Those are either the
commercial layer or someone else's job. v0.1's purpose is to make the *protocol*
concrete and correct.
