"""MCP client implementation for data generation using simple HTTP."""

import os
import logging
import httpx
from typing import Dict, Any

import mcp.types as types

logger = logging.getLogger('MCPClient')

class MCPClient:
    """MCP client for calling remote data nodes via HTTP."""

    def __init__(self):
        """Initialize MCP client"""
        self.timeout = int(os.getenv("MCP_CLIENT_TIMEOUT", "30"))

    async def execute_rfd(self, rfd: Dict[str, Any], node_url: str) -> Dict[str, Any]:
        """
        Execute an RFD on a remote data node using a simple HTTP POST request.
        
        Args:
            rfd: The Request for Data
            node_url: The URL of the target MCP server data node
            
        Returns:
            The dataset returned from the remote node
        """
        request_id = 1
        json_rpc_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "process_rfd", "arguments": rfd},
            "id": request_id,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Sending POST request to {node_url}")
                response = await client.post(node_url, json=json_rpc_payload)
                response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
                
                response_data = response.json()
                
                if "error" in response_data:
                    error = response_data["error"]
                    logger.error(f"Received error from server: {error}")
                    raise RuntimeError(f"MCP Error: {error.get('message', 'Unknown error')}")
                    
                logger.info(f"Successfully received result from {node_url}")
                return response_data.get("result", {})

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred while calling {node_url}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Failed to execute RFD on remote node {node_url}: {e}")
            raise 