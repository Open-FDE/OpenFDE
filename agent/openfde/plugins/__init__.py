"""Plugin seams — where the open baseline ends and the commercial moat plugs in.

OpenFDE's open/closed boundary is not a slogan; it is expressed in code as four
plugin protocols. The open repo ships a working *baseline* for each so the loop
runs end-to-end out of the box. The tuned implementations — the parts that get
better with every client engagement — are meant to plug in behind the same
interfaces and are the commercial moat:

    protocol            open baseline (this repo)     closed moat (plugs in here)
    ----------------------------------------------------------------------------
    MomentRanker        cue-count heuristic           attribution-fed cross-client
                                                       moment value ranking
    StopCriterion       marginal-info + coverage       tuned 8-dimension real-time
                                                       stop policy
    MoveLibrary         CDM sweep templates            tuned Move library (wording,
                                                       ordering, adaptivity)
    AttributionEngine   time-window heuristic          delayed/noisy long-horizon
                                                       credit + incrementality

Everything here is dependency-free and deterministic so the reference loop is
reproducible.
"""
from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from ..schema.attribution import ActionRecord, AttributionLink, AttributionMethod, Outcome
from ..schema.elicitation import ElicitationMove, ElicitationSession, Phase, Probe
from ..schema.judgment_unit import StopSnapshot
from ..schema.trace import CriticalIncident, Trace


# --------------------------------------------------------------------------- #
# Protocols
# --------------------------------------------------------------------------- #
@runtime_checkable
class MomentRanker(Protocol):
    """Rank/score critical-incident candidates by how much judgment they hide."""

    def rank(self, trace: Trace, incidents: List[CriticalIncident]) -> List[CriticalIncident]:
        ...


@runtime_checkable
class StopCriterion(Protocol):
    """Decide whether an elicitation session has recovered enough judgment."""

    def score(self, session: ElicitationSession) -> StopSnapshot:
        ...

    def should_stop(self, session: ElicitationSession) -> bool:
        ...


@runtime_checkable
class MoveLibrary(Protocol):
    """Choose the next elicitation move given the session so far."""

    def next_move(self, session: ElicitationSession, incident: CriticalIncident) -> Optional[ElicitationMove]:
        ...


@runtime_checkable
class AttributionEngine(Protocol):
    """Assign credit from an outcome back to the JUs/actions that influenced it."""

    def attribute(
        self, outcome: Outcome, actions: List[ActionRecord]
    ) -> List[AttributionLink]:
        ...


# --------------------------------------------------------------------------- #
# Open baselines
# --------------------------------------------------------------------------- #
# Cue weights for the baseline moment ranker. The *tuned, attribution-fed*
# weighting is the moat; these are transparent, hand-set priors.
_CUE_WEIGHT = {
    "override": 1.0,
    "correction": 0.9,
    "high_stakes": 0.85,
    "exception": 0.7,
    "deviation": 0.65,
    "hesitation": 0.6,
    "explicit_decision": 0.55,
    "retry": 0.5,
}


class BaselineMomentRanker:
    """Score = saturating sum of weighted cues. Transparent, no learning."""

    def rank(self, trace: Trace, incidents: List[CriticalIncident]) -> List[CriticalIncident]:
        for inc in incidents:
            raw = sum(_CUE_WEIGHT.get(c.value, 0.4) for c in inc.cues)
            inc.score = round(min(1.0, raw / 2.0), 3)
            inc.detector = "baseline"
        return sorted(incidents, key=lambda i: i.score, reverse=True)


# The CDM deepening sweep the baseline library walks through, in order. The
# tuned Move library reorders/rewords these adaptively per expert and domain.
_DEEPEN_SEQUENCE: List[tuple] = [
    (Probe.CUES, "signals", "At that exact moment, what did you notice? Which specific signals were you reading?"),
    (Probe.ASSESSMENT, "rationale", "How did you size up the situation — what did those signals tell you?"),
    (Probe.GOALS, "rationale", "What were you trying to achieve right then?"),
    (Probe.OPTIONS, "alternatives", "What other options did you consider, and why did you set them aside?"),
    (Probe.EXPECTANCY, "cues_to_watch", "Having decided, what did you expect to happen next? What would you watch for?"),
    (Probe.ANALOGUES, "rationale", "Did this remind you of a previous case? What did that teach you?"),
    (Probe.REVERSAL, "reversal_conditions", "What would have made you decide the opposite?"),
    (Probe.STANDARD, "rationale", "Is there a rule of thumb here that a novice would likely miss?"),
    (Probe.STAKES, "rationale", "What was at risk if you'd gotten this wrong?"),
]


class BaselineMoveLibrary:
    """Walks the four CDM sweeps, issuing one probe per unanswered slot.

    This is a genuine, useful baseline — it will conduct a coherent CDM-style
    interview — but it is deliberately non-adaptive. The moat library adapts
    wording/order to the expert and skips probes already satisfied.
    """

    def next_move(self, session: ElicitationSession, incident: CriticalIncident) -> Optional[ElicitationMove]:
        covered = session.probes_covered()

        # Sweep 1: bound the incident. Uses MENTAL_MODEL, not CUES, so it does
        # not pre-cover the dedicated cues probe in the DEEPEN sweep.
        if not any(m.phase is Phase.INCIDENT for m in session.moves):
            return ElicitationMove(
                phase=Phase.INCIDENT,
                probe=Probe.MENTAL_MODEL,
                question=(
                    f"Walk me through this moment: {incident.summary or 'the flagged decision'}. "
                    "What was going on, and where exactly did you have to make a call?"
                ),
                extracts_to="trigger",
            )
        # Sweep 2: verify the timeline once.
        if not any(m.phase is Phase.TIMELINE for m in session.moves):
            return ElicitationMove(
                phase=Phase.TIMELINE,
                probe=Probe.KNOWLEDGE,
                question="In order, what happened just before and just after your decision?",
                extracts_to="preconditions",
            )
        # Sweep 3: cognitive probes (the core).
        for probe, field, question in _DEEPEN_SEQUENCE:
            if probe not in covered:
                return ElicitationMove(
                    phase=Phase.DEEPEN, probe=probe, question=question, extracts_to=field
                )
        # Sweep 4: one what-if to sharpen the decision boundary.
        if not any(m.phase is Phase.WHATIF for m in session.moves):
            return ElicitationMove(
                phase=Phase.WHATIF,
                probe=Probe.REVERSAL,
                question="If one thing about the situation had been different, what would have flipped your decision?",
                extracts_to="reversal_conditions",
            )
        return None


class BaselineStopCriterion:
    """8-dimension readiness from transcript coverage + marginal info gain.

    Fully transparent: each dimension is a simple function of which probes were
    answered and how much new information the last moves carried. The moat
    version scores these in real time from the *content* of answers.
    """

    def __init__(self, max_moves: int = 12, saturation: float = 0.15, target_readiness: float = 0.7):
        self.max_moves = max_moves
        self.saturation = saturation
        self.target_readiness = target_readiness

    def score(self, session: ElicitationSession) -> StopSnapshot:
        answered = session.answered_moves()
        covered = {m.probe for m in answered}

        def cov(*probes: Probe) -> float:
            hit = sum(1 for p in probes if p in covered)
            return round(hit / len(probes), 3)

        recent = answered[-2:]
        novelty = 1.0 - (sum(m.info_gain for m in recent) / len(recent) if recent else 1.0)

        return StopSnapshot(
            cue_coverage=cov(Probe.CUES, Probe.KNOWLEDGE),
            rationale_depth=cov(Probe.ASSESSMENT, Probe.GOALS, Probe.ANALOGUES, Probe.STANDARD),
            alternative_coverage=cov(Probe.OPTIONS),
            reversal_coverage=cov(Probe.REVERSAL),
            consistency=1.0 if answered else 0.0,  # baseline assumes internal consistency
            novelty_exhaustion=round(max(0.0, min(1.0, novelty)), 3),
            expert_confidence=cov(Probe.STAKES, Probe.EXPECTANCY),
            corroboration=round(min(1.0, len(answered) / 6.0), 3),
        )

    def should_stop(self, session: ElicitationSession) -> bool:
        if len(session.moves) >= self.max_moves:
            return True
        snap = self.score(session)
        answered = session.answered_moves()
        if len(answered) >= 4 and snap.readiness() >= self.target_readiness:
            return True
        # Saturation: the last two answered moves carried almost no new info.
        recent = answered[-2:]
        if len(recent) == 2 and all(m.info_gain <= self.saturation for m in recent):
            return True
        return False


class BaselineAttributionEngine:
    """Time-window, evenly-split credit — an honest placeholder, clearly labeled.

    It splits an outcome's signed value across the actions taken on that subject
    before the outcome, weighted by recency. It makes NO causal claim. The moat
    engine does delayed/noisy long-horizon credit assignment with incrementality
    correction (holdouts), which this repo intentionally does not.
    """

    def attribute(self, outcome: Outcome, actions: List[ActionRecord]) -> List[AttributionLink]:
        relevant = [
            a for a in actions
            if a.subject_ref == outcome.subject_ref and a.occurred_at <= outcome.occurred_at
        ]
        if not relevant:
            return []
        sign = 1.0 if outcome.polarity.value == "positive" else -1.0
        magnitude = sign * abs(outcome.value)
        # recency weights (most recent action gets the largest share)
        n = len(relevant)
        weights = [i + 1 for i in range(n)]
        total = sum(weights)
        links: List[AttributionLink] = []
        for w, action in zip(weights, relevant):
            credit = round(magnitude * (w / total), 4)
            links.append(
                AttributionLink(
                    outcome_id=outcome.id,
                    ju_id=action.ju_id,
                    action_id=action.id,
                    credit=credit,
                    method=AttributionMethod.HEURISTIC,
                    rationale=f"baseline recency-weighted split across {n} action(s) on {outcome.subject_ref}",
                ).ensure_id()
            )
        return links


# Default wiring used across the loop when no moat plugin is supplied.
DEFAULT_MOMENT_RANKER: MomentRanker = BaselineMomentRanker()
DEFAULT_MOVE_LIBRARY: MoveLibrary = BaselineMoveLibrary()
DEFAULT_STOP_CRITERION: StopCriterion = BaselineStopCriterion()
DEFAULT_ATTRIBUTION_ENGINE: AttributionEngine = BaselineAttributionEngine()

__all__ = [
    "MomentRanker",
    "StopCriterion",
    "MoveLibrary",
    "AttributionEngine",
    "BaselineMomentRanker",
    "BaselineMoveLibrary",
    "BaselineStopCriterion",
    "BaselineAttributionEngine",
    "DEFAULT_MOMENT_RANKER",
    "DEFAULT_MOVE_LIBRARY",
    "DEFAULT_STOP_CRITERION",
    "DEFAULT_ATTRIBUTION_ENGINE",
]
