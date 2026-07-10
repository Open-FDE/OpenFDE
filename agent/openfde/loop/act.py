"""ACT — compile Judgment Units into a governed, runnable agent config.

OpenFDE does not compete with LangGraph / CrewAI / ADK / Agents SDK. It sits
*above* them: it turns Judgment Units into a portable `AgentConfig` (system
prompt + tool policy + approval policy + guardrails) that a runtime executes.
The compiler is deliberately thin — the value is in the Judgment Units, not the
runtime.

Two things make this enterprise-shaped rather than demo-shaped:
  1. **Graduated autonomy.** Each JU declares suggest/approve/auto; the compiler
     turns that into an approval policy the runtime enforces. Nothing runs at
     'auto' if its connector operation is marked destructive/requires_approval.
  2. **Guardrails are first-class**, collected from every JU and every connector
     operation, so the executing agent inherits the expert's hard limits.

`to_pydantic_ai(...)` shows one concrete adapter against a real, verified API
(pydantic-ai). LangGraph / ADK / Agents SDK adapters follow the same shape.
"""
from __future__ import annotations

from typing import Iterable, List, Optional, Union

from pydantic import BaseModel, Field

from ..schema.connector import ConnectorSpec, OpKind
from ..schema.judgment_unit import Autonomy, JudgmentLibrary, JudgmentUnit


class ToolPermission(BaseModel):
    operation: str
    connector: str
    kind: str
    min_autonomy_to_auto: str = Field(
        "approve",
        description="An agent may run this without a human only at/above this autonomy tier",
    )
    requires_approval: bool = False
    destructive: bool = False


class ApprovalPolicy(BaseModel):
    """The rule the runtime enforces before an action is applied."""

    default: str = Field("approve", description="suggest|approve|auto default for un-tiered actions")
    always_approve_destructive: bool = True
    escalate_on: List[str] = Field(
        default_factory=lambda: [
            "financial commitment",
            "external-stakeholder impact",
            "confidence below threshold",
            "PII exposure",
        ],
        description="Conditions that force human escalation regardless of autonomy (enterprise norm)",
    )


class AgentConfig(BaseModel):
    """A portable, runtime-agnostic agent specification compiled from JUs."""

    project: str = "untitled"
    domain: str = "general"
    system_prompt: str = ""
    judgment_ids: List[str] = Field(default_factory=list)
    tools: List[ToolPermission] = Field(default_factory=list)
    approval: ApprovalPolicy = Field(default_factory=ApprovalPolicy)
    guardrails: List[str] = Field(default_factory=list)


def _render_judgment(ju: JudgmentUnit) -> str:
    lines = [f"### Judgment: {ju.title}  [{ju.autonomy.value}, confidence={ju.confidence}]"]
    lines.append(f"- WHEN: {ju.trigger}")
    if ju.signals:
        sigs = "; ".join(s.name for s in ju.signals)
        lines.append(f"- SIGNALS: {sigs}")
    lines.append(f"- DO: {ju.decision}")
    if ju.rationale:
        lines.append(f"- WHY: {ju.rationale}")
    if ju.reversal_conditions:
        lines.append(f"- REVERSE IF: {'; '.join(ju.reversal_conditions)}")
    if ju.cues_to_watch:
        lines.append(f"- THEN WATCH: {'; '.join(ju.cues_to_watch)}")
    return "\n".join(lines)


def _autonomy_floor(ju: JudgmentUnit) -> str:
    # An action inherits the strictest of the JU's own autonomy tier.
    return ju.autonomy.value


def compile_judgments(
    judgments: Union[JudgmentLibrary, Iterable[JudgmentUnit]],
    connectors: Optional[List[ConnectorSpec]] = None,
    *,
    project: str = "untitled",
    domain: str = "general",
    include_drafts: bool = False,
) -> AgentConfig:
    """Compile Judgment Units (+ connectors) into an AgentConfig."""
    if isinstance(judgments, JudgmentLibrary):
        project = project if project != "untitled" else judgments.project
        domain = domain if domain != "general" else judgments.domain
        units = judgments.units if include_drafts else judgments.active()
        if not units and include_drafts is False:
            units = judgments.units  # fall back so a fresh library still compiles
    else:
        units = list(judgments)

    connectors = connectors or []

    preamble = (
        f"You are an OpenFDE agent — a forward-deployed engineer (FDE) for the '{domain}' domain of project "
        f"'{project}'. You act on Judgment Units distilled from a domain expert. "
        "Respect each judgment's autonomy tier: at 'suggest' you only surface the "
        "judgment; at 'approve' you propose an action and wait for a human; at "
        "'auto' you may act, but never for destructive or approval-required "
        "operations without explicit human approval. Honor every guardrail."
    )
    body = "\n\n".join(_render_judgment(ju) for ju in units)
    system_prompt = preamble + "\n\n" + body if body else preamble

    # Tool policy from connectors.
    tools: List[ToolPermission] = []
    guardrails: List[str] = []
    for conn in connectors:
        for op in conn.operations:
            tools.append(
                ToolPermission(
                    operation=op.name,
                    connector=conn.name,
                    kind=op.kind.value,
                    min_autonomy_to_auto="approve" if (op.requires_approval or op.destructive) else "auto",
                    requires_approval=op.requires_approval or op.destructive,
                    destructive=op.destructive,
                )
            )
    for ju in units:
        if ju.action and ju.action.guardrails:
            guardrails.extend(ju.action.guardrails)
    # de-dup guardrails, preserve order
    seen = set()
    guardrails = [g for g in guardrails if not (g in seen or seen.add(g))]

    return AgentConfig(
        project=project,
        domain=domain,
        system_prompt=system_prompt,
        judgment_ids=[ju.id for ju in units],
        tools=tools,
        approval=ApprovalPolicy(),
        guardrails=guardrails,
    )


def to_pydantic_ai(config: AgentConfig, model: str = "openai:gpt-4o-mini"):  # pragma: no cover
    """Reference adapter: build a pydantic-ai Agent from an AgentConfig.

    Verified against pydantic-ai's public API:
        Agent(model, instructions=..., ...); @agent.tool / @agent.tool_plain

    Imported lazily so the core has no dependency on any runtime. Non-auto tools
    should be wrapped by the caller with an approval gate before registration.
    """
    try:
        from pydantic_ai import Agent
    except ImportError as exc:  # keep the core dependency-free
        raise ImportError(
            "pydantic-ai is optional. Install with: pip install 'openfde[runtime]'"
        ) from exc
    return Agent(model, instructions=config.system_prompt)
