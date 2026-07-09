"""ATTRIBUTION plane — the append-only outcome ledger.

This plane closes the loop: it records the actions agents took on Judgment
Units, records the real business outcomes that followed, and assigns credit
from outcomes back to JUs. That credit is the reward signal EVOLVE consumes.

The ledger is append-only JSONL (never overwritten; state is a deterministic
projection) — the pattern ProjectMem (MIT) proved for agent memory, applied
here to business attribution and audit. The same log doubles as the immutable
audit trail enterprises require before granting an agent autonomy.

Credit assignment uses a pluggable `AttributionEngine`. The open baseline is a
recency-weighted heuristic that makes no causal claim; the moat engine does
delayed/noisy long-horizon credit with incrementality correction.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, Union

from ..plugins import DEFAULT_ATTRIBUTION_ENGINE, AttributionEngine
from ..schema.attribution import ActionRecord, AttributionLink, Outcome
from ..schema.judgment_unit import JudgmentLibrary, OutcomeRef

_Record = Union[ActionRecord, Outcome, AttributionLink]


def _tag(rec: _Record) -> str:
    if isinstance(rec, ActionRecord):
        return "action"
    if isinstance(rec, Outcome):
        return "outcome"
    return "attribution"


class OutcomeLedger:
    """Append-only store of actions, outcomes and attribution links."""

    def __init__(self, path: Optional[str] = None, engine: AttributionEngine = DEFAULT_ATTRIBUTION_ENGINE):
        self.path = Path(path) if path else None
        self.engine = engine
        self.actions: List[ActionRecord] = []
        self.outcomes: List[Outcome] = []
        self.links: List[AttributionLink] = []
        if self.path and self.path.exists():
            self.load()

    # --- append side ---
    def record_action(self, action: ActionRecord) -> ActionRecord:
        action.ensure_id(len(self.actions))
        self.actions.append(action)
        self._append(action)
        return action

    def record_outcome(self, outcome: Outcome) -> List[AttributionLink]:
        """Record an outcome and immediately attribute credit to prior actions."""
        outcome.ensure_id()
        self.outcomes.append(outcome)
        self._append(outcome)
        new_links = self.engine.attribute(outcome, self.actions)
        for link in new_links:
            self.links.append(link)
            self._append(link)
        return new_links

    # --- projection side ---
    def credit_by_ju(self) -> dict:
        out: dict = {}
        for link in self.links:
            out[link.ju_id] = round(out.get(link.ju_id, 0.0) + link.credit, 4)
        return out

    def fold_into_library(self, library: JudgmentLibrary) -> JudgmentLibrary:
        """Write attributed credit back onto each JU as OutcomeRefs (for EVOLVE)."""
        by_ju: dict = {}
        for link in self.links:
            by_ju.setdefault(link.ju_id, []).append(link)
        for ju in library.units:
            links = by_ju.get(ju.id, [])
            ju.outcomes = [
                OutcomeRef(
                    outcome_id=link.outcome_id,
                    metric=self._metric_for(link.outcome_id),
                    credit=link.credit,
                    method=link.method.value,
                )
                for link in links
            ]
        return library

    def _metric_for(self, outcome_id: str) -> str:
        oc = next((o for o in self.outcomes if o.id == outcome_id), None)
        return oc.metric if oc else "unknown"

    # --- persistence ---
    def _append(self, rec: _Record) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"kind": _tag(rec), "data": rec.model_dump(mode="json")}, ensure_ascii=False) + "\n")

    def load(self) -> None:
        self.actions.clear()
        self.outcomes.clear()
        self.links.clear()
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                kind, data = row["kind"], row["data"]
                if kind == "action":
                    self.actions.append(ActionRecord(**data))
                elif kind == "outcome":
                    self.outcomes.append(Outcome(**data))
                elif kind == "attribution":
                    self.links.append(AttributionLink(**data))
