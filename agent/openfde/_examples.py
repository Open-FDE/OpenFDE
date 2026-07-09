"""Built-in worked example(s), importable so the CLI and tests share one source.

Everything here is synthetic and desensitized — no real customer data — per the
open-repo data rule: never put real sessions, deals or private-domain data into
community examples.
"""
from __future__ import annotations

from typing import Any, Dict

from .loop.elicit import ScriptedAnswerProvider
from .planes.deploy import MockCrmConnector
from .schema.attribution import ActionRecord, Outcome, Polarity
from .schema.trace import EventType, Trace, TraceEvent


def sales_qualification() -> Dict[str, Any]:
    """A senior AE qualifying an inbound B2B lead — the reference scenario.

    The expert overrides seat-count auto-routing because a small team inside a
    large company, plus a dated compelling event, signals land-and-expand. The
    tacit rule ("qualify on the company behind the team, not the team size") is
    exactly what plain observation misses and elicitation recovers.
    """
    trace = Trace(
        project="acme-sales",
        actor="expert:chen",
        source="manual",
        events=[
            TraceEvent(
                type=EventType.MESSAGE,
                actor="lead:4821",
                content="We're evaluating QA tooling for our quality team — about 40 people. "
                "We need something rolled out within 6 weeks for an audit.",
            ),
            TraceEvent(type=EventType.TOOL_CALL, actor="expert:chen", content="crm.get_lead lead:4821"),
            TraceEvent(
                type=EventType.TOOL_RESULT,
                actor="mockcrm",
                content="company=Acme Manufacturing; total_employees=600; industry=manufacturing; budget=unknown",
            ),
            TraceEvent(
                type=EventType.MESSAGE,
                actor="expert:chen",
                content="Hmm, 40-person QA team but 600 total — this is a department pilot, not company-wide. "
                "Let me think about whether to route this to SMB self-serve or Enterprise.",
            ),
            TraceEvent(
                type=EventType.MESSAGE,
                actor="expert:chen",
                content="The hard 6-week deadline is the real signal — that's a compelling event. "
                "And the reply was fast and specific.",
            ),
            TraceEvent(
                type=EventType.DECISION,
                actor="expert:chen",
                content="Qualify as an Enterprise land-and-expand opportunity and push for a 30-minute "
                "scoping call this week, overriding the seat-count auto-routing.",
            ),
            TraceEvent(
                type=EventType.MESSAGE,
                actor="expert:chen",
                content="Normally a 40-seat pilot auto-routes to SMB self-serve. I'm overriding that: "
                "compelling event plus a 600-person parent means real expansion. Ignore the auto-routing.",
            ),
            TraceEvent(type=EventType.EDIT, actor="expert:chen", content="stage -> 'Enterprise - Discovery'"),
        ],
    ).ensure_ids()

    answers = ScriptedAnswerProvider(
        {
            "trigger": "An inbound lead where the immediate team is small but the parent company is large, "
            "and there is a hard deadline.",
            "preconditions": "The inbound reply is fast and specific, and there is a named compelling event with a date.",
            "cues": "The mismatch between a 40-person team and a 600-person company; a hard 6-week deadline; "
            "a fast, specific first reply.",
            "assessment": "A small team inside a big company with a deadline is almost always a beachhead — "
            "land the pilot, then expand. The deadline means they will actually buy, not just browse.",
            "goals": "Get a scoping call booked this week before the deadline pressure fades, and set up land-and-expand.",
            "options": "Auto-route to SMB self-serve, or disqualify as too small. Both are wrong — self-serve "
            "wastes the expansion, and disqualifying throws away a live, funded deal.",
            "expectancy": "If it is real, they book the call within 48 hours; watch whether a VP or procurement joins.",
            "analogues": "Last year a 25-seat pilot at a 2,000-person firm became our largest manufacturing account — same pattern.",
            "reversal_conditions": "If the parent company were actually small, or if there were no deadline and the reply "
            "were vague, I would route it to SMB self-serve.",
            "standard": "Rule of thumb: qualify on the company behind the team, not the team size; a dated compelling "
            "event beats any lead score.",
            "stakes": "Mis-routing a land-and-expand deal to self-serve can cost a six-figure expansion.",
        }
    )

    crm = MockCrmConnector()

    # Synthetic outcome: the deal closed. In run_loop, a blank ju_id resolves to
    # the primary induced JU, so this attributes the win back to the judgment.
    actions = [
        ActionRecord(
            ju_id="",
            subject_ref="lead:4821",
            autonomy="suggest",
            intent="Qualify as Enterprise land-and-expand; book a scoping call.",
            approved_by="expert:chen",
            applied=True,
        )
    ]
    outcomes = [
        Outcome(
            subject_ref="lead:4821",
            metric="deal_closed",
            value=1.0,
            polarity=Polarity.POSITIVE,
            metadata={"acv_band": "six-figure", "note": "synthetic"},
        )
    ]

    return {
        "project": "acme-sales",
        "domain": "sales.qualification",
        "trace": trace,
        "answers": answers,
        "connectors": [crm.spec],
        "decisions": {},  # INDUCE will read the DECISION event from the trace
        "actions": actions,
        "outcomes": outcomes,
    }


EXAMPLES = {"sales-qualification": sales_qualification}
