"""DEPLOY plane schema — the Connector Spec.

DEPLOY is the plane that lets an agent actually live in the customer's real
system of work (CRM, ERP, IM, docs) with real auth, scopes and audit. The
open-source ecosystem here is already strong — MCP, Composio, Temporal,
OpenTelemetry — so OpenFDE does NOT re-invent connectors. It defines a thin
**Connector Spec** so that connectors declare, uniformly:

    - what they can read and write (operations + schemas)
    - the least-privilege scopes they need
    - whether an operation is destructive / needs approval
    - how their events feed OBSERVE and ATTRIBUTION

and then adapts existing connectors (an MCP server, a Composio tool, a plain
CSV file) into that shape. Enterprise reality — permissioning and integration —
is front-loaded here, because that is where most deployments actually stall.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class OpKind(str, Enum):
    READ = "read"
    WRITE = "write"
    ACTION = "action"    # side-effecting, e.g. "send_email"


class Operation(BaseModel):
    name: str = Field(..., description="e.g. 'crm.update_stage'")
    kind: OpKind = OpKind.READ
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    destructive: bool = Field(False, description="True if it changes external state irreversibly")
    requires_approval: bool = Field(
        False, description="If True, an agent may never run it at 'auto' autonomy without approval"
    )
    scopes: List[str] = Field(default_factory=list, description="Least-privilege scopes required")


class ConnectorSpec(BaseModel):
    """A uniform declaration of a connection into a customer system.

    Adapters map MCP servers / Composio tools / databases / files into this
    shape; the spec is what ACT reads to build a safe tool policy.
    """

    name: str
    kind: str = Field("generic", description="'mcp' | 'composio' | 'db' | 'file' | 'http' | ...")
    description: str = ""
    auth: str = Field("none", description="'none' | 'api_key' | 'oauth' | 'iam' — never store secrets here")
    operations: List[Operation] = Field(default_factory=list)
    emits_events: bool = Field(
        True, description="Whether this connector's activity should feed OBSERVE / ATTRIBUTION"
    )
    audit: bool = Field(True, description="Whether operations are written to the audit log")

    def operation(self, name: str) -> Optional[Operation]:
        return next((o for o in self.operations if o.name == name), None)

    def writable_ops(self) -> List[Operation]:
        return [o for o in self.operations if o.kind in (OpKind.WRITE, OpKind.ACTION)]
