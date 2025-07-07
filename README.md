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
By default the server now binds to **port 6969** and all interfaces.  Override
with the ``MCP_PORT``/``MCP_HOST`` environment variables if needed.

```bash
# defaults → http://127.0.0.1:6969/mcp/
python main.py
# or customise
MCP_PORT=8080 MCP_HOST=0.0.0.0 python main.py
```
You should see output like:

```
Orchestrator: Starting sub-servers...
Orchestrator: Launching 'adder_server' with command: ... python.exe sub_servers/adder_server.py
Orchestrator: All sub-servers connected and ready.
```

### 3. Connect with MCP clients

The `local.py` wrapper now defaults to the same port (6969).  Point it
elsewhere by setting ``ORCHESTRATOR_URL`` first.

```bash
# local proxy to default localhost:6969
python local.py

# or remote gateway
ORCHESTRATOR_URL="https://mcp.akshaykripalani.tech/mcp/" python local.py
```

* `discover_mcp_servers` – list available sub-servers (name + description)

Configure your MCP client to launch `python local.py` and it will automatically
proxy all requests to the running orchestrator service.

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
