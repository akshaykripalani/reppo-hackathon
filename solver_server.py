import subprocess
import json
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context
from mcp.client.session_group import ClientSessionGroup
from mcp.client.stdio import StdioServerParameters
from mcp.types import Implementation as MCPImplementation
from pydantic import BaseModel, Field

# --- Pydantic Models for our new tools' inputs/outputs ---

class ServerInfo(BaseModel):
    name: str
    description: Optional[str] = None

class ToolInfo(BaseModel):
    name: str
    description: Optional[str]
    input_schema: Dict[str, Any]

class UseToolInput(BaseModel):
    server_name: str = Field(description="The name of the target MCP server (e.g., 'sqlite_server').")
    tool_name: str = Field(description="The name of the tool to execute on that server (e.g., 'query_nba_stats').")
    arguments: Dict[str, Any] = Field(description="A JSON object of arguments for the tool.")

# --- Application Context ---

class AppContext(BaseModel):
    session_group: ClientSessionGroup
    sub_processes: Dict[str, subprocess.Popen]
    server_configs: Dict[str, Dict[str, Any]]

    class Config:
        arbitrary_types_allowed = True

# --- Lifespan Management ---

@asynccontextmanager
async def app_lifespan(app: FastMCP):
    print("Orchestrator: Starting sub-servers...")
    sub_processes: Dict[str, subprocess.Popen] = {}
    server_params: List[StdioServerParameters] = []
    config_path = Path("manifest.json")
    server_configs = json.loads(config_path.read_text()) if config_path.exists() else {}
    for name, config in server_configs.items():
        # Resolve the interpreter: use current Python executable unless config explicitly points elsewhere
        interpreter = config.get("command", "python")
        if interpreter == "python":
            import sys
            interpreter = sys.executable  # ensures we use the same venv interpreter

        command = [interpreter, *config["args"]]
        print(f"Orchestrator: Launching '{name}' with command: {' '.join(command)}")
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        sub_processes[name] = proc
        server_params.append(StdioServerParameters(**config))
    def name_hook(component_name: str, server_info: MCPImplementation) -> str:
        return f"{server_info.name}::{component_name}"
    session_group = ClientSessionGroup(component_name_hook=name_hook)
    app_context = AppContext(session_group=session_group, sub_processes=sub_processes, server_configs=server_configs)

    async with session_group:
        for params in server_params:
            await session_group.connect_to_server(params)
        print("Orchestrator: All sub-servers connected and ready.")
        
        # We yield the AppContext object directly, not in a dictionary.
        yield app_context

    # This shutdown logic is correct and remains unchanged.
    print("Orchestrator: Shutting down sub-servers...")
    for name, proc in sub_processes.items():
        print(f"Orchestrator: Terminating '{name}' (PID: {proc.pid})...")
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("Orchestrator: Shutdown complete.")

# --- Main MCP Server Instance ---

mcp = FastMCP(
    name="ReppoOrchestratorServer",
    instructions="A meta-server that discovers and proxies requests to other MCP servers.",
    host="0.0.0.0",
    port=8000,
    stateless_http=True,
    json_response=True,
    lifespan=app_lifespan,  # critical to ensure sub-servers start
)

# --- Orchestrator Tools ---

@mcp.tool()
def discover_mcp_servers(ctx: Context) -> List[ServerInfo]:
    """Lists all configured and running MCP sub-servers managed by this orchestrator."""
    maybe_ctx = ctx.request_context.lifespan_context
    if isinstance(maybe_ctx, dict):
        # If yielded as {"orchestrator_context": AppContext}
        inner = maybe_ctx.get("orchestrator_context")
        if isinstance(inner, AppContext):
            maybe_ctx = inner
        else:
            # Fall back to constructing an AppContext from dict fields (if possible)
            try:
                maybe_ctx = AppContext(**maybe_ctx)  # type: ignore[arg-type]
            except Exception:
                pass

    # At this point `maybe_ctx` is either an AppContext or still a dict.  Handle both.
    if isinstance(maybe_ctx, AppContext):
        server_configs = maybe_ctx.server_configs
        sub_processes = maybe_ctx.sub_processes
    elif isinstance(maybe_ctx, dict):
        server_configs = maybe_ctx.get("server_configs", {})
        sub_processes = maybe_ctx.get("sub_processes", {})
    else:
        raise TypeError("Unsupported lifespan_context type; expected AppContext or dict")

    return [
        ServerInfo(
            name=name,
            description=config.get("description")
        ) for name, config in server_configs.items()
    ]

@mcp.tool()
def find_mcp_tools(server_name: str, ctx: Context) -> List[ToolInfo]:
    """Finds all available tools for a specific managed MCP server."""
    maybe_ctx = ctx.request_context.lifespan_context
    if isinstance(maybe_ctx, dict):
        inner = maybe_ctx.get("orchestrator_context")
        if isinstance(inner, AppContext):
            maybe_ctx = inner
        else:
            try:
                maybe_ctx = AppContext(**maybe_ctx)  # type: ignore[arg-type]
            except Exception:
                pass

    if isinstance(maybe_ctx, AppContext):
        app_context = maybe_ctx
    elif isinstance(maybe_ctx, dict) and "session_group" in maybe_ctx:
        app_context = AppContext(
            session_group=maybe_ctx["session_group"],
            sub_processes=maybe_ctx.get("sub_processes", {}),
            server_configs=maybe_ctx.get("server_configs", {}),
        )
    else:
        raise TypeError("Unsupported lifespan_context type")

    session_group = app_context.session_group

    # Logic for finding tools.
    server_class_name = server_name
    prefix = f"{server_class_name}::"
    found_tools = [
        ToolInfo(
            name=tool.name,
            description=tool.description,
            input_schema=tool.inputSchema,
        )
        for qualified_name, tool in session_group.tools.items()
        if qualified_name.startswith(prefix)
    ]
    if not found_tools:
        raise ValueError(f"No server found with name '{server_name}' or it has no tools.")
    return found_tools

@mcp.tool()
async def use_mcp_tool(tool_call: UseToolInput, ctx: Context) -> Any:
    """Acts as a proxy to call a tool on a specified MCP sub-server."""
    maybe_ctx = ctx.request_context.lifespan_context
    if isinstance(maybe_ctx, dict):
        inner = maybe_ctx.get("orchestrator_context")
        if isinstance(inner, AppContext):
            maybe_ctx = inner
        else:
            try:
                maybe_ctx = AppContext(**maybe_ctx)  # type: ignore[arg-type]
            except Exception:
                pass

    if isinstance(maybe_ctx, AppContext):
        app_context = maybe_ctx
    elif isinstance(maybe_ctx, dict) and "session_group" in maybe_ctx:
        app_context = AppContext(
            session_group=maybe_ctx["session_group"],
            sub_processes=maybe_ctx.get("sub_processes", {}),
            server_configs=maybe_ctx.get("server_configs", {}),
        )
    else:
        raise TypeError("Unsupported lifespan_context type")

    session_group = app_context.session_group

    # Logic for calling tools.
    server_class_name = tool_call.server_name
    qualified_tool_name = f"{server_class_name}::{tool_call.tool_name}"
    if qualified_tool_name not in session_group.tools:
        raise ValueError(
            f"Tool '{tool_call.tool_name}' not found on server '{tool_call.server_name}'."
        )

    await ctx.info(f"Proxying call to '{qualified_tool_name}' with args: {tool_call.arguments}")
    result = await session_group.call_tool(name=qualified_tool_name, args=tool_call.arguments)
    return result.structuredContent