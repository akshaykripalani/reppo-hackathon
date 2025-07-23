# Giga MCP Demo 🚀

An **MCP orchestrator** that behaves like an API gateway: it discovers remote sub-servers (other MCPs), lets you inspect their tools, and proxies calls — so your LLM only talks to **one** endpoint.

* discover → find tools → run tool
* No need to self-host every worker; the orchestrator connects dynamically.

---
### This project won the Protocol Labs: Modular Worlds hackathon!
Demo video: https://youtu.be/B0gXihBZpTE
---
## ⚡ Quick Start

You have **two ways to play**:

### A) Just connect to the public Giga-MCP network

```bash
uv pip install "mcp[cli]>=1.10.1" requests   # or plain pip
python local.py   # points to the public gateway by default
```

`local.py` runs over stdio, so drop it straight into Claude Desktop and the LLM instantly gains access to every tool on the network.

### B) Run your **own** mini-network locally

```bash
uv pip install "mcp[cli]>=1.10.1" requests
python main.py      # launches orchestrator on http://127.0.0.1:6969/mcp/

# (Optional) connect via the wrapper instead of curl
ORCHESTRATOR_URL=http://localhost:6969/mcp/ python local.py
```

That's it! No Docker, no databases to install.

---

## Project Structure

```
solver-node/
├── main.py              # starts orchestrator
├── solver_server.py     # orchestrator impl + lifespan
├── local.py             # stdio wrapper (gateway for LLMs)
├── manifest.json        # declares sub-servers
└── sub_servers/         # example worker MCPs
    ├── __init__.py
    ├── adder_server.py
    ├── nba_players.db
    ├── random_server.py
    └── sqlite_server.py
```

---

## How It Works

### Layout diagram

```
+-----------------+      (Runs & communicates      +------------------------------------------+
|                 |         via stdio)             |                                          |
|  Claude Client  | <============================> |  local.py (LocalReppoWrapper)            |
|                 |                                |  - A stdio MCP server for the client     |
+-----------------+                                |  - Proxies calls to the orchestrator     |
                                                   +------------------------------------------+
                                                                         |
                                                                         | (HTTP/S Request)
                                                                         | ORCHESTRATOR_URL=https://mcp.akshaykripalani.tech/mcp/
                                                                         |
                                                                        _V_
+------------------------------------------------------------------------------------------------------+
|                                                                                                      |
|   Giga-MCP Orchestrator (solver_server.py)                                                           |
|   - Listens on HTTP, manages sub-server lifecycle.                                                   |
|   - Uses ClientSessionGroup to talk to sub-servers.                                                  |
|                                                                                                      |
|   +-------------------+       (Reads on startup)       +-----------------------------------------+   |
|   |   manifest.json   | -----------------------------> | Lifespan Manager (launches sub-servers) |   |
|   | - adder_server    |                                +-----------------------------------------+   |
|   | - random_server   |                                                  |                           |
|   | - sqlite_server   |                                                  | (Launches & Manages via   |
|   +-------------------+                                                  |  subprocess & stdio)      |
|                                                                          |                           |
|      (Proxies tool calls via stdio pipes)                                V                           |
|    .----------------------------------------------------------------------|---------------.          |
|    |                          |                             |                             |          |
|   _V_                        _V_                           _V_                           _V_         |
+----+--------------------------+-----------------------------+-----------------------------+----------+
     |                          |                             |                             |
(stdio pipe)               (stdio pipe)                  (stdio pipe)                  (reads from)
     |                          |                             |                             |
+----V-------------+ +----------V-----------+ +---------------V----------+ +------------------+
| adder_server.py  | |   random_server.py   | |    sqlite_server.py      | | nba_players.db   |
| - tool: add()    | | - tool: generate...()| | - tool: query_nba_stats()| | (SQLite Database)|
+------------------+ +----------------------+ +--------------------------+ +------------------+
                                                             |                      |
                                                             '----------------------'
```


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
