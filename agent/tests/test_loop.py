"""End-to-end smoke tests for the FDE Loop (fully offline, deterministic)."""
from __future__ import annotations

from openfde import run_loop
from openfde._examples import sales_qualification
from openfde.loop.observe import observe
from openfde.schema.judgment_unit import Autonomy


def _run():
    ex = sales_qualification()
    return run_loop(
        ex["trace"],
        ex["answers"],
        project=ex["project"],
        domain=ex["domain"],
        connectors=ex["connectors"],
        decisions=ex["decisions"],
        actions=ex["actions"],
        outcomes=ex["outcomes"],
    )


def test_observe_flags_the_override():
    ex = sales_qualification()
    incidents = observe(ex["trace"])
    assert incidents, "expected at least one critical incident"
    cues = {c.value for inc in incidents for c in inc.cues}
    # the expert overrode the auto-routing and it was a high-stakes decision
    assert "override" in cues
    assert "explicit_decision" in cues


def test_induce_produces_a_judgment_unit_with_the_why():
    result = _run()
    assert len(result.library.units) >= 1
    ju = result.library.units[0]
    assert ju.decision, "JU must carry a decision"
    assert ju.rationale, "JU must recover the *why*"
    assert ju.reversal_conditions, "JU must capture when the judgment reverses"
    assert ju.signals, "JU must capture the triggering signals"
    # every JU starts conservative until it earns trust
    assert ju.id.startswith("ju_")


def test_act_compiles_a_governed_config():
    result = _run()
    cfg = result.agent_config
    assert cfg is not None
    assert "forward-deployed" in cfg.system_prompt.lower()
    # the mock CRM write op must be approval-gated in the compiled tool policy
    write_ops = [t for t in cfg.tools if t.operation == "crm.update_stage"]
    assert write_ops and write_ops[0].requires_approval


def test_attribution_credits_the_winning_judgment():
    result = _run()
    assert result.ledger is not None
    credit = result.ledger.credit_by_ju()
    ju = result.library.units[0]
    assert credit.get(ju.id, 0.0) > 0, "a closed deal should credit the judgment that drove it"


def test_evolve_promotes_on_positive_outcome():
    result = _run()
    assert result.evolve_report is not None
    ju = result.library.units[0]
    # positive attributed outcome should raise confidence and earn a promotion
    update = next(u for u in result.evolve_report.updates if u.ju_id == ju.id)
    assert update.confidence_after >= update.confidence_before
    assert ju.autonomy in (Autonomy.APPROVE, Autonomy.AUTO)


def test_ledger_roundtrips_to_disk(tmp_path):
    ex = sales_qualification()
    path = tmp_path / "ledger.jsonl"
    run_loop(
        ex["trace"], ex["answers"], project=ex["project"], domain=ex["domain"],
        connectors=ex["connectors"], actions=ex["actions"], outcomes=ex["outcomes"],
        ledger_path=str(path),
    )
    assert path.exists()
    from openfde.planes.attribution import OutcomeLedger

    reloaded = OutcomeLedger(path=str(path))
    assert reloaded.outcomes and reloaded.actions and reloaded.links
