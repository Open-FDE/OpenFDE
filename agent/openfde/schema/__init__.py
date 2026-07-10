"""OpenFDE schemas — the open standards at the heart of the FDE Loop.

The two flagship standards OpenFDE wants to make open are the **Judgment Unit
Schema** and the **Elicitation Protocol**. See SPEC.md.
"""
from __future__ import annotations

from .attribution import (
    ActionRecord,
    AttributionLink,
    AttributionMethod,
    Outcome,
    Polarity,
)
from .connector import ConnectorSpec, Operation, OpKind
from .elicitation import (
    ElicitationMove,
    ElicitationSession,
    Phase,
    Probe,
    StopReason,
)
from .judgment_unit import (
    ActionSpec,
    Alternative,
    Autonomy,
    JudgmentLibrary,
    JudgmentStatus,
    JudgmentUnit,
    OutcomeRef,
    Provenance,
    Signal,
    StopSnapshot,
)
from .trace import (
    CriticalIncident,
    EventType,
    IncidentCue,
    Trace,
    TraceEvent,
)

__all__ = [
    # judgment unit
    "JudgmentUnit",
    "JudgmentLibrary",
    "JudgmentStatus",
    "Autonomy",
    "Signal",
    "Alternative",
    "ActionSpec",
    "Provenance",
    "StopSnapshot",
    "OutcomeRef",
    # trace / observe
    "Trace",
    "TraceEvent",
    "EventType",
    "CriticalIncident",
    "IncidentCue",
    # elicit
    "ElicitationSession",
    "ElicitationMove",
    "Phase",
    "Probe",
    "StopReason",
    # attribution
    "Outcome",
    "Polarity",
    "ActionRecord",
    "AttributionLink",
    "AttributionMethod",
    # connector
    "ConnectorSpec",
    "Operation",
    "OpKind",
]
