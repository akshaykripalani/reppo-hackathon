"""
A mock MCP server that simulates an external data node.

This server hosts a simple tool that can be called by the main solver node
to test routing and remote execution functionality.

To run:
uvicorn mock_mcp_server:server.app --host 127.0.0.1 --port 8001
"""

from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the MCP server instance
server = FastMCP(
    name="Mock NBA Stats Data Node",
    instructions="A mock MCP server that provides NBA player statistics."
)

# Call a method on the server object to get the actual ASGI app.
app = server.streamable_http_app()

@server.tool()
async def process_rfd(rfd: Dict[str, Any], ctx: Context) -> None:
    """
    Processes a Request for Data (RFD) and returns a mock dataset.
    This simulates a real data node fetching and returning data.
    """
    logger.info(f"Mock server received RFD: {rfd}")
    
    service = rfd.get("service")
    if service != "nba_player_stats":
        result = {
            "error": "Service not supported",
            "details": f"This node only supports 'nba_player_stats', not '{service}'."
        }
    else:
        metrics = rfd.get("metrics", ["points"])
        season = rfd.get("season", "2024-25")
        
        # Mock data generation
        mock_data = [
            {"player": "LeBron James", "season": season, "stats": {m: 30 for m in metrics}},
            {"player": "Stephen Curry", "season": season, "stats": {m: 28 for m in metrics}},
            {"player": "Nikola Jokic", "season": season, "stats": {m: 26 for m in metrics}},
        ]
        
        logger.info("Successfully processed RFD and returning mock data.")
        
        result = {
            "status": "success",
            "data": mock_data
        }
    
    await ctx.return_value(result) 