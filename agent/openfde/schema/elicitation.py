"""ELICIT schema — the Elicitation Protocol.

ELICIT is the emptiest category in today's open-source agent ecosystem. There
are interview tools, labeling tools and feedback collectors, but no open
*protocol* for actively recovering an expert's tacit reasoning around a
critical moment. OpenFDE stakes this category.

The protocol is grounded in the **Critical Decision Method** (Klein, Calderwood
& MacGregor, 1989) and **Cognitive Task Analysis** (Hoffman, Crandall &
Shadbolt, 1998): sweep the incident, verify a timeline, then deepen with
cognitive probes that target the *cues, goals, options, expectancies, analogues
and mental models* behind the decision — the elements plain observation cannot
see.

    Observation gives you the *what*; elicitation recovers the *why*.

Open in this repo: the protocol, the move taxonomy, a baseline Move Library,
and the stop-criterion interface. Closed (the moat): the tuned Move Library and
the 8-dimension real-time stop policy — see openfde/plugins.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Phase(str, Enum):
    """The four CDM sweeps, adapted for on-site agent elicitation."""

    INCIDENT = "incident"        # sweep 1: identify & bound the critical incident
    TIMELINE = "timeline"        # sweep 2: reconstruct the sequence of events
    DEEPEN = "deepen"            # sweep 3: cognitive probes (the core of CDM)
    WHATIF = "whatif"            # sweep 4: hypotheticals / expert-novice contrast


class Probe(str, Enum):
    """What tacit element a move targets. This is the open move *taxonomy*.

    Drawn from CDM cognitive probes. The tuned realization of each probe (exact
    wording, ordering, adaptivity) is the closed Move Library.
    """

    CUES = "cues"                    # "What did you notice? What were you seeing/hearing?"
    KNOWLEDGE = "knowledge"          # "What information did you use?"
    GOALS = "goals"                  # "What were your goals at that moment?"
    OPTIONS = "options"              # "What other choices did you have?"
    ASSESSMENT = "assessment"        # "How did you size up the situation?"
    ANALOGUES = "analogues"          # "Were you reminded of a previous experience?"
    EXPECTANCY = "expectancy"        # "What did you expect to happen next?"
    MENTAL_MODEL = "mental_model"    # "What was your mental picture of what was going on?"
    REVERSAL = "reversal"            # "What would have made you decide differently?"
    STAKES = "stakes"                # "What was at risk if you got it wrong?"
    STANDARD = "standard"            # "Is there a rule of thumb here? Would a novice miss it?"


class ElicitationMove(BaseModel):
    """One question asked of the expert, and their answer.

    A 'move' is the unit of the Elicitation Protocol — analogous to a chess
    move: it is a deliberate act chosen from a library to advance the state of
    the elicitation toward a well-formed Judgment Unit.
    """

    id: str = Field(default="")
    phase: Phase = Phase.DEEPEN
    probe: Probe = Probe.CUES
    question: str
    answer: Optional[str] = Field(None, description="Expert's response; None until answered")
    # what the answer contributed to the emerging Judgment Unit
    extracts_to: Optional[str] = Field(
        None, description="JU field this move feeds: signals|rationale|alternatives|reversal_conditions|..."
    )
    info_gain: float = Field(
        0.0, ge=0.0, le=1.0, description="Estimated new information from this move (feeds the stop policy)"
    )
    asked_at: datetime = Field(default_factory=_utcnow)

    def ensure_id(self, seq: int = 0) -> "ElicitationMove":
        if not self.id:
            self.id = f"mv_{seq:04d}"
        return self

    @property
    def answered(self) -> bool:
        return bool(self.answer and self.answer.strip())


class StopReason(str, Enum):
    SATURATED = "saturated"          # marginal info gain fell below threshold
    READY = "ready"                  # 8-dim readiness reached target
    MAX_MOVES = "max_moves"          # hit the budget
    EXPERT_ENDED = "expert_ended"    # expert stopped (fatigue/time)
    OPEN = "open"                    # session still in progress


class ElicitationSession(BaseModel):
    """A structured interview around one critical incident.

    Runs as a state machine (INCIDENT -> TIMELINE -> DEEPEN -> WHATIF), issuing
    moves until a stop criterion fires. The resulting transcript is the raw
    material INDUCE compiles into a Judgment Unit.
    """

    id: str = Field(default="")
    incident_id: str
    trace_id: Optional[str] = None
    expert_id: Optional[str] = None
    project: str = "untitled"
    phase: Phase = Phase.INCIDENT
    moves: List[ElicitationMove] = Field(default_factory=list)
    status: StopReason = StopReason.OPEN
    started_at: datetime = Field(default_factory=_utcnow)

    def ensure_id(self) -> "ElicitationSession":
        if not self.id:
            basis = f"{self.incident_id}|{self.expert_id}".encode("utf-8")
            self.id = "el_" + hashlib.sha1(basis).hexdigest()[:12]
        for i, mv in enumerate(self.moves):
            mv.ensure_id(i)
        return self

    def add(self, move: ElicitationMove) -> ElicitationMove:
        move.ensure_id(len(self.moves))
        self.moves.append(move)
        return move

    def answered_moves(self) -> List[ElicitationMove]:
        return [m for m in self.moves if m.answered]

    def probes_covered(self) -> set:
        return {m.probe for m in self.answered_moves()}

    def transcript(self) -> str:
        lines = []
        for m in self.moves:
            lines.append(f"[{m.phase.value}/{m.probe.value}] Q: {m.question}")
            if m.answered:
                lines.append(f"    A: {m.answer}")
        return "\n".join(lines)
