"""Judgment Unit — the central primitive of OpenFDE.

A Judgment Unit (JU) is *decision-level procedural memory*: it captures not
just what an expert did, but the tacit **why** behind a judgment and, over
time, how that judgment connected to real business outcomes.

This is deliberately NOT another generic "memory" record:

    Mem0 / LangMem / Graphiti  -> manage memory (facts, preferences, context)
    AWM (Agent Workflow Memory) -> induces reusable *workflows*
    OpenFDE Judgment Unit       -> induces *judgments* — a decision, its
                                   triggering signals, the expert's rationale,
                                   the conditions under which it reverses, the
                                   autonomy at which an agent may act on it,
                                   and its attributed business outcome.

    Observation gives you the *what*; elicitation recovers the *why*.

The JU schema is one of the standards OpenFDE wants to make open. See SPEC.md.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Autonomy(str, Enum):
    """Graduated autonomy (Parasuraman levels-of-automation, applied to agents).

    A JU is not simply "on" — it carries the level at which an agent is trusted
    to act on it in production. Trust is *earned* as attribution accrues.
    """

    SUGGEST = "suggest"   # agent surfaces the judgment; human decides
    APPROVE = "approve"   # agent proposes an action; human approves before it runs
    AUTO = "auto"         # agent acts, human audits after the fact


class JudgmentStatus(str, Enum):
    DRAFT = "draft"           # freshly induced, not yet reviewed by the expert
    ACTIVE = "active"         # reviewed, in use
    SHADOW = "shadow"         # running but its actions are logged, not applied
    DEPRECATED = "deprecated"  # superseded or retired


class Signal(BaseModel):
    """One thing the expert attended to when making the judgment.

    The set of signals is the observable "situation" that triggers a JU. What
    makes a signal valuable is not its value but the expert's account of *why*
    it mattered — recovered during ELICIT.
    """

    name: str = Field(..., description="Human label, e.g. 'buyer replied within 1h'")
    source: Optional[str] = Field(
        None, description="System/field the signal is read from, e.g. 'crm.lead.last_reply_at'"
    )
    observation: Optional[str] = Field(
        None, description="The pattern/value the expert noticed, e.g. 'fast, specific reply'"
    )
    why_it_matters: Optional[str] = Field(
        None, description="Elicited rationale for the signal's diagnostic value"
    )
    importance: float = Field(0.5, ge=0.0, le=1.0, description="Relative weight, 0..1")


class Alternative(BaseModel):
    """An option the expert considered and (usually) rejected — and why."""

    option: str
    considered_because: Optional[str] = None
    rejected_because: Optional[str] = None


class ActionSpec(BaseModel):
    """What acting on this judgment concretely looks like.

    Kept runtime-agnostic on purpose. ACT compiles this into a specific agent
    config (tool policy + approval policy). See openfde/loop/act.py.
    """

    intent: str = Field(..., description="What the agent should do, in plain language")
    tool: Optional[str] = Field(None, description="Tool/connector operation, e.g. 'crm.update_stage'")
    arguments: dict[str, Any] = Field(default_factory=dict)
    template: Optional[str] = Field(None, description="Draft message/template if the action is a suggestion")
    guardrails: List[str] = Field(default_factory=list, description="Hard constraints the agent must not cross")


class Provenance(BaseModel):
    """Where this JU came from — every JU is traceable back to real work."""

    trace_id: Optional[str] = None
    incident_id: Optional[str] = None
    elicitation_id: Optional[str] = None
    expert_id: Optional[str] = None
    reviewer_id: Optional[str] = None


class StopSnapshot(BaseModel):
    """8-dimension readiness at the moment ELICIT stopped probing.

    The *interface* is open; the tuned scoring of these dimensions (and the
    weights that decide when a judgment is 'ready') is part of the commercial
    moat — see openfde/plugins. Baseline scoring ships in the open repo.
    """

    cue_coverage: float = 0.0
    rationale_depth: float = 0.0
    alternative_coverage: float = 0.0
    reversal_coverage: float = 0.0
    consistency: float = 0.0
    novelty_exhaustion: float = 0.0   # 1.0 == last probes yielded ~no new info
    expert_confidence: float = 0.0
    corroboration: float = 0.0

    def readiness(self) -> float:
        vals = [
            self.cue_coverage,
            self.rationale_depth,
            self.alternative_coverage,
            self.reversal_coverage,
            self.consistency,
            self.novelty_exhaustion,
            self.expert_confidence,
            self.corroboration,
        ]
        return round(sum(vals) / len(vals), 3)


class OutcomeRef(BaseModel):
    """A link back to the ATTRIBUTION plane: this JU influenced a real result."""

    outcome_id: str
    metric: str
    credit: float = Field(0.0, description="Attributed credit/weight for this JU on the outcome")
    method: str = Field("heuristic", description="heuristic | causal | incrementality")


class JudgmentUnit(BaseModel):
    """A single, versioned, decision-level unit of expert judgment."""

    id: str = Field(default="", description="Stable id; auto-derived if empty")
    version: int = 1
    status: JudgmentStatus = JudgmentStatus.DRAFT

    title: str = Field(..., description="Short human label for the judgment")
    domain: str = Field("general", description="Dotted domain, e.g. 'sales.qualification'")

    # --- the situation that triggers this judgment (from OBSERVE) ---
    trigger: str = Field(..., description="When does this judgment apply? Plain-language situation.")
    signals: List[Signal] = Field(default_factory=list)
    preconditions: List[str] = Field(default_factory=list)

    # --- the judgment itself (from OBSERVE + ELICIT) ---
    decision: str = Field(..., description="What the expert decides/does")
    rationale: str = Field("", description="The elicited *why* — the tacit reasoning made explicit")
    alternatives: List[Alternative] = Field(default_factory=list)
    reversal_conditions: List[str] = Field(
        default_factory=list, description="What would make the expert decide the opposite"
    )
    cues_to_watch: List[str] = Field(
        default_factory=list, description="Leading indicators to monitor after acting"
    )

    # --- how an agent may act on it (from INDUCE + graduated trust) ---
    autonomy: Autonomy = Autonomy.SUGGEST
    action: Optional[ActionSpec] = None

    # --- confidence & evidence ---
    confidence: float = Field(0.3, ge=0.0, le=1.0)
    evidence_count: int = Field(1, description="How many observed episodes support this JU")
    stop_snapshot: Optional[StopSnapshot] = None

    # --- links ---
    provenance: Provenance = Field(default_factory=Provenance)
    outcomes: List[OutcomeRef] = Field(default_factory=list)
    supersedes: Optional[str] = Field(None, description="id of a JU this one replaces")

    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    def ensure_id(self) -> "JudgmentUnit":
        """Derive a stable content-addressed id when one was not supplied."""
        if not self.id:
            basis = f"{self.domain}|{self.title}|{self.decision}".encode("utf-8")
            self.id = "ju_" + hashlib.sha1(basis).hexdigest()[:12]
        return self

    def outcome_score(self) -> float:
        """Sum of attributed credit across linked outcomes.

        This is the signal EVOLVE optimizes against — the JU's real business
        track record, not a demo score.
        """
        return round(sum(o.credit for o in self.outcomes), 4)

    def promote(self) -> Autonomy:
        """Suggest the next autonomy tier given confidence + attributed outcomes.

        Deliberately conservative: an agent earns 'auto' only with both high
        confidence and positive real-world track record. The tuned promotion
        policy is a moat hook (see plugins); this is the safe open baseline.
        """
        score = self.outcome_score()
        if self.autonomy is Autonomy.SUGGEST and self.confidence >= 0.6 and score > 0:
            return Autonomy.APPROVE
        if self.autonomy is Autonomy.APPROVE and self.confidence >= 0.8 and score >= 1.0:
            return Autonomy.AUTO
        return self.autonomy


class JudgmentLibrary(BaseModel):
    """A versioned collection of Judgment Units for one project/domain.

    This is the closest OpenFDE artifact to Palantir's 'ontology', but scoped
    to *judgments* rather than objects: the reusable, auditable asset a
    forward-deployed engagement leaves behind.
    """

    project: str = "untitled"
    domain: str = "general"
    units: List[JudgmentUnit] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)

    def add(self, ju: JudgmentUnit) -> JudgmentUnit:
        ju.ensure_id()
        # replace same-id (new version) or append
        for i, existing in enumerate(self.units):
            if existing.id == ju.id:
                ju.version = existing.version + 1
                ju.updated_at = _utcnow()
                self.units[i] = ju
                return ju
        self.units.append(ju)
        return ju

    def get(self, ju_id: str) -> Optional[JudgmentUnit]:
        return next((u for u in self.units if u.id == ju_id), None)

    def active(self) -> List[JudgmentUnit]:
        return [u for u in self.units if u.status in (JudgmentStatus.ACTIVE, JudgmentStatus.SHADOW)]
