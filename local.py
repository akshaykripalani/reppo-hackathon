"""
MCP Local Wrapper for Claude Desktop Integration.

This script acts as a thin, stateless proxy server that runs locally. Its sole
purpose is to be launched as a `stdio`-based process by an external MCP client
like Claude Desktop.

It exposes a set of high-level tools that mirror the capabilities of a remote
orchestrator service. When one of its tools is called, this wrapper makes a
standard, one-off HTTP POST request to the main orchestrator server, forwards the
arguments, and returns the result.

This architecture solves two key problems:
1.  It provides a stable, launchable process for clients like Claude Desktop that
    expect to manage a server's lifecycle.
2.  It decouples the main application logic (the orchestrator) from the
    client-facing integration point, allowing the main service to be hosted
    anywhere and communicate via standard HTTP.
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
    """
    Sends a JSON-RPC 2.0 request and returns the 'result' field.

    This function is the core of the proxy logic. It constructs a valid MCP
    request and handles the HTTP communication.

    Args:
        method: The JSON-RPC method to call (e.g., "tools/call").
        params: The parameters for the JSON-RPC method.

    Returns:
        The "result" field from the orchestrator's JSON-RPC response.

    Raises:
        RuntimeError: If the HTTP request fails or the orchestrator returns an error.
    """
    payload = {"jsonrpc": "2.0", "id": "local-wrapper-request", "method": method, "params": params}
    
    # This header is crucial. It tells the orchestrator that this client can
    # handle both JSON and SSE, which satisfies the StreamableHTTP transport's
    # compliance check.
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    try:
        response = requests.post(ORCHESTRATOR_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Failed to communicate with orchestrator at {ORCHESTRATOR_URL}: {exc}") from exc

    if "error" in data:
        raise RuntimeError(f"Orchestrator error: {json.dumps(data['error'])}")

    return data.get("result")

# ---------------------------------------------------------------------------
# Tool Implementations: The Public API of the Wrapper
# ---------------------------------------------------------------------------

@mcp.tool()
def discover_mcp_servers() -> List[Dict[str, Any]]:
    """
    Discovers the available sub-servers managed by the main orchestrator.
    This tool takes no arguments. It acts as a proxy to the orchestrator's
    `discover_mcp_servers` tool.

    Returns:
        A list of objects, each describing a configured sub-server, its process ID,
        and its launch command.
    """
    result = _call_orchestrator(
        method="tools/call",
        params={"name": "discover_mcp_servers", "arguments": {}},
    )
    # The orchestrator's tool returns structured content which we pass through.
    return result["structuredContent"]["result"]

@mcp.tool()
def find_mcp_tools(input_data: FindToolsInput) -> List[Dict[str, Any]]:
    """
    Finds all available tools for a specific managed MCP sub-server.
    This acts as a proxy to the orchestrator's `find_mcp_tools` tool.

    Args:
        input_data: An object containing the `server_name` to inspect.

    Returns:
        A list of objects, each describing a tool available on the target sub-server.
    """
    result = _call_orchestrator(
        method="tools/call",
        params={"name": "find_mcp_tools", "arguments": input_data.model_dump()},
    )
    return result["structuredContent"]["result"]

@mcp.tool()
def use_mcp_tool(input_data: UseToolInput) -> Any:
    """
    Executes a tool on a specific sub-server by proxying the request through the orchestrator.
    This is the main entry point for using the capabilities of the underlying worker servers.

    Args:
        input_data: An object specifying the `server_name`, `tool_name`, and the `arguments` for the target tool.

    Returns:
        The direct result from the executed sub-server tool, passed through by the orchestrator.
    """
    result = _call_orchestrator(
        method="tools/call",
        params={
            "name": "use_mcp_tool",
            "arguments": {"tool_call": input_data.model_dump()},
        },
    )
    return result["structuredContent"]

if __name__ == "__main__":
    # When run directly, this script starts an MCP server over stdio.
    # This is how Claude Desktop will execute it.
    mcp.run(transport="stdio")