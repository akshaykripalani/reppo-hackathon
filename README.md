# Giga-MCP Demo: MCP Orchestrator 🧩

A **self-contained local demonstration** of an _MCP Orchestrator_ that aggregates the capabilities of several small worker MCP servers.  The orchestrator exposes three high-level tools that let any MCP client:

1. Discover which sub-servers are running  
2. Inspect the tools each sub-server offers  
3. Proxy a call to any of those tools — all through a single endpoint


---

## Project Structure

```text
solver-node/
├── local.py             # THIS IS WHAT THE USER HAS TO USE, EVERYTHING BEYOND IS PURE TECHNICALS
├── main.py              # Entry point – starts the orchestrator FastMCP server
├── solver_server.py     # Orchestrator implementation & lifespan manager
├── manifest.json        # Declares sub-servers to launch (command + args)
├── pyproject.toml       # Minimal dependencies (only mcp[cli])
└── sub_servers/
    ├── __init__.py
    ├── adder_server.py      # add(a, b)
    ├── random_server.py     # generate_random(min, max)
    └── sqlite_server.py     # query_nba_stats(sql_query)
```

---

## Quick Start
### Note: The Remote MCPs in this server have already been hosted at https://mcp.akshaykripalani.tech/mcp/
### Feel free to use those rather than running any of these locally! (except local.py, which you will have to)

### 1. Install dependency
```bash
pip install "mcp[cli]"
```

### 2. Add to Claude Desktop!
"giga-mcp": {
      "type": "mcp",
      "command": "C:\\Akshay\\Projects\\solver-node\\.venv\\Scripts\\python.exe",
      "args": [
        "/path/to/local.py"
      ]
    }


### Should you wish to self host it all yourself
1. Install dependencies using uv
2. Run main.py in a separate terminal window
3. Use claude desktop as normal
---

## How It Works

1. **Lifespan Manager** (`app_lifespan` in `solver_server.py`)
   * Reads `manifest.json`
   * `subprocess.Popen` launches each worker with `stdin/stdout` pipes
   * `ClientSessionGroup` connects to each process using `StdioServerParameters`
   * A `name_hook` prefixes every imported tool with `<ServerName>::` to avoid name collisions
   * On shutdown (Ctrl-C) all child processes are terminated cleanly

2. **Orchestrator Tools**
   * `discover_mcp_servers`  → `List[ServerInfo]`
   * `find_mcp_tools`        → `List[ToolInfo]`
   * `use_mcp_tool`          → proxied result of any worker tool

3. **Workers** (`sub_servers/…`)
   * Each is a tiny FastMCP server running over `stdio`
   * Demonstrate distinct capabilities and schemas

4. **Local Wrapper** (`local.py`)
    * Tiny FastMCP server running over `stdio`
    * Mirrors the orchestrator tools and proxies them to `http://localhost:8000/mcp/`
    * Perfect for desktop apps (e.g. Claude Desktop) that launch a local process but don't embed HTTP logic

---

## Extending the Demo

* **Add a new worker**  
  1. Create `sub_servers/my_server.py` with a FastMCP instance & tool(s)  
  2. Add an entry to `manifest.json`  
  3. Restart the orchestrator – no other code changes required.

* **Swap transport**  
  Change `transport="sse"` in `main.py` to `http` or `websocket` if preferred.

* **Deploy remotely**  
  Because each worker is launched via `manifest.json`, you could point to remote TCP servers instead of local processes by switching to `HttpServerParameters` / `WebSocketServerParameters`.

---

## License

Distributed under the **MIT License**.  See [`LICENSE`](LICENSE) for full text.
