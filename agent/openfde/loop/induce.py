"""INDUCE — compile a trace + elicitation transcript into a Judgment Unit.

This is where OpenFDE refuses to be "another memory/RAG layer". Mem0/LangMem
manage memory; Graphiti builds temporal graphs; AWM induces reusable
*workflows*. INDUCE produces a **Judgment Unit**: a decision, the signals that
trigger it, the elicited rationale, the alternatives, the reversal conditions,
the autonomy it may act at, and a slot for its business outcome.

Two extractors, same output:
  * a deterministic extractor that maps each answered move to a JU field via
    its declared `extracts_to` target — reproducible, offline, model-free;
  * an optional LLM extractor that reads the whole transcript and returns the
    same structured fields — higher quality when a model is available.

"Do we have to use an LLM to extract?" — No. The deterministic path always runs
and is what the reference example uses.
"""
from __future__ import annotations

import json
import re
from typing import List, Optional

from ..llm import LLMClient
from ..plugins import DEFAULT_STOP_CRITERION, StopCriterion
from ..schema.elicitation import ElicitationSession, Probe
from ..schema.judgment_unit import (
    Alternative,
    Autonomy,
    JudgmentUnit,
    Provenance,
    Signal,
)
from ..schema.trace import CriticalIncident, Trace

# General splitter for lists (options, reversal conditions, cues-to-watch).
_SPLIT = re.compile(r"[;\n]|(?:,\s)|(?:\band\b)|(?:、)|(?:；)")
# Conservative splitter for signals: clause boundaries only, so a single signal
# phrase ("a fast, specific first reply") is not shredded into fragments.
_CLAUSE = re.compile(r"[;\n]|(?:；)|(?:。)")


def _answers_for(session: ElicitationSession, field: str) -> List[str]:
    return [m.answer.strip() for m in session.answered_moves() if m.extracts_to == field and m.answer]


def _answers_by_probe(session: ElicitationSession, *probes: Probe) -> List[str]:
    want = set(probes)
    return [m.answer.strip() for m in session.answered_moves() if m.probe in want and m.answer]


def _split_phrases(text: str) -> List[str]:
    parts = [p.strip(" .,-–—") for p in _SPLIT.split(text) if p and p.strip(" .,-–—")]
    return [p for p in parts if len(p) > 3]


def _split_clauses(text: str) -> List[str]:
    parts = [p.strip(" .,-–—") for p in _CLAUSE.split(text) if p and p.strip(" .,-–—")]
    return [p for p in parts if len(p) > 3]


def induce_deterministic(
    session: ElicitationSession,
    incident: CriticalIncident,
    *,
    decision: Optional[str] = None,
    domain: str = "general",
    title: Optional[str] = None,
    trace: Optional[Trace] = None,
    stop: StopCriterion = DEFAULT_STOP_CRITERION,
) -> JudgmentUnit:
    """Map the transcript into a Judgment Unit with no model in the loop."""
    trigger = " ".join(_answers_for(session, "trigger")) or incident.summary or "when the flagged situation recurs"
    preconditions = _split_phrases(" ".join(_answers_for(session, "preconditions")))

    signal_text = " ".join(_answers_by_probe(session, Probe.CUES))
    why_signals = " ".join(_answers_by_probe(session, Probe.ASSESSMENT))
    signals = [
        Signal(name=phrase, why_it_matters=why_signals or None, importance=0.6)
        for phrase in _split_clauses(signal_text)[:6]
    ]

    rationale = " ".join(
        _answers_by_probe(
            session, Probe.ASSESSMENT, Probe.GOALS, Probe.ANALOGUES, Probe.STANDARD, Probe.STAKES
        )
    ).strip()

    alternatives = [
        Alternative(option=phrase, rejected_because="see expert rationale")
        for phrase in _split_phrases(" ".join(_answers_by_probe(session, Probe.OPTIONS)))[:4]
    ]

    reversal = _split_phrases(" ".join(_answers_for(session, "reversal_conditions")))
    cues_to_watch = _split_phrases(" ".join(_answers_by_probe(session, Probe.EXPECTANCY)))

    if not decision and trace is not None:
        dec_events = [e for e in trace.events if e.type.value == "decision"]
        if dec_events:
            decision = dec_events[-1].content
    decision = decision or incident.summary or "apply the expert's judgment"

    snap = stop.score(session)
    ju = JudgmentUnit(
        title=title or (decision[:60] if decision else "expert judgment"),
        domain=domain,
        trigger=trigger,
        signals=signals,
        preconditions=preconditions,
        decision=decision,
        rationale=rationale,
        alternatives=alternatives,
        reversal_conditions=reversal,
        cues_to_watch=cues_to_watch,
        autonomy=Autonomy.SUGGEST,   # every JU starts at suggest; trust is earned via ATTRIBUTION
        confidence=round(0.3 + 0.6 * snap.readiness(), 3),
        evidence_count=1,
        stop_snapshot=snap,
        provenance=Provenance(
            trace_id=session.trace_id,
            incident_id=incident.id,
            elicitation_id=session.id,
            expert_id=session.expert_id,
        ),
        tags=[c.value for c in incident.cues],
    )
    return ju.ensure_id()


_LLM_SYSTEM = (
    "You compile an expert-knowledge interview into ONE Judgment Unit as strict JSON. "
    "A Judgment Unit captures a decision and the tacit reasoning behind it. "
    "Return ONLY a JSON object with keys: title, trigger, signals (list of {name, why_it_matters}), "
    "decision, rationale, alternatives (list of {option, rejected_because}), reversal_conditions (list), "
    "cues_to_watch (list). Be faithful to the transcript; do not invent facts."
)


def induce_llm(
    session: ElicitationSession,
    incident: CriticalIncident,
    llm: LLMClient,
    *,
    domain: str = "general",
    decision: Optional[str] = None,
    stop: StopCriterion = DEFAULT_STOP_CRITERION,
) -> Optional[JudgmentUnit]:
    """Higher-quality extraction when a model is configured. Returns None on failure."""
    if not llm.enabled:
        return None
    data = llm.json(
        [
            {"role": "system", "content": _LLM_SYSTEM},
            {
                "role": "user",
                "content": f"Moment: {incident.summary}\n\nInterview transcript:\n{session.transcript()}",
            },
        ]
    )
    if not data:
        return None
    snap = stop.score(session)
    try:
        ju = JudgmentUnit(
            title=data.get("title") or (decision or incident.summary or "expert judgment")[:60],
            domain=domain,
            trigger=data.get("trigger") or incident.summary or "",
            signals=[
                Signal(name=s.get("name", ""), why_it_matters=s.get("why_it_matters"), importance=0.6)
                for s in data.get("signals", [])
                if s.get("name")
            ],
            decision=decision or data.get("decision") or "apply the expert's judgment",
            rationale=data.get("rationale", ""),
            alternatives=[
                Alternative(option=a.get("option", ""), rejected_because=a.get("rejected_because"))
                for a in data.get("alternatives", [])
                if a.get("option")
            ],
            reversal_conditions=[r for r in data.get("reversal_conditions", []) if r],
            cues_to_watch=[c for c in data.get("cues_to_watch", []) if c],
            autonomy=Autonomy.SUGGEST,
            confidence=round(0.35 + 0.6 * snap.readiness(), 3),
            evidence_count=1,
            stop_snapshot=snap,
            provenance=Provenance(
                trace_id=session.trace_id,
                incident_id=incident.id,
                elicitation_id=session.id,
                expert_id=session.expert_id,
            ),
            tags=[c.value for c in incident.cues],
        )
        return ju.ensure_id()
    except (TypeError, ValueError):
        return None


def induce(
    session: ElicitationSession,
    incident: CriticalIncident,
    *,
    decision: Optional[str] = None,
    domain: str = "general",
    title: Optional[str] = None,
    trace: Optional[Trace] = None,
    llm: Optional[LLMClient] = None,
    stop: StopCriterion = DEFAULT_STOP_CRITERION,
) -> JudgmentUnit:
    """INDUCE step: prefer the LLM extractor when available, else deterministic."""
    llm = llm or LLMClient()
    if llm.enabled:
        ju = induce_llm(session, incident, llm, domain=domain, decision=decision, stop=stop)
        if ju is not None:
            return ju
    return induce_deterministic(
        session, incident, decision=decision, domain=domain, title=title, trace=trace, stop=stop
    )
