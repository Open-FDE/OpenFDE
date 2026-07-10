# Example: sales-qualification

A synthetic, fully **desensitized** scenario — no real customer data — that drives
the whole FDE Loop end to end. Run it:

```bash
openfde loop --example sales-qualification
```

## The scenario

A senior account executive (`expert:chen`) gets an inbound lead (`lead:4821`): a
40-person QA team at a 600-person manufacturer, with a hard 6-week deadline. The
company's auto-routing would send a 40-seat pilot to SMB self-serve. The expert
**overrides** that: a small team inside a large company plus a dated compelling
event signals *land-and-expand*, so they qualify it as an Enterprise opportunity
and push for a scoping call this week.

That override is exactly the kind of moment plain observation records but does not
understand. The loop:

1. **OBSERVE** — flags the moment (cues: `override`, `explicit_decision`,
   `high_stakes`, `hesitation`).
2. **ELICIT** — runs a Critical-Decision-Method interview and recovers the *why*.
3. **INDUCE** — compiles it into a Judgment Unit (see `expected-judgment.json`) —
   note the **reversal conditions**: *if the parent company were small, or there
   were no deadline and the reply were vague, route to SMB.*
4. **ACT** — compiles a governed agent config; the CRM write op is approval-gated.
5. **ATTRIBUTION + EVOLVE** — a synthetic closed-deal outcome credits the judgment,
   which earns a promotion from `suggest` to `approve`.

## Files

| file | what it is |
|------|------------|
| `trace.jsonl` | the expert's work trace (try `openfde observe trace.jsonl`) |
| `outcomes.jsonl` | the synthetic business outcome (deal closed) |
| `expected-judgment.json` | the Judgment Unit the loop induces (generated from code) |
| `project.yaml` | the blueprint header (as `openfde init` would scaffold) |

The canonical, runnable definition lives in `openfde/_examples.py` so the CLI and
tests share one source of truth; these files are readable projections of it.

## The elicited *why*, in the expert's words

> *"Qualify on the company behind the team, not the team size; a dated compelling
> event beats any lead score. Mis-routing a land-and-expand deal to self-serve can
> cost a six-figure expansion."*

That sentence is tacit knowledge. It never appears in the trace. Elicitation is
the only way to get it — and a Judgment Unit is the only artifact here that keeps
it.
