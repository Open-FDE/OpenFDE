"""DEPLOY plane — connector registry + reference connectors.

The ecosystem already solves connectivity (MCP, Composio, Temporal). This plane
adds only the thin `ConnectorSpec` declaration and a small registry so ACT can
build a safe tool policy, plus a couple of dependency-free reference connectors
so the loop runs with no external services. Real deployments register MCP /
Composio / database connectors here behind the same spec.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..schema.connector import ConnectorSpec, Operation, OpKind


class Connector:
    """Base reference connector: pairs a ConnectorSpec with callable operations."""

    spec: ConnectorSpec

    def invoke(self, operation: str, **kwargs) -> Any:  # pragma: no cover - overridden
        raise NotImplementedError


class LocalFileConnector(Connector):
    """Read text files from a sandboxed root. Read-only, least privilege."""

    def __init__(self, root: str):
        self.root = Path(root)
        self.spec = ConnectorSpec(
            name="localfile",
            kind="file",
            description=f"Read files under {self.root}",
            auth="none",
            operations=[
                Operation(
                    name="file.read",
                    kind=OpKind.READ,
                    description="Read a UTF-8 text file under the sandbox root",
                    scopes=["file:read"],
                )
            ],
        )

    def invoke(self, operation: str, **kwargs) -> Any:
        if operation != "file.read":
            raise ValueError(f"unknown operation {operation}")
        target = (self.root / kwargs["path"]).resolve()
        if not str(target).startswith(str(self.root.resolve())):
            raise PermissionError("path escapes sandbox root")
        return target.read_text(encoding="utf-8")


class CsvConnector(Connector):
    """Read rows from a CSV as list[dict]. Stand-in for a data source."""

    def __init__(self, path: str, name: str = "csv"):
        self.path = Path(path)
        self.spec = ConnectorSpec(
            name=name,
            kind="db",
            description=f"Tabular source: {self.path.name}",
            operations=[
                Operation(name=f"{name}.rows", kind=OpKind.READ, description="Return all rows", scopes=["data:read"])
            ],
        )

    def invoke(self, operation: str, **kwargs) -> Any:
        with self.path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))


class MockCrmConnector(Connector):
    """In-memory CRM with a destructive, approval-gated write op.

    Exists to demonstrate the governance path: `crm.update_stage` is marked
    `requires_approval`, so ACT will never let an agent run it at 'auto' without
    a human. No real data leaves the process.
    """

    def __init__(self):
        self.leads: Dict[str, Dict[str, Any]] = {}
        self.spec = ConnectorSpec(
            name="mockcrm",
            kind="http",
            description="Mock CRM for demos and tests",
            auth="api_key",
            operations=[
                Operation(name="crm.get_lead", kind=OpKind.READ, description="Fetch a lead", scopes=["crm:read"]),
                Operation(
                    name="crm.update_stage",
                    kind=OpKind.WRITE,
                    description="Advance a lead's pipeline stage",
                    scopes=["crm:write"],
                    destructive=False,
                    requires_approval=True,  # external-facing change → human in the loop
                ),
            ],
        )

    def invoke(self, operation: str, **kwargs) -> Any:
        if operation == "crm.get_lead":
            return self.leads.get(kwargs["lead_id"])
        if operation == "crm.update_stage":
            lead = self.leads.setdefault(kwargs["lead_id"], {"id": kwargs["lead_id"]})
            lead["stage"] = kwargs["stage"]
            return lead
        raise ValueError(f"unknown operation {operation}")


class ConnectorRegistry:
    """Holds registered connectors and exposes their specs to ACT."""

    def __init__(self):
        self._connectors: Dict[str, Connector] = {}

    def register(self, connector: Connector) -> Connector:
        self._connectors[connector.spec.name] = connector
        return connector

    def get(self, name: str) -> Optional[Connector]:
        return self._connectors.get(name)

    def specs(self) -> List[ConnectorSpec]:
        return [c.spec for c in self._connectors.values()]
