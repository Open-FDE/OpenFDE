"""OpenFDE — the Apprentice Loop.

An in-situ apprenticeship layer that sits *above* agent runtimes: it observes an
expert's real work, elicits the tacit *why* behind their judgments, induces
those into reusable **Judgment Units**, acts on them with graduated autonomy,
and evolves on real business outcomes.

    Observation gives you the *what*; elicitation recovers the *why*.

Quick start:

    from openfde import run_loop, Trace
    from openfde.loop.elicit import ScriptedAnswerProvider

See examples/sales-qualification and `openfde loop --example sales-qualification`.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .loop import LoopResult, compile_judgments, elicit, evolve, induce, observe, run_loop
from .planes import ConnectorRegistry, OutcomeLedger
from .schema import (
    Autonomy,
    ConnectorSpec,
    CriticalIncident,
    ElicitationSession,
    JudgmentLibrary,
    JudgmentUnit,
    Outcome,
    Trace,
    TraceEvent,
)

__all__ = [
    "__version__",
    # loop
    "run_loop",
    "observe",
    "elicit",
    "induce",
    "compile_judgments",
    "evolve",
    "LoopResult",
    # planes
    "OutcomeLedger",
    "ConnectorRegistry",
    # core schema
    "JudgmentUnit",
    "JudgmentLibrary",
    "Autonomy",
    "Trace",
    "TraceEvent",
    "CriticalIncident",
    "ElicitationSession",
    "Outcome",
    "ConnectorSpec",
]
