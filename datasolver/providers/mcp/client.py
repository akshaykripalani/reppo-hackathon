"""MCP client implementation for data generation."""

import os
import logging
import asyncio
from typing import Dict, Any

from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.message import SessionMessage
import mcp.types as types

logger = logging.getLogger('MCPClient')

class MCPClient:
    """MCP client for calling remote data nodes"""

    def __init__(self):
        """Initialize MCP client"""
        self.timeout = int(os.getenv("MCP_CLIENT_TIMEOUT", "30"))

    async def execute_rfd(self, rfd: Dict[str, Any], node_url: str) -> Dict[str, Any]:
        """
        Execute an RFD on a remote data node using the streamablehttp_client.
        """
        mcp_endpoint_url = f"{node_url.rstrip('/')}/mcp"

        try:
            async with streamablehttp_client(mcp_endpoint_url, timeout=self.timeout) as (read_stream, write_stream, _):
                # Step 1: Initialize the session
                init_id = 0
                init_request = types.JSONRPCRequest(
                    jsonrpc="2.0",
                    method="initialize",
                    params={"protocolVersion": "1.0"},
                    id=init_id
                )
                await write_stream.send(SessionMessage(message=types.JSONRPCMessage(root=init_request)))
                
                # Wait for initialize result
                async for init_response in read_stream:
                    if hasattr(init_response.message, 'id') and init_response.message.id == init_id:
                        logger.info("Session initialized successfully.")
                        break
                
                # Step 2: Call the tool
                request_id = 1
                request = types.JSONRPCRequest(
                    jsonrpc="2.0",
                    method="tools/call",
                    params={"name": "process_rfd", "arguments": rfd},
                    id=request_id,
                )
                json_rpc_message = types.JSONRPCMessage(root=request)
                session_message = SessionMessage(message=json_rpc_message)
                
                logger.info(f"Sending tools/call request to {mcp_endpoint_url}")
                await write_stream.send(session_message)

                # Wait for the corresponding response
                async for response_message in read_stream:
                    if hasattr(response_message.message, 'id') and response_message.message.id == request_id:
                        if isinstance(response_message.message, types.JSONRPCResponse):
                            logger.info(f"Received response from {mcp_endpoint_url}")
                            return response_message.message.result
                        
                        if isinstance(response_message.message, types.JSONRPCError):
                            logger.error(f"Received error from server: {response_message.message.error}")
                            raise RuntimeError(f"MCP Error: {response_message.message.error.message}")

                raise TimeoutError("Did not receive a matching response from the server.")

        except Exception as e:
            logger.error(f"Failed to execute RFD on remote node {mcp_endpoint_url}: {e}")
            raise