"""local.py – *Universal MCP Gateway*
+------------------------------------------------
+You (the LLM) are connected to the outside world through **one** door: this
+minimal FastMCP server.  Think of it as your personal switch-board:
+
+1.   **discover_mcp_servers** – *"What doors are available?"*
+2.   **find_mcp_tools**      – *"What can I do behind a chosen door?"*
+3.   **use_mcp_tool**        – *"Go do it and bring back the answer."*
+
+Every time you need fresh knowledge, live data, or functionality that is not
+already in your weights, follow that three-step workflow **before** you try to
+search the open internet on your own:
+
+    discover → find tools → run tool
+
+Behind the scenes this wrapper performs a single HTTP request to a local
+orchestrator service (http://localhost:8000/mcp/).  The orchestrator, in turn,
+speaks to *any* number of sub-servers—potentially every MCP in existence.
+
+As a result **you inherit the super-powers of every connected MCP** without
+knowing their individual URLs, transports, or authentication details.  When you
+call one of the three tools below, the wrapper handles all that plumbing and
+returns clean JSON.
"""

import requests
import json
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# The URL of the main orchestrator server, which should be running separately.
ORCHESTRATOR_URL = "http://localhost:8000/mcp"

# ---------------------------------------------------------------------------
# FastMCP instance for the local wrapper
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="LocalReppoWrapper",
    instructions="A local wrapper that proxies MCP tool calls to the main Reppo Orchestrator service.",
)

# ---------------------------------------------------------------------------
# Pydantic Schemas for the Wrapper's Tool Inputs
# ---------------------------------------------------------------------------

class FindToolsInput(BaseModel):
    """Input model for the find_mcp_tools tool."""
    server_name: str = Field(..., description="Name of the target sub-server (e.g., 'sqlite_server').")

class UseToolInput(BaseModel):
    """Input model for the use_mcp_tool tool."""
    server_name: str = Field(..., description="Target sub-server name.")
    tool_name: str = Field(..., description="Tool to execute on the sub-server.")
    arguments: dict = Field(default_factory=dict, description="Arguments for the tool.")

# ---------------------------------------------------------------------------
# Internal Helper for Calling the Orchestrator
# ---------------------------------------------------------------------------

def _call_orchestrator(method: str, params: Dict[str, Any]) -> Any:
    """Low-level HTTP helper used by all public tools.

    The wrapper never exposes raw HTTP or JSON-RPC to you.  Instead, each public
    tool calls this helper, which:

    1.  Builds a standards-compliant JSON-RPC 2.0 payload.
    2.  Sends it to the orchestrator via a single POST to `/mcp/`.
    3.  Unwraps *both* FastMCP response envelopes (`structuredContent` and
        nested `{"result": ...}`) so callers receive the **direct** Python
        object they requested (list, dict, int, etc.).

    Args:
        method: The JSON-RPC method (usually ``"tools/call"``).
        params: Arguments for that method.

    Returns:
        The fully-unwrapped ``result`` object ready for consumption.

    Raises:
        RuntimeError: Network error or JSON-RPC error returned by the orchestrator.
    """
    payload = {"jsonrpc": "2.0", "id": "local-wrapper-request", "method": method, "params": params}
    
    # This header is crucial. It tells the orchestrator that this client can
    # handle both JSON and SSE, which satisfies the StreamableHTTP transport's
    # compliance check.
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    
    try:
        response = requests.post(ORCHESTRATOR_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Failed to communicate with orchestrator at {ORCHESTRATOR_URL}: {exc}") from exc

    if "error" in data:
        raise RuntimeError(f"Orchestrator error: {json.dumps(data['error'])}")

    # The orchestrator typically wraps tool output in a CallToolResult that
    # places the actual payload inside the "structuredContent" field.  Some
    # tools (notably our custom orchestrator helpers) already return raw
    # Python objects.  To offer a uniform API to the wrapper tools we
    # transparently unwrap `structuredContent` when it exists.

    result = data.get("result")
    if isinstance(result, dict) and "structuredContent" in result:
        result = result["structuredContent"]
        # Many CallToolResults nest the real payload under a single top-level
        # key named "result" – unwrap that too so our wrapper tools can declare
        # the true return type directly (e.g. List[Dict]).
        if isinstance(result, dict) and set(result.keys()) == {"result"}:
            result = result["result"]
    return result

# ---------------------------------------------------------------------------
# Tool Implementations: The Public API of the Wrapper
# ---------------------------------------------------------------------------

@mcp.tool()
def discover_mcp_servers() -> List[Dict[str, Any]]:
    """Step 1 – **discover** available MCP servers.

    Use this *first* when you are unsure what external knowledge sources or
    capabilities exist.  The orchestrator responds with a list of sub-servers,
    each representing an independent MCP endpoint (could be local utilities,
    remote APIs, or specialised agents).

    Args:
        None

    Returns:
        ``List[Dict]`` – One dict per sub-server containing ``name`` and human-
        readable ``description`` of what the server offers.

    Raises:
        RuntimeError: Propagated from the orchestrator on communication failure.
    """
    result = _call_orchestrator(
        method="tools/call",
        params={"name": "discover_mcp_servers", "arguments": {}},
    )
    return result

@mcp.tool()
def find_mcp_tools(input_data: FindToolsInput) -> List[Dict[str, Any]]:
    """Step 2 – **inspect** a server's toolbox.

    After discovering a promising ``server_name`` call this to enumerate the
    concrete tools it offers.  Typical next step: pick one and feed its
    ``tool_name`` + ``arguments`` to ``use_mcp_tool``.

    Args:
        input_data: ``FindToolsInput`` with the target ``server_name``.

    Returns:
        ``List[Dict]`` – Each dict includes ``name``, ``description``, and
        ``input_schema`` for a tool.

    Raises:
        RuntimeError: If the orchestrator reports an error (e.g. unknown server).
    """
    result = _call_orchestrator(
        method="tools/call",
        params={"name": "find_mcp_tools", "arguments": input_data.model_dump()},
    )
    return result

@mcp.tool()
def use_mcp_tool(input_data: UseToolInput) -> Any:
    """Step 3 – **run** a specific tool.

    Hand the orchestrator exactly *which* server + tool to run and supply any
    arguments.  The wrapper forwards the call, waits for completion, unwraps the
    response, and gives you the raw result.

    Args:
        input_data: ``UseToolInput`` containing
            • ``server_name`` – as returned by ``discover_mcp_servers``
            • ``tool_name``   – as returned by ``find_mcp_tools``
            • ``arguments``   – JSON-serialisable dict matching the tool schema

    Returns:
        The direct result from the sub-server tool (type depends on the tool).

    Raises:
        RuntimeError: If the orchestrator cannot locate or execute the tool.
    """
    result = _call_orchestrator(
        method="tools/call",
        params={
            "name": "use_mcp_tool",
            "arguments": {"tool_call": input_data.model_dump()},
        },
    )
    return result

if __name__ == "__main__":
    # When run directly, this script starts an MCP server over stdio.
    # This is how Claude Desktop will execute it.
    mcp.run(transport="stdio")