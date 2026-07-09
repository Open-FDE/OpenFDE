"""OBSERVE schema — expert work trajectories and the critical incidents in them.

A Trace is a normalized record of *what happened*: an expert's messages, tool
calls, edits and decisions, in order. It is intentionally shaped to be a thin
superset of what Langfuse / OpenTelemetry / rrweb already emit, so OpenFDE
ingests those rather than re-inventing observability.

The OpenFDE-specific idea lives in `CriticalIncident`: not every recorded
moment is equal. Most of an expert's day is routine; expertise hides in a few
*critical incidents* — hesitations, corrections, overrides, deviations. OBSERVE
flags candidates; ELICIT then probes them.

    These projects record 'what happened'; they do not decide which moments
    hid a judgment. That ranking is OpenFDE's job (baseline open; the tuned
    cross-client moment ranker is the moat — see plugins).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EventType(str, Enum):
    MESSAGE = "message"          # expert or counterparty utterance
    TOOL_CALL = "tool_call"      # expert (or their tools) invoked something
    TOOL_RESULT = "tool_result"
    EDIT = "edit"                # a document/record was changed
    DECISION = "decision"        # an explicit choice was made
    USER_ACTION = "user_action"  # UI action (from rrweb/OpenReplay-style capture)
    NOTE = "note"


class TraceEvent(BaseModel):
    id: str = Field(default="")
    ts: datetime = Field(default_factory=_utcnow)
    type: EventType = EventType.MESSAGE
    actor: Optional[str] = Field(None, description="Who produced this event")
    content: str = Field("", description="Human-readable content of the event")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def ensure_id(self, seq: int = 0) -> "TraceEvent":
        if not self.id:
            self.id = f"ev_{seq:04d}"
        return self


class Trace(BaseModel):
    """One episode of observed expert work."""

    id: str = Field(default="")
    project: str = "untitled"
    actor: Optional[str] = Field(None, description="Expert being observed")
    source: Optional[str] = Field(None, description="Where captured: 'langfuse' | 'rrweb' | 'manual' ...")
    events: List[TraceEvent] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def ensure_ids(self) -> "Trace":
        if not self.id:
            basis = f"{self.project}|{self.actor}|{len(self.events)}".encode("utf-8")
            self.id = "tr_" + hashlib.sha1(basis).hexdigest()[:12]
        for i, ev in enumerate(self.events):
            ev.ensure_id(i)
        return self

    def event(self, event_id: str) -> Optional[TraceEvent]:
        return next((e for e in self.events if e.id == event_id), None)

    def span(self, start_id: str, end_id: str) -> List[TraceEvent]:
        ids = [e.id for e in self.events]
        try:
            i, j = ids.index(start_id), ids.index(end_id)
        except ValueError:
            return []
        return self.events[i : j + 1]


class IncidentCue(str, Enum):
    """Observable heuristics that a moment may hide a judgment.

    These are the *open baseline* detectors. The tuned weighting of cues (and
    attribution-fed re-ranking of which moments actually paid off) is closed.
    """

    HESITATION = "hesitation"        # long pause / "let me think"
    CORRECTION = "correction"        # expert reversed/edited a prior action
    OVERRIDE = "override"            # expert went against a tool/system suggestion
    DEVIATION = "deviation"          # departed from the usual path
    EXCEPTION = "exception"          # an edge case / non-standard situation
    HIGH_STAKES = "high_stakes"      # money, escalation, external party
    RETRY = "retry"                  # repeated attempts / tool failures
    EXPLICIT_DECISION = "explicit_decision"


class CriticalIncident(BaseModel):
    """A flagged moment in a trace worth eliciting the expert about."""

    id: str = Field(default="")
    trace_id: str
    start_event: str
    end_event: str
    cues: List[IncidentCue] = Field(default_factory=list)
    score: float = Field(0.0, ge=0.0, le=1.0, description="Criticality score, 0..1")
    detector: str = Field("baseline", description="Which detector/ranker produced this")
    summary: str = Field("", description="One-line description of the moment")
    why_flagged: str = Field("", description="Why this moment looks judgment-bearing")

    def ensure_id(self) -> "CriticalIncident":
        if not self.id:
            basis = f"{self.trace_id}|{self.start_event}|{self.end_event}".encode("utf-8")
            self.id = "ci_" + hashlib.sha1(basis).hexdigest()[:12]
        return self
