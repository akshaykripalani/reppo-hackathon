import json
import logging
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from datasolver.providers.mcp.client import MCPClient
from datasolver.router import Router
from pipeline import RFDHandler
import httpx

# --- Test Fixture to run Mock Server ---

class MockServer(threading.Thread):
    def __init__(self, host="127.0.0.1", port=8001):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.server = None

    def run(self):
        config = uvicorn.Config("mock_mcp_server:app", host=self.host, port=self.port, log_level="info")
        self.server = uvicorn.Server(config)
        self.server.run()

    def shutdown(self):
        if self.server:
            self.server.should_exit = True
            
@pytest.fixture(scope="module")
def mock_server():
    """Starts the mock MCP server in a background thread for the test module."""
    server = MockServer()
    server.start()
    
    # Health check to ensure the server is ready before tests run
    is_ready = False
    for _ in range(10): # Try for 1 second
        try:
            with httpx.Client() as client:
                response = client.get("http://127.0.0.1:8001")
                if response.status_code in [200, 404]: # 404 is ok, means routing is working
                    is_ready = True
                    break
        except httpx.ConnectError:
            time.sleep(0.1)
    
    if not is_ready:
        raise RuntimeError("Mock server did not start in time.")
        
    yield
    server.shutdown()
    server.join(timeout=2)


# --- Integration Test ---

@pytest.mark.anyio
async def test_pipeline_end_to_end(tmp_path, caplog, mock_server):
    """
    Tests the full pipeline from file creation to remote execution and result logging.
    """
    # 1. Arrange: Set up a temporary environment
    rfd_inbox = tmp_path / "rfd_inbox"
    rfd_inbox.mkdir()
    
    nodes_file = tmp_path / "nodes.json"
    nodes_file.write_text(json.dumps({
        "nba_player_stats": "http://127.0.0.1:8001"
    }))
    
    rfd_content = {
        "rfd_id": "integration_test_001",
        "service": "nba_player_stats",
        "metrics": ["points"],
        "season": "2024-25"
    }
    rfd_file = rfd_inbox / "test_rfd.json"
    rfd_file.write_text(json.dumps(rfd_content))

    # 2. Act: Initialize components and process the RFD
    router = Router(registry_path=nodes_file)
    mcp_client = MCPClient()
    handler = RFDHandler(router, mcp_client)
    
    with caplog.at_level(logging.INFO):
        await handler.process_rfd_async(str(rfd_file))

    # 3. Assert: Check the log output for the final result
    assert "Routing RFD to http://127.0.0.1:8001 for service 'nba_player_stats'" in caplog.text
    
    # Check for the key parts of the successful output
    assert "--- RFD Execution Result ---" in caplog.text
    assert '"status": "success"' in caplog.text
    assert '"player": "LeBron James"' in caplog.text 