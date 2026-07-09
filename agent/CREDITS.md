# Credits & prior art

OpenFDE Agent stands on an existing ecosystem. Per the project's principle
(*orchestrate, don't rebuild*), the core vendors **no** third-party code — it
adapts ideas and targets public APIs through optional, clearly-marked seams. This
file credits the projects that informed the design and records their licenses, so
integration stays honest and license-clean.

## Ideas & methods adapted

| project | license | how OpenFDE relates |
|---------|---------|---------------------|
| [AWM — Agent Workflow Memory](https://github.com/zorazrw/agent-workflow-memory) | Apache-2.0 | INDUCE's inspiration. AWM induces reusable *workflows* from experience (prompt-based). OpenFDE induces *judgments* (the why/when), a different object. |
| [ProjectMem](https://github.com/riponcm/projectmem) | MIT | The append-only, event-sourced ledger discipline (typed events, deterministic projection, nothing overwritten) informed the ATTRIBUTION ledger and JU provenance. |
| [GEPA](https://github.com/gepa-ai/gepa) | MIT | EVOLVE. `openfde/loop/evolve.py:GEPAAdapter` targets GEPA's documented `GEPAAdapter` protocol (`evaluate` + `make_reflective_dataset`) and `gepa.optimize`. |
| [LLMREI](https://arxiv.org/abs/2507.02564) | replication pkg (license unverified) | ELICIT. Reference-only: its finding that an LLM can conduct a competent requirements interview, and its short/long prompt strategies. No code reused. |
| Critical Decision Method (Klein et al. 1989); Cognitive Task Analysis (Hoffman, Crandall & Shadbolt 1998) | academic | The Elicitation Protocol's four sweeps and cognitive-probe taxonomy. |

## Runtime & storage adapters (optional, targeted by public API)

| project | license | seam |
|---------|---------|------|
| [Pydantic AI](https://github.com/pydantic/pydantic-ai) | MIT | ACT runtime (`to_pydantic_ai`) |
| [LangGraph](https://github.com/langchain-ai/langgraph) / [ADK](https://github.com/google/adk-python) / [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | MIT / Apache-2.0 | ACT runtimes (same adapter shape) |
| [Graphiti](https://github.com/getzep/graphiti) | Apache-2.0 | INDUCE storage (temporal graph) |
| [Mem0](https://github.com/mem0ai/mem0) | Apache-2.0 | memory layer beneath JUs |
| [DSPy](https://github.com/stanfordnlp/dspy) | MIT | alternative optimizer for EVOLVE |
| [Langfuse](https://github.com/langfuse/langfuse) / OpenTelemetry / [rrweb](https://github.com/rrweb-io/rrweb) | MIT / Apache-2.0 | OBSERVE ingest (Trace is a thin superset) |
| [DoWhy](https://github.com/py-why/dowhy) / [EconML](https://github.com/py-why/EconML) | MIT | causal ATTRIBUTION engine |
| [MCP](https://github.com/modelcontextprotocol) / [Composio](https://github.com/composiohq/composio) / [Temporal](https://github.com/temporalio/temporal) | MIT / Apache / MIT | DEPLOY connectors |

If any adapter later vendors code from an Apache-2.0 project, its `NOTICE` and
attribution will be added here and the source retained per the license. All
projects above were confirmed MIT or Apache-2.0 except LLMREI's replication
package, which is kept reference-only pending a license check.
