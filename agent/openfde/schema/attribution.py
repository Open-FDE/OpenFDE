"""ATTRIBUTION plane schema — connecting judgments to real business results.

The ATTRIBUTION plane is what turns a copilot into an FDE that gets
better at the *business*, not just at looking helpful. It links every expert
judgment, agent action and Judgment Unit to real outcomes — a deal closing,
a customer churning, an NPS moving — and becomes the reward signal EVOLVE
optimizes against.

    GEPA gives you the optimizer; ATTRIBUTION gives you the golden feedback.

It is deliberately NOT ordinary BI or a plain A/B test. The question is causal
and per-judgment: *which* judgment / action / JU actually moved the result?
The open repo ships an append-only ledger + a heuristic attributor + a
pluggable metric protocol. The tuned attribution engine (delayed, noisy,
long-horizon credit assignment; incrementality correction; cross-client
outcome models) is the deepest part of the moat — see openfde/plugins.

Ledger design follows the event-sourced, append-only pattern proven by
ProjectMem (MIT): nothing is overwritten; state is a deterministic projection.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Polarity(str, Enum):
    POSITIVE = "positive"    # the outcome is good (deal closed, retained)
    NEGATIVE = "negative"    # the outcome is bad (churned, complaint)
    NEUTRAL = "neutral"


class Outcome(BaseModel):
    """A real business result observed after some judgments/actions."""

    id: str = Field(default="")
    subject_ref: str = Field(..., description="What the outcome is about, e.g. 'lead:4821'")
    metric: str = Field(..., description="Metric name, e.g. 'deal_closed' | 'churn' | 'nps'")
    value: float = Field(1.0, description="Metric value (1/0 for events, or a number)")
    polarity: Polarity = Polarity.POSITIVE
    occurred_at: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def ensure_id(self) -> "Outcome":
        if not self.id:
            basis = f"{self.subject_ref}|{self.metric}|{self.occurred_at.isoformat()}".encode("utf-8")
            self.id = "oc_" + hashlib.sha1(basis).hexdigest()[:12]
        return self


class ActionRecord(BaseModel):
    """An action an agent took on a JU, with its autonomy and approval state.

    This is also the audit record enterprises require before granting autonomy:
    who/what acted, under which JU, at which autonomy, and who approved it.
    """

    id: str = Field(default="")
    ju_id: str
    subject_ref: str
    autonomy: str = "suggest"
    intent: str = ""
    approved_by: Optional[str] = None
    applied: bool = False
    occurred_at: datetime = Field(default_factory=_utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def ensure_id(self, seq: int = 0) -> "ActionRecord":
        if not self.id:
            self.id = f"ac_{seq:04d}_" + hashlib.sha1(
                f"{self.ju_id}|{self.subject_ref}".encode("utf-8")
            ).hexdigest()[:8]
        return self


class AttributionMethod(str, Enum):
    HEURISTIC = "heuristic"              # simple last-touch / time-window credit (open baseline)
    CAUSAL = "causal"                    # DoWhy-style effect estimation (adapter)
    INCREMENTALITY = "incrementality"    # holdout / uplift (moat)


class AttributionLink(BaseModel):
    """Credit assigned from an outcome back to a JU (and the action that used it)."""

    id: str = Field(default="")
    outcome_id: str
    ju_id: str
    action_id: Optional[str] = None
    credit: float = Field(0.0, description="Signed credit; positive helped, negative hurt")
    method: AttributionMethod = AttributionMethod.HEURISTIC
    rationale: str = ""
    created_at: datetime = Field(default_factory=_utcnow)

    def ensure_id(self) -> "AttributionLink":
        if not self.id:
            basis = f"{self.outcome_id}|{self.ju_id}|{self.action_id}".encode("utf-8")
            self.id = "at_" + hashlib.sha1(basis).hexdigest()[:12]
        return self


# The three record kinds that live in the append-only ledger.
LedgerRecord = Any  # Outcome | ActionRecord | AttributionLink (kept loose for JSONL round-trips)
