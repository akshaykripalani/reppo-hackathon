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
                
                # Use a dictionary to track outstanding requests
                pending_requests = {}

                # Create and send initialize request
                init_id = 0
                init_request = types.JSONRPCRequest(
                    jsonrpc="2.0", method="initialize",
                    params={"protocolVersion": "1.0"}, id=init_id
                )
                init_event = asyncio.Event()
                pending_requests[init_id] = init_event
                await write_stream.send(SessionMessage(message=types.JSONRPCMessage(root=init_request)))

                # Create and send tool call request
                tool_id = 1
                tool_request = types.JSONRPCRequest(
                    jsonrpc="2.0", method="tools/call",
                    params={"name": "process_rfd", "arguments": rfd}, id=tool_id
                )
                tool_event = asyncio.Event()
                pending_requests[tool_id] = tool_event
                await write_stream.send(SessionMessage(message=types.JSONRPCMessage(root=tool_request)))
                
                # Single loop to process all incoming messages
                tool_call_result = None
                async for response_message in read_stream:
                    msg_id = getattr(response_message.message, 'id', None)
                    if msg_id in pending_requests:
                        if isinstance(response_message.message, types.JSONRPCResponse):
                            if msg_id == init_id:
                                logger.info("Session initialized successfully.")
                                pending_requests.pop(init_id).set()
                            elif msg_id == tool_id:
                                logger.info(f"Received tool call response from {mcp_endpoint_url}")
                                tool_call_result = response_message.message.result
                                pending_requests.pop(tool_id).set()
                        
                        elif isinstance(response_message.message, types.JSONRPCError):
                            error_msg = response_message.message.error.message
                            logger.error(f"Received error from server: {error_msg}")
                            raise RuntimeError(f"MCP Error: {error_msg}")
                    
                    # If all tracked requests are done, we can exit
                    if not pending_requests:
                        break

                # Wait for events to be set, with a timeout
                await asyncio.wait_for(asyncio.gather(*[event.wait() for event in pending_requests.values()]), timeout=self.timeout)

                if tool_call_result is not None:
                    return tool_call_result

                raise TimeoutError("Did not receive a matching response for the tool call from the server.")

        except Exception as e:
            logger.error(f"Failed to execute RFD on remote node {mcp_endpoint_url}: {e}")
            raise