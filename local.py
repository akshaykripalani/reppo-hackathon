"""local.py
A minimal FastMCP wrapper that proxies all orchestration-related tool calls to the
already running orchestrator service (main.py / solver_server.py) via HTTP.

This file is intended to be launched by external clients (e.g., Claude Desktop)
using the `stdio` transport.  It exposes three tools that mirror the
orchestrator public API:

1. discover_mcp_servers
2. find_mcp_tools
3. use_mcp_tool

The wrapper remains stateless and contains no business logic of its own.
"""

from __future__ import annotations

import json
from typing import Any, Dict

import requests
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# URL where the orchestrator FastMCP server is listening (started via `python main.py`)
ORCHESTRATOR_URL = "http://127.0.0.1:8000/mcp"

# ---------------------------------------------------------------------------
# FastMCP instance for the wrapper
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="LocalReppoWrapper",
    instructions=(
        "A thin local wrapper that proxies MCP tool calls to the main Reppo "
        "Orchestrator service running on 127.0.0.1:8000."
    ),
)

# ---------------------------------------------------------------------------
# Pydantic schemas mirroring the orchestrator inputs
# ---------------------------------------------------------------------------

class DiscoverInput(BaseModel):
    """No-arg model for discover_mcp_servers."""

    pass


class FindToolsInput(BaseModel):
    server_name: str = Field(
        ..., description="Name of the target sub-server (e.g. 'sqlite_server')."
    )


class UseToolInput(BaseModel):
    server_name: str = Field(..., description="Target sub-server name.")
    tool_name: str = Field(..., description="Tool to execute on the sub-server.")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Arguments for the selected tool."
    )


# ---------------------------------------------------------------------------
# Internal helper – perform an HTTP POST JSON-RPC call to orchestrator
# ---------------------------------------------------------------------------

def _call_orchestrator(method: str, params: Dict[str, Any]) -> Any:
    """Send a JSON-RPC 2.0 request to the orchestrator and return the result field."""

    payload = {
        "jsonrpc": "2.0",
        "id": "local-wrapper-request",
        "method": method,
        "params": params,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    try:
        response = requests.post(ORCHESTRATOR_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            f"Failed to communicate with orchestrator at {ORCHESTRATOR_URL}: {exc}"
        ) from exc

    if "error" in data:
        # Bubble up orchestrator-side errors
        raise RuntimeError(f"Orchestrator error: {json.dumps(data['error'])}")

    return data.get("result")


# ---------------------------------------------------------------------------
# Tool implementations – thin proxies
# ---------------------------------------------------------------------------


@mcp.tool()
def discover_mcp_servers(_: DiscoverInput) -> Any:  # noqa: D401
    """Proxy to orchestrator's *discover_mcp_servers* tool."""

    return _call_orchestrator(
        method="tools/call",
        params={"name": "discover_mcp_servers", "arguments": {}},
    )


@mcp.tool()
def find_mcp_tools(input_data: FindToolsInput) -> Any:  # noqa: D401
    """Proxy to orchestrator's *find_mcp_tools* tool."""

    return _call_orchestrator(
        method="tools/call",
        params={"name": "find_mcp_tools", "arguments": input_data.model_dump()},
    )


@mcp.tool()
def use_mcp_tool(input_data: UseToolInput) -> Any:  # noqa: D401
    """Proxy to orchestrator's *use_mcp_tool* tool."""

    return _call_orchestrator(
        method="tools/call",
        params={
            "name": "use_mcp_tool",
            "arguments": {"tool_call": input_data.model_dump()},
        },
    )


# ---------------------------------------------------------------------------
# Entrypoint when executed directly – run over stdio so external apps can spawn it.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio") 