# Giga-MCP Demo: MCP Orchestrator 🧩

A **self-contained local demonstration** of an _MCP Orchestrator_ that aggregates the capabilities of several small worker MCP servers.  The orchestrator exposes three high-level tools that let any MCP client:

1. Discover which sub-servers are running  
2. Inspect the tools each sub-server offers  
3. Proxy a call to any of those tools — all through a single endpoint

No blockchain, IPFS, or other production complexity — just pure MCP over `stdio` / `sse` for easy local experimentation.

---

## Project Structure

```text
solver-node/
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

### 1. Install dependency
```bash
pip install "mcp[cli]>=1.10.1"
```

### 2. Run the orchestrator
```bash
python main.py          # starts on http://127.0.0.1:8000 using SSE transport
```
You should see log output indicating that three sub-servers were launched and connected.

### 3. Explore with MCP Inspector
```bash
mcp dev solver_server.py:mcp
```
This opens a browser UI where you can:

* `discover_mcp_servers` – list the worker PIDs and launch commands
* `find_mcp_tools` – e.g. `{ "server_name": "sqlite_server" }`
* `use_mcp_tool` – proxy a call:
  ```jsonc
  {
    "tool_call": {
      "server_name": "sqlite_server",
      "tool_name": "query_nba_stats",
      "arguments": {
        "sql_query": "SELECT name, points FROM players WHERE points > 26;"
      }
    }
  }
  ```

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
