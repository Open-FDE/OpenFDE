<div align="center">

# OpenFDE Agent — the FDE Loop

**An in-situ FDE layer that sits *above* agent runtimes.**
It watches an expert's real work, asks *why* at the moments that matter, distills
that into reusable **Judgment Units**, acts with graduated autonomy, and evolves
on real business outcomes.

`OBSERVE → ELICIT → INDUCE → ACT → EVOLVE`  ·  on two planes: **DEPLOY** + **ATTRIBUTION**

> *Observation gives you the what; elicitation recovers the why.*

</div>

---

## Why this exists

Enterprise AI mostly fails for organizational, not model, reasons. The recurring
finding across 2025–2026 studies is a **learning gap**: generic tools "don't
learn from or adapt to workflows," so pilots stall before production (MIT NANDA,
*State of AI in Business 2025*). Gartner projects **>40% of agentic-AI projects
will be canceled by end of 2027** on unclear value and weak controls. McKinsey
finds the bottleneck is **workflow redesign**, not model quality — the thing that
correlates with EBIT impact, and the thing almost nobody does.

The scarcest asset in every deployment is the **tacit judgment** of the person
who is already good at the job — the signals they read, the calls they make, the
conditions under which they'd decide the opposite. Cognitive-science calls this
out plainly: *experts know more than they can tell.* A copilot that captures
*what* an expert did but not *why* cannot transfer expertise.

OpenFDE's bet: the unit of enterprise value is not a chatbot, a workflow, or a
memory store — it is a **Judgment Unit**, and the loop that produces one.

## The FDE Loop (5 + 2)

```
  DEPLOY plane  ───────────────────────────────────────────────  (in-situ: connectors · auth · audit)
        │
        ▼
   ① OBSERVE ──▶ ② ELICIT ──▶ ③ INDUCE ──▶ ④ ACT ──▶ ⑤ EVOLVE
      看          问            学           做         长
        ▲                                                   │
  ATTRIBUTION plane  ◀──────────────────────────────────────  (credit: which judgment moved the result?)
```

| step | does | OpenFDE's distinct move |
|------|------|--------------------------|
| **OBSERVE** | ingest expert traces (Langfuse / OTel / rrweb shape) | flags **critical incidents** — which moments hid a judgment |
| **ELICIT** | actively interview the expert around a moment | an open **Elicitation Protocol** (Critical Decision Method); the emptiest OSS category |
| **INDUCE** | compile trace + interview into memory | a **Judgment Unit**, not a workflow (AWM) or a memory record (Mem0) |
| **ACT** | run the judgment in the real system | thin compiler → governed agent config with **graduated autonomy** (suggest→approve→auto) |
| **EVOLVE** | improve from feedback | reflection (GEPA-shaped) driven by **real outcomes**, not demo accuracy |
| **DEPLOY** plane | let the agent live on-site | thin **Connector Spec** over MCP / Composio / Temporal — we don't rebuild them |
| **ATTRIBUTION** plane | connect judgments to results | append-only **outcome ledger** = the reward signal + the audit trail |

## Quick start

```bash
cd agent
python -m venv .venv && . .venv/bin/activate
pip install -e .            # core deps only: pydantic, typer, rich, pyyaml

openfde loop --example sales-qualification
```

That runs the entire 5+2 loop **offline and deterministically** — no LLM, no
network — on a synthetic B2B sales-qualification scenario, and prints each stage:
the flagged incident, the elicitation transcript, the induced Judgment Unit, the
compiled (governed) agent config, the attributed credit, and the EVOLVE update.

Programmatically:

```python
from openfde import run_loop
from openfde._examples import sales_qualification

ex = sales_qualification()
result = run_loop(ex["trace"], ex["answers"],
                  project=ex["project"], domain=ex["domain"],
                  connectors=ex["connectors"],
                  actions=ex["actions"], outcomes=ex["outcomes"])

ju = result.library.units[0]
print(ju.decision)             # what the expert does
print(ju.rationale)            # the recovered *why*
print(ju.reversal_conditions)  # when the judgment flips
print(ju.autonomy)             # earned trust tier after the outcome
```

### Do I have to use an LLM to extract?

**No.** OBSERVE, the baseline elicitation interview, deterministic induction, ACT
compilation and heuristic attribution all run with no model. An LLM only *raises
the ceiling* of ELICIT (probe wording) and INDUCE (structuring free-text). Enable
it when you have one and are allowed to use it:

```bash
export OPENFDE_LLM_BASE_URL=https://api.openai.com/v1   # any OpenAI-compatible gateway
export OPENFDE_LLM_API_KEY=sk-...
export OPENFDE_LLM_MODEL=gpt-4o-mini
pip install 'openfde[llm]'
openfde loop --example sales-qualification --llm
```

Secrets are only ever read from the environment — never written into a repo, a
Judgment Unit, or a connector spec.

## Open core, and the boundary

OpenFDE open-sources the **protocols and algorithms**; the compounding **assets
and signals** are the commercial moat. The boundary is expressed in code as four
plugin seams (`openfde/plugins`), each shipping a working open baseline:

| seam | open baseline (this repo) | moat (plugs in behind the same interface) |
|------|---------------------------|--------------------------------------------|
| `MomentRanker` | cue-count heuristic | attribution-fed cross-client moment ranking |
| `StopCriterion` | coverage + marginal-info | tuned real-time 8-dimension stop policy |
| `MoveLibrary` | CDM sweep templates | tuned Move library (wording, order, adaptivity) |
| `AttributionEngine` | recency-weighted heuristic | delayed/noisy long-horizon credit + incrementality |

> The standard is open so the ecosystem grows around it. What is not copyable is
> the expert Move library, the industry judgment structures, and the real
> business-outcome attribution signal.

## Where it plugs into the ecosystem

OpenFDE orchestrates, it does not re-implement. Adapters target **verified**
public APIs and are optional (`pip install 'openfde[...]'`):

- **ACT** → Pydantic AI / LangGraph / ADK / Agents SDK (`openfde/loop/act.py:to_pydantic_ai`)
- **EVOLVE** → GEPA (`GEPAAdapter`, `openfde/loop/evolve.py`) · DSPy
- **INDUCE storage** → Graphiti (temporal graph) · Mem0 (memory) — JU is the layer *above* them
- **OBSERVE** → Langfuse / OpenTelemetry / rrweb (Trace is a thin superset)
- **ATTRIBUTION** → DoWhy / EconML (causal) — the ledger is append-only, ProjectMem-style

See [`SPEC.md`](./SPEC.md) for the Judgment Unit Schema and the Elicitation
Protocol, and [`DESIGN.md`](./DESIGN.md) for the full "what do enterprise
customers actually need" rationale with sources.

## Layout

```
openfde/
  schema/       Judgment Unit ⭐, Trace/CriticalIncident, Elicitation, Attribution, Connector
  loop/         observe · elicit · induce · act · evolve  (+ run_loop orchestrator)
  planes/       deploy (connector registry + reference connectors) · attribution (ledger)
  plugins/      the four moat seams + open baselines
  llm/          optional OpenAI-compatible client (graceful offline fallback)
  cli.py        openfde loop | observe | init | schema | version
examples/       sales-qualification (synthetic, desensitized)
tests/          offline end-to-end smoke tests
```

## Status

v0.1 — a runnable reference implementation of the loop and the two flagship
standards. It is intentionally thin: the point of v1 is to make the *protocol*
concrete and correct, not to ship a runtime. Not affiliated with Palantir /
OpenAI / Anthropic / Google. Code: MIT.
