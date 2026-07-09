"""The Apprentice Loop — OBSERVE → ELICIT → INDUCE → ACT → EVOLVE.

This module orchestrates the five steps over the two planes (DEPLOY provides
connectors; ATTRIBUTION provides the outcome ledger). Each step is independently
usable; `run_loop` wires them into one pass for the reference example, tests and
the `openfde loop` command.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ..llm import LLMClient
from ..planes.attribution import OutcomeLedger
from ..schema.attribution import ActionRecord, Outcome
from ..schema.connector import ConnectorSpec
from ..schema.elicitation import ElicitationSession
from ..schema.judgment_unit import JudgmentLibrary
from ..schema.trace import CriticalIncident, Trace
from .act import AgentConfig, compile_judgments
from .elicit import AnswerProvider, elicit
from .evolve import EvolveReport, evolve
from .induce import induce
from .observe import observe

__all__ = [
    "observe",
    "elicit",
    "induce",
    "compile_judgments",
    "evolve",
    "AgentConfig",
    "LoopResult",
    "run_loop",
]


@dataclass
class LoopResult:
    incidents: List[CriticalIncident] = field(default_factory=list)
    sessions: List[ElicitationSession] = field(default_factory=list)
    library: JudgmentLibrary = field(default_factory=JudgmentLibrary)
    agent_config: Optional[AgentConfig] = None
    ledger: Optional[OutcomeLedger] = None
    evolve_report: Optional[EvolveReport] = None


def run_loop(
    trace: Trace,
    answers: AnswerProvider,
    *,
    project: str = "untitled",
    domain: str = "general",
    connectors: Optional[List[ConnectorSpec]] = None,
    max_incidents: int = 3,
    decisions: Optional[dict] = None,
    actions: Optional[List[ActionRecord]] = None,
    outcomes: Optional[List[Outcome]] = None,
    ledger_path: Optional[str] = None,
    llm: Optional[LLMClient] = None,
) -> LoopResult:
    """Run one full pass of the Apprentice Loop.

    OBSERVE + ELICIT + INDUCE + ACT always run. ATTRIBUTION + EVOLVE run when
    `actions`/`outcomes` are supplied (the example provides synthetic ones).
    `decisions` optionally maps incident_id -> decision text to seed INDUCE.
    """
    llm = llm or LLMClient()
    decisions = decisions or {}
    result = LoopResult(library=JudgmentLibrary(project=project, domain=domain))

    # 1. OBSERVE
    result.incidents = observe(trace)[:max_incidents]

    # 2-3. ELICIT + INDUCE, per incident
    for incident in result.incidents:
        session = elicit(
            incident, answers, expert_id=trace.actor, project=project, llm=llm
        )
        result.sessions.append(session)
        ju = induce(
            session,
            incident,
            decision=decisions.get(incident.id),
            domain=domain,
            trace=trace,
            llm=llm,
        )
        result.library.add(ju)

    # 4. ACT
    result.agent_config = compile_judgments(
        result.library, connectors or [], project=project, domain=domain, include_drafts=True
    )

    # 5 + ATTRIBUTION plane
    if actions or outcomes:
        ledger = OutcomeLedger(path=ledger_path)
        primary = result.library.units[0].id if result.library.units else ""
        for action in actions or []:
            # Convenience: a blank ju_id means "the primary induced JU", whose
            # content-addressed id isn't known until after INDUCE has run.
            if not action.ju_id:
                action.ju_id = primary
            ledger.record_action(action)
        for outcome in outcomes or []:
            ledger.record_outcome(outcome)
        ledger.fold_into_library(result.library)
        result.ledger = ledger
        result.evolve_report = evolve(result.library)

    return result
