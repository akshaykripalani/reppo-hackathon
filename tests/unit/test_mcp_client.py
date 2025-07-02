import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
from contextlib import asynccontextmanager

# Since MCPClient is now in a provider subdirectory, we adjust the import path
from datasolver.providers.mcp.client import MCPClient
from mcp.shared.message import SessionMessage
import mcp.types as types

@pytest.fixture
def mcp_client():
    """Provides a fresh MCPClient instance for each test."""
    return MCPClient()

@pytest.mark.anyio
async def test_execute_rfd_success(mcp_client, mocker):
    """Tests the successful execution of an RFD by mocking the streamablehttp_client."""
    # Arrange
    mock_read_stream = MagicMock()
    # The client now expects two responses: one for 'initialize' and one for 'tools/call'
    mock_read_stream.__aiter__.return_value = [
        SessionMessage(
            message=types.JSONRPCResponse(jsonrpc="2.0", result={"protocolVersion": "1.0"}, id=0)
        ),
        SessionMessage(
            message=types.JSONRPCResponse(
                jsonrpc="2.0",
                result={"status": "success", "data": "mock_data"},
                id=1
            )
        )
    ]
    
    mock_write_stream = AsyncMock()

    @asynccontextmanager
    async def mock_client_context_manager(*args, **kwargs):
        yield mock_read_stream, mock_write_stream, (lambda: "session-123")

    mocker.patch("datasolver.providers.mcp.client.streamablehttp_client", side_effect=mock_client_context_manager)

    rfd = {"service": "test_service"}
    node_url = "http://test-node.com"

    # Act
    result = await mcp_client.execute_rfd(rfd, node_url)

    # Assert
    assert result == {"status": "success", "data": "mock_data"}
    # Check that both initialize and tools/call were sent
    assert mock_write_stream.send.call_count == 2

@pytest.mark.anyio
async def test_execute_rfd_error_response(mcp_client, mocker):
    """Tests handling of a JSONRPCError from the server."""
    # Arrange
    mock_read_stream = MagicMock()
    error_obj = types.ErrorData(code=-32000, message="Server error")
    # Provide a successful init response, then an error for the tool call
    mock_read_stream.__aiter__.return_value = [
        SessionMessage(
            message=types.JSONRPCResponse(jsonrpc="2.0", result={"protocolVersion": "1.0"}, id=0)
        ),
        SessionMessage(
            message=types.JSONRPCError(jsonrpc="2.0", error=error_obj, id=1)
        )
    ]
    mock_write_stream = AsyncMock()
    
    @asynccontextmanager
    async def mock_client_context_manager(*args, **kwargs):
        yield mock_read_stream, mock_write_stream, (lambda: "session-123")

    mocker.patch("datasolver.providers.mcp.client.streamablehttp_client", side_effect=mock_client_context_manager)

    # Act & Assert
    with pytest.raises(RuntimeError, match="MCP Error: Server error"):
        await mcp_client.execute_rfd({}, "http://test-node.com")