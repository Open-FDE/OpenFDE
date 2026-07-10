"""openfde — the FDE Loop, on the command line.

    openfde loop --example sales-qualification   # run OBSERVE→...→EVOLVE end to end
    openfde observe trace.jsonl                   # detect critical incidents in a trace
    openfde init my-project                       # scaffold a blueprint
    openfde schema judgment-unit                  # print the Judgment Unit JSON Schema
    openfde version
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from ._examples import EXAMPLES
from .llm import LLMClient
from .loop import run_loop
from .loop.observe import observe
from .schema.judgment_unit import JudgmentUnit
from .schema.trace import EventType, Trace, TraceEvent

app = typer.Typer(add_completion=False, help="OpenFDE — the FDE Loop for enterprise agents.")
console = Console()


@app.command()
def version() -> None:
    """Print the OpenFDE version."""
    console.print(f"openfde [bold cyan]{__version__}[/] — Observation gives you the what; elicitation recovers the why.")


@app.command()
def loop(
    example: str = typer.Option("sales-qualification", "--example", "-e", help="Built-in example to run."),
    use_llm: bool = typer.Option(False, "--llm", help="Use a configured LLM for ELICIT/INDUCE (else deterministic)."),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Directory to write the judgment library + agent config."),
    ledger: Optional[Path] = typer.Option(None, "--ledger", help="Path for the append-only attribution ledger (JSONL)."),
) -> None:
    """Run one full pass of the FDE Loop on a built-in example."""
    if example not in EXAMPLES:
        console.print(f"[red]Unknown example '{example}'.[/] Available: {', '.join(EXAMPLES)}")
        raise typer.Exit(1)

    ex = EXAMPLES[example]()
    llm = LLMClient()
    if use_llm and not llm.enabled:
        console.print("[yellow]--llm requested but no LLM configured (set OPENFDE_LLM_* env). Running deterministic.[/]")

    result = run_loop(
        ex["trace"],
        ex["answers"],
        project=ex["project"],
        domain=ex["domain"],
        connectors=ex["connectors"],
        decisions=ex["decisions"],
        actions=ex.get("actions"),
        outcomes=ex.get("outcomes"),
        ledger_path=str(ledger) if ledger else None,
        llm=llm if use_llm else LLMClient(),
    )

    _render(result, example)

    if out:
        out.mkdir(parents=True, exist_ok=True)
        (out / "judgments.json").write_text(
            result.library.model_dump_json(indent=2), encoding="utf-8"
        )
        if result.agent_config:
            (out / "agent_config.json").write_text(
                result.agent_config.model_dump_json(indent=2), encoding="utf-8"
            )
        console.print(f"\n[green]Wrote[/] {out/'judgments.json'} and {out/'agent_config.json'}")


@app.command(name="observe")
def observe_cmd(
    trace_path: Path = typer.Argument(..., help="A trace as JSONL (one event per line) or JSON."),
) -> None:
    """Detect critical incidents in a trace file."""
    trace = _load_trace(trace_path)
    incidents = observe(trace)
    table = Table(title=f"Critical incidents in {trace_path.name}")
    table.add_column("score", justify="right", style="cyan")
    table.add_column("cues", style="magenta")
    table.add_column("summary")
    for inc in incidents:
        table.add_row(f"{inc.score:.2f}", ", ".join(c.value for c in inc.cues), inc.summary)
    console.print(table)


@app.command()
def init(
    directory: Path = typer.Argument(..., help="Directory to scaffold a blueprint into."),
    domain: str = typer.Option("general", help="Domain, e.g. sales.qualification."),
) -> None:
    """Scaffold a minimal OpenFDE project blueprint."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "project.yaml").write_text(
        "\n".join(
            [
                f"project: {directory.name}",
                f"domain: {domain}",
                "expert: ",
                "goal: ",
                "kpi: ",
                "connectors: []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (directory / "traces").mkdir(exist_ok=True)
    (directory / "judgments").mkdir(exist_ok=True)
    (directory / "ledger.jsonl").touch()
    console.print(
        Panel.fit(
            f"Scaffolded [bold]{directory}[/]\n"
            "  project.yaml   — scenario, goal, KPI, connectors\n"
            "  traces/        — drop expert work traces (JSONL) here\n"
            "  judgments/     — induced Judgment Units land here\n"
            "  ledger.jsonl   — append-only attribution + audit ledger",
            title="openfde init",
        )
    )


@app.command()
def schema(
    which: str = typer.Argument("judgment-unit", help="Schema to print: judgment-unit."),
) -> None:
    """Print a JSON Schema for one of the open standards."""
    if which in ("judgment-unit", "ju", "judgment_unit"):
        console.print_json(json.dumps(JudgmentUnit.model_json_schema()))
    else:
        console.print(f"[red]Unknown schema '{which}'.[/] Try: judgment-unit")
        raise typer.Exit(1)


# --------------------------------------------------------------------------- #
# rendering + IO helpers
# --------------------------------------------------------------------------- #
def _render(result, example: str) -> None:
    console.rule(f"[bold]OpenFDE · FDE Loop[/] · example: {example}")

    # OBSERVE
    t = Table(title="① OBSERVE — critical incidents", show_lines=False)
    t.add_column("score", justify="right", style="cyan")
    t.add_column("cues", style="magenta")
    t.add_column("summary")
    for inc in result.incidents:
        t.add_row(f"{inc.score:.2f}", ", ".join(c.value for c in inc.cues), (inc.summary or "")[:70])
    console.print(t)

    # ELICIT
    if result.sessions:
        s = result.sessions[0]
        lines = []
        for m in s.moves:
            lines.append(f"[dim]{m.phase.value}/{m.probe.value}[/] [bold]Q[/] {m.question}")
            if m.answered:
                lines.append(f"    [green]A[/] {m.answer}")
        console.print(Panel("\n".join(lines), title=f"② ELICIT — session {s.id} · stop={s.status.value}", expand=False))

    # INDUCE
    for ju in result.library.units:
        console.print(_ju_panel(ju))

    # ACT
    if result.agent_config:
        cfg = result.agent_config
        excerpt = cfg.system_prompt[:600] + ("…" if len(cfg.system_prompt) > 600 else "")
        tool_lines = [
            f"- {tp.connector}:{tp.operation} [{tp.kind}]"
            + (" [red](requires approval)[/]" if tp.requires_approval else "")
            for tp in cfg.tools
        ]
        console.print(
            Panel(
                excerpt + ("\n\n[bold]Tool policy[/]\n" + "\n".join(tool_lines) if tool_lines else ""),
                title="④ ACT — compiled agent config (system prompt excerpt)",
                expand=False,
            )
        )

    # ATTRIBUTION + EVOLVE
    if result.ledger is not None:
        credit = result.ledger.credit_by_ju()
        at = Table(title="⑦ ATTRIBUTION — credit assigned to judgments")
        at.add_column("judgment", style="cyan")
        at.add_column("credit", justify="right")
        for ju in result.library.units:
            at.add_row(ju.title[:50], f"{credit.get(ju.id, 0.0):+.3f}")
        console.print(at)

    if result.evolve_report is not None:
        et = Table(title="⑤ EVOLVE — updates from real outcomes")
        et.add_column("judgment", style="cyan")
        et.add_column("action", style="magenta")
        et.add_column("confidence", justify="right")
        et.add_column("autonomy")
        for u in result.evolve_report.updates:
            et.add_row(
                u.title[:40],
                u.action,
                f"{u.confidence_before:.2f} → {u.confidence_after:.2f}",
                f"{u.autonomy_before} → {u.autonomy_after}",
            )
        console.print(et)

    console.rule("[dim]Judgment Units are the reusable, auditable asset the engagement leaves behind.")


def _ju_panel(ju: JudgmentUnit) -> Panel:
    rows = [
        f"[bold]WHEN[/]  {ju.trigger}",
        f"[bold]SIGNALS[/]  " + "; ".join(s.name for s in ju.signals) if ju.signals else "",
        f"[bold]DO[/]  {ju.decision}",
        f"[bold]WHY[/]  {ju.rationale}" if ju.rationale else "",
        f"[bold]REVERSE IF[/]  " + "; ".join(ju.reversal_conditions) if ju.reversal_conditions else "",
        f"[bold]WATCH[/]  " + "; ".join(ju.cues_to_watch) if ju.cues_to_watch else "",
        f"[dim]autonomy={ju.autonomy.value} · confidence={ju.confidence} · readiness="
        f"{ju.stop_snapshot.readiness() if ju.stop_snapshot else 'n/a'} · id={ju.id}[/]",
    ]
    body = "\n".join(r for r in rows if r)
    return Panel(body, title=f"③ INDUCE — Judgment Unit · {ju.title}", expand=False)


def _load_trace(path: Path) -> Trace:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise typer.BadParameter("empty trace file")
    # JSON object with 'events', or JSONL of events.
    if text.lstrip().startswith("{") and '"events"' in text:
        return Trace(**json.loads(text)).ensure_ids()
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        events.append(
            TraceEvent(
                type=EventType(row.get("type", "message")),
                actor=row.get("actor"),
                content=row.get("content", ""),
                metadata=row.get("metadata", {}),
            )
        )
    return Trace(project=path.stem, events=events).ensure_ids()


if __name__ == "__main__":
    app()
