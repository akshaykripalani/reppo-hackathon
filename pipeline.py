"""
Main pipeline for the RFD Solver Node.

This script monitors a directory for incoming RFD files, routes them to the
appropriate data node, executes them, and prints the result.
"""

import time
import logging
import json
from pathlib import Path
import asyncio

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from datasolver.router import Router
from datasolver.providers.mcp.client import MCPClient

# --- Configuration ---
WATCH_DIRECTORY = "rfd_inbox"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RFDHandler(FileSystemEventHandler):
    """Handles new RFD files created in the watch directory."""
    
    def __init__(self, router: Router, mcp_client: MCPClient):
        self.router = router
        self.mcp_client = mcp_client
        self._processed_files = set()

    def on_created(self, event):
        """Called when a file or directory is created."""
        if not event.is_directory and event.src_path not in self._processed_files:
            # Since this is a sync callback, we need to run our async code
            # in a new event loop or schedule it on a running one.
            # For simplicity, we'll run it here.
            asyncio.run(self.process_rfd_async(event.src_path))

    async def process_rfd_async(self, file_path: str):
        """Asynchronously reads, routes, and executes an RFD."""
        self._processed_files.add(file_path)
        logging.info(f"New RFD file detected: {file_path}")
        try:
            with open(file_path, 'r') as f:
                rfd = json.load(f)
            
            service = rfd.get("service")
            if not service:
                logging.error(f"RFD {file_path} is missing the required 'service' key.")
                return

            node_url = self.router.get_node_url(service)
            if not node_url:
                logging.error(f"Could not find a data node for service '{service}'.")
                return
                
            logging.info(f"Routing RFD to {node_url} for service '{service}'")
            result = await self.mcp_client.execute_rfd(rfd, node_url)
            
            logging.info("--- RFD Execution Result ---")
            logging.info(json.dumps(result, indent=2))
            logging.info("--------------------------")

        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in RFD file: {file_path}")
        except Exception as e:
            logging.error(f"An error occurred while processing {file_path}: {e}")

def main():
    """Starts the solver node pipeline."""
    # Ensure the watch directory exists
    Path(WATCH_DIRECTORY).mkdir(exist_ok=True)
    
    # Initialize components
    router = Router()
    mcp_client = MCPClient()
    
    # Set up the watchdog file observer
    event_handler = RFDHandler(router, mcp_client)
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
    
    logging.info(f"Solver node started. Watching for RFDs in ./{WATCH_DIRECTORY}")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Solver node shutting down.")
    
    observer.join()

if __name__ == "__main__":
    main() 