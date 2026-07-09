"""ELICIT — run the Elicitation Protocol around a critical incident.

This is the flagship: an active interview that recovers the expert's tacit
*why*. It is a state machine that repeatedly (1) asks a Move Library for the
next question, (2) obtains the expert's answer, (3) estimates how much new
information that answer carried, and (4) asks a Stop Criterion whether enough
judgment has been recovered.

Who answers? In a live deployment, the expert does (via chat, voice, or a
trace-replay UI). Offline — for the reference example and tests — a scripted
transcript answers, so the whole loop reproduces without a human or a model.

An optional LLM can sharpen question wording (LLMREI's finding: an LLM makes a
competent requirements interviewer). It never gates the loop.
"""
from __future__ import annotations

import re
from typing import Callable, Dict, Optional, Protocol, runtime_checkable

from ..llm import LLMClient
from ..plugins import (
    DEFAULT_MOVE_LIBRARY,
    DEFAULT_STOP_CRITERION,
    MoveLibrary,
    StopCriterion,
)
from ..schema.elicitation import ElicitationMove, ElicitationSession, StopReason
from ..schema.trace import CriticalIncident

_WORD = re.compile(r"[a-zA-Z一-鿿]{2,}")


@runtime_checkable
class AnswerProvider(Protocol):
    """Something that can answer an elicitation move as the expert would."""

    def answer(self, move: ElicitationMove, incident: CriticalIncident) -> Optional[str]:
        ...


class ScriptedAnswerProvider:
    """Answers from a canned transcript — used offline and in tests.

    Keys are matched against the move's target field (`extracts_to`) first, then
    its probe name, so a single dict can drive a full CDM sweep.
    """

    def __init__(self, answers: Dict[str, str]):
        self.answers = answers

    def answer(self, move: ElicitationMove, incident: CriticalIncident) -> Optional[str]:
        for key in (move.extracts_to, move.probe.value, move.phase.value):
            if key and key in self.answers:
                return self.answers[key]
        return None


class CallableAnswerProvider:
    """Wraps any callable(question) -> answer, e.g. a live chat prompt."""

    def __init__(self, fn: Callable[[str], Optional[str]]):
        self.fn = fn

    def answer(self, move: ElicitationMove, incident: CriticalIncident) -> Optional[str]:
        return self.fn(move.question)


def _info_gain(answer: str, seen_tokens: set) -> float:
    """Fraction of the answer's content words not seen in prior answers, 0..1."""
    if not answer or not answer.strip():
        return 0.0
    toks = {t.lower() for t in _WORD.findall(answer)}
    if not toks:
        return 0.0
    new = toks - seen_tokens
    return round(len(new) / len(toks), 3)


def _refine_question(llm: LLMClient, move: ElicitationMove, incident: CriticalIncident) -> str:
    """Optionally rephrase a probe to fit the concrete moment (LLM, best-effort)."""
    if not llm.enabled:
        return move.question
    reply = llm.chat(
        [
            {
                "role": "system",
                "content": (
                    "You are an expert-knowledge interviewer using the Critical Decision Method. "
                    "Rewrite the given probe as ONE short, concrete, non-leading question about the "
                    "specific moment. Return only the question."
                ),
            },
            {
                "role": "user",
                "content": f"Moment: {incident.summary}\nProbe type: {move.probe.value}\nGeneric probe: {move.question}",
            },
        ],
        temperature=0.3,
        max_tokens=120,
    )
    return (reply or move.question).strip()


def elicit(
    incident: CriticalIncident,
    answers: AnswerProvider,
    *,
    expert_id: Optional[str] = None,
    project: str = "untitled",
    library: MoveLibrary = DEFAULT_MOVE_LIBRARY,
    stop: StopCriterion = DEFAULT_STOP_CRITERION,
    llm: Optional[LLMClient] = None,
    max_moves: int = 12,
) -> ElicitationSession:
    """Conduct one elicitation session and return the completed transcript."""
    llm = llm or LLMClient()
    session = ElicitationSession(
        incident_id=incident.id,
        trace_id=incident.trace_id,
        expert_id=expert_id,
        project=project,
    ).ensure_id()

    seen_tokens: set = set()

    while len(session.moves) < max_moves:
        move = library.next_move(session, incident)
        if move is None:
            session.status = StopReason.SATURATED
            break

        move.question = _refine_question(llm, move, incident)
        reply = answers.answer(move, incident)
        move.answer = reply
        move.info_gain = _info_gain(reply or "", seen_tokens)
        if reply:
            seen_tokens |= {t.lower() for t in _WORD.findall(reply)}
        session.phase = move.phase
        session.add(move)

        if stop.should_stop(session):
            snap = stop.score(session)
            session.status = (
                StopReason.READY if snap.readiness() >= 0.7 else StopReason.SATURATED
            )
            break
    else:
        session.status = StopReason.MAX_MOVES

    return session
