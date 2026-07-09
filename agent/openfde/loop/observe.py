"""OBSERVE — ingest expert traces and flag critical incidents.

OpenFDE does not re-implement observability. It ingests what Langfuse /
OpenTelemetry / rrweb already capture (via `Trace`) and adds the one thing they
don't: deciding *which moments hid a judgment worth eliciting*.

The detector here is the open baseline: transparent heuristics over the trace.
The attribution-fed, cross-client **moment ranker** that learns which kinds of
moments actually paid off is the moat — it plugs in via `MomentRanker`.
"""
from __future__ import annotations

import re
from typing import List

from ..plugins import DEFAULT_MOMENT_RANKER, MomentRanker
from ..schema.trace import CriticalIncident, EventType, IncidentCue, Trace

# Lexical cues for the baseline detector. Deliberately simple and inspectable.
_HESITATION = re.compile(r"\b(hmm|let me think|not sure|tricky|on the other hand|actually,|wait)\b", re.I)
_CORRECTION = re.compile(r"\b(actually|no wait|let me redo|scratch that|correction|revert|undo)\b", re.I)
_OVERRIDE = re.compile(r"\b(ignore|override|against|despite|not following|overrule|don't agree)\b", re.I)
_STAKES = re.compile(r"\b(contract|discount|refund|escalat|legal|budget|churn|renew|deadline|price|risk)\b", re.I)
_EXCEPTION = re.compile(r"\b(exception|edge case|unusual|special case|one-off|non-standard|first time)\b", re.I)


def detect_incidents(trace: Trace) -> List[CriticalIncident]:
    """Scan a trace and emit candidate critical incidents (unranked).

    Each explicit DECISION event, and each event whose content trips a cue, is
    treated as a candidate. Nearby cues within a small window are merged so one
    decision doesn't fan out into many fragments.
    """
    trace.ensure_ids()
    incidents: List[CriticalIncident] = []

    for idx, ev in enumerate(trace.events):
        cues: List[IncidentCue] = []
        text = ev.content or ""

        if ev.type is EventType.DECISION:
            cues.append(IncidentCue.EXPLICIT_DECISION)
        if ev.type is EventType.EDIT and _CORRECTION.search(text):
            cues.append(IncidentCue.CORRECTION)
        if _HESITATION.search(text):
            cues.append(IncidentCue.HESITATION)
        if _CORRECTION.search(text):
            cues.append(IncidentCue.CORRECTION)
        if _OVERRIDE.search(text):
            cues.append(IncidentCue.OVERRIDE)
        if _STAKES.search(text):
            cues.append(IncidentCue.HIGH_STAKES)
        if _EXCEPTION.search(text):
            cues.append(IncidentCue.EXCEPTION)

        # structural cue: repeated tool_call/tool_result churn = RETRY
        if ev.type is EventType.TOOL_CALL and idx >= 2:
            window = trace.events[max(0, idx - 2): idx]
            if sum(1 for w in window if w.type is EventType.TOOL_CALL) >= 2:
                cues.append(IncidentCue.RETRY)

        if not cues:
            continue

        # span: include one event of context before and after when available
        start = trace.events[max(0, idx - 1)].id
        end = trace.events[min(len(trace.events) - 1, idx + 1)].id
        summary = (text[:120] + "…") if len(text) > 120 else text
        inc = CriticalIncident(
            trace_id=trace.id,
            start_event=start,
            end_event=end,
            cues=sorted(set(cues), key=lambda c: c.value),
            summary=summary or f"{ev.type.value} at {ev.id}",
            why_flagged="; ".join(sorted({c.value for c in cues})),
        ).ensure_id()
        incidents.append(inc)

    return _merge_adjacent(incidents, trace)


def _merge_adjacent(incidents: List[CriticalIncident], trace: Trace) -> List[CriticalIncident]:
    """Merge incidents whose spans overlap or touch, unioning their cues."""
    if not incidents:
        return []
    order = {e.id: i for i, e in enumerate(trace.events)}
    incidents.sort(key=lambda inc: order.get(inc.start_event, 0))
    merged: List[CriticalIncident] = [incidents[0]]
    for inc in incidents[1:]:
        last = merged[-1]
        if order.get(inc.start_event, 0) <= order.get(last.end_event, 0) + 1:
            last.cues = sorted(set(last.cues) | set(inc.cues), key=lambda c: c.value)
            if order.get(inc.end_event, 0) > order.get(last.end_event, 0):
                last.end_event = inc.end_event
            last.why_flagged = "; ".join(sorted({c.value for c in last.cues}))
            last.ensure_id()
        else:
            merged.append(inc)
    return merged


def observe(trace: Trace, ranker: MomentRanker = DEFAULT_MOMENT_RANKER) -> List[CriticalIncident]:
    """Full OBSERVE step: detect candidates, then rank them by criticality."""
    incidents = detect_incidents(trace)
    return ranker.rank(trace, incidents)
