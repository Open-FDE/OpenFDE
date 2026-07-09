"""EVOLVE — improve Judgment Units from real business outcomes.

Most optimizers answer "how to improve"; few have a high-value signal to improve
*against*. OpenFDE's answer:

    GEPA gives you the optimizer; ATTRIBUTION gives you the golden feedback.

The open baseline here does the honest, transparent thing: it reads each JU's
attributed outcome score and (a) nudges confidence, (b) proposes an autonomy
change (promote what pays off, demote what hurts), (c) flags negatively-credited
JUs for expert revision. No hidden learning.

`GEPAAdapter` is the reference seam to GEPA (MIT), whose public API we target
exactly: a `GEPAAdapter` protocol with `evaluate()` + `make_reflective_dataset()`,
and a top-level `gepa.optimize(seed_candidate, trainset, ...)` where a candidate
is a `dict[str, str]` of named text components. Here the components are JU
rationale/decision texts, the score is the attributed outcome, and the reflective
dataset is drawn from the outcomes each JU influenced.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from ..schema.judgment_unit import Autonomy, JudgmentLibrary, JudgmentUnit


class JudgmentUpdate(BaseModel):
    ju_id: str
    title: str
    outcome_score: float
    confidence_before: float
    confidence_after: float
    autonomy_before: str
    autonomy_after: str
    action: str = Field(..., description="promote | demote | reinforce | flag_for_revision | hold")
    note: str = ""


class EvolveReport(BaseModel):
    updates: List[JudgmentUpdate] = Field(default_factory=list)

    def summary(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for u in self.updates:
            out[u.action] = out.get(u.action, 0) + 1
        return out


def evolve(library: JudgmentLibrary, *, learning_rate: float = 0.1, apply: bool = True) -> EvolveReport:
    """Update JUs from their attributed outcomes. Baseline, deterministic."""
    report = EvolveReport()
    for ju in library.units:
        score = ju.outcome_score()
        conf_before = ju.confidence
        auto_before = ju.autonomy

        # Reinforce from evidence: positive attributed credit raises confidence,
        # negative lowers it. Squashed so a single large outcome can't dominate.
        conf_after = round(max(0.0, min(1.0, conf_before + learning_rate * _squash(score))), 3)

        auto_after = auto_before
        action = "hold"
        note = ""
        if score < 0:
            action = "flag_for_revision"
            note = "negative attributed outcome — expert should review"
            if auto_before is Autonomy.AUTO:
                auto_after = Autonomy.APPROVE
            elif auto_before is Autonomy.APPROVE:
                auto_after = Autonomy.SUGGEST
        elif score > 0:
            probe = JudgmentUnit(**{**ju.model_dump(), "confidence": conf_after})
            promoted = probe.promote()
            if promoted != auto_before:
                auto_after = promoted
                action = "promote"
                note = "positive track record — earned a higher autonomy tier"
            else:
                action = "reinforce"
                note = "positive outcome reinforces this judgment"

        if apply:
            ju.confidence = conf_after
            ju.autonomy = auto_after

        report.updates.append(
            JudgmentUpdate(
                ju_id=ju.id,
                title=ju.title,
                outcome_score=score,
                confidence_before=conf_before,
                confidence_after=conf_after,
                autonomy_before=auto_before.value,
                autonomy_after=auto_after.value,
                action=action,
                note=note,
            )
        )
    return report


def _squash(x: float) -> float:
    """Map an unbounded score into (-1, 1) so single big outcomes don't dominate."""
    if x == 0:
        return 0.0
    return x / (1.0 + abs(x))


# --------------------------------------------------------------------------- #
# Reference GEPA seam (optional; targets github.com/gepa-ai/gepa, MIT)
# --------------------------------------------------------------------------- #
class GEPAAdapter:  # pragma: no cover - exercised only when gepa is installed
    """Adapt a JudgmentLibrary to GEPA's optimizer.

    A GEPA *candidate* is a dict[str, str]. We expose each JU's rationale as a
    named text component (`f"{ju.id}.rationale"`), let GEPA reflectively rewrite
    them, and score candidates by the JUs' attributed outcome scores. This mirrors
    GEPA's documented `evaluate` / `make_reflective_dataset` protocol.
    """

    def __init__(self, library: JudgmentLibrary):
        self.library = library

    def seed_candidate(self) -> Dict[str, str]:
        return {f"{ju.id}.rationale": ju.rationale for ju in self.library.units}

    def evaluate(self, batch, candidate: Dict[str, str], capture_traces: bool = False):
        # Score = current attributed outcome per JU referenced in the batch.
        scores = []
        outputs = []
        for item in batch:
            ju = self.library.get(item.get("ju_id"))
            scores.append(ju.outcome_score() if ju else 0.0)
            outputs.append(candidate.get(f"{item.get('ju_id')}.rationale", ""))
        try:
            from gepa.core.adapter import EvaluationBatch  # type: ignore
        except ImportError:
            return {"outputs": outputs, "scores": scores}
        return EvaluationBatch(outputs=outputs, scores=scores, trajectories=None)

    def make_reflective_dataset(self, candidate, eval_batch, components_to_update):
        # Feed each component the outcomes it influenced as "actionable side info".
        dataset: Dict[str, List[dict]] = {}
        for comp in components_to_update:
            ju_id = comp.split(".")[0]
            ju = self.library.get(ju_id)
            if not ju:
                continue
            dataset[comp] = [
                {
                    "Inputs": ju.trigger,
                    "Generated": candidate.get(comp, ju.rationale),
                    "Feedback": f"attributed outcome score = {ju.outcome_score()}; "
                    f"reverse if: {'; '.join(ju.reversal_conditions) or 'n/a'}",
                }
            ]
        return dataset


def optimize_with_gepa(library: JudgmentLibrary, reflection_lm: Optional[str] = None, max_metric_calls: int = 30):  # pragma: no cover
    """Optionally run real GEPA over the library. Requires `pip install openfde[evolve]`."""
    try:
        import gepa  # type: ignore
    except ImportError as exc:
        raise ImportError("GEPA is optional. Install with: pip install 'openfde[evolve]'") from exc
    adapter = GEPAAdapter(library)
    trainset = [{"ju_id": ju.id} for ju in library.units]
    return gepa.optimize(
        seed_candidate=adapter.seed_candidate(),
        trainset=trainset,
        adapter=adapter,
        reflection_lm=reflection_lm,
        max_metric_calls=max_metric_calls,
    )
