# main.py
"""Main entry point for the solver node."""

import click
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the mcp instance from our server file
from solver_server import mcp as orchestrator_server
BANNER = """
 ██████╗ ██╗ ██████╗  █████╗ ███╗   ███╗ ██████╗██████╗ 
██╔════╝ ██║██╔════╝ ██╔══██╗████╗ ████║██╔════╝██╔══██╗
██║  ███╗██║██║  ███╗███████║██╔████╔██║██║     ██████╔╝
██║   ██║██║██║   ██║██╔══██║██║╚██╔╝██║██║     ██╔═══╝ 
╚██████╔╝██║╚██████╔╝██║  ██║██║ ╚═╝ ██║╚██████╗██║     
 ╚═════╝ ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝╚═╝     
"""

@click.command()
def start():
    """Starts the Reppo Solver Orchestrator MCP Server."""
    print(BANNER)
    logging.info("Starting Reppo Orchestrator MCP Server on port 6969...")
    try:
        orchestrator_server.run(transport="streamable-http")
    except KeyboardInterrupt:
        logging.info("Server stopped by user.")
    except Exception as e:
        logging.error(f"Server failed to start: {e}", exc_info=True)


if __name__ == '__main__':
    start()