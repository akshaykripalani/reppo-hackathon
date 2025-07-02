import pytest
import httpx
from unittest.mock import AsyncMock

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
    """Tests the successful execution of an RFD with a simple HTTP client."""
    # Arrange
    # Mock the response from the server
    mock_response = httpx.Response(
        200,
        json={"jsonrpc": "2.0", "result": {"status": "success", "data": "mock_data"}, "id": 1}
    )
    
    # Mock the AsyncClient's post method
    mock_post = AsyncMock(return_value=mock_response)
    mocker.patch("httpx.AsyncClient.post", mock_post)
    
    rfd = {"service": "test_service"}
    node_url = "http://test-node.com"

    # Act
    result = await mcp_client.execute_rfd(rfd, node_url)

    # Assert
    # Check that post was called correctly
    mock_post.assert_awaited_once()
    assert mock_post.call_args[0][0] == node_url
    assert mock_post.call_args[1]['json']['method'] == 'tools/call'
    
    # Check the result
    assert result == {"status": "success", "data": "mock_data"}

@pytest.mark.anyio
async def test_execute_rfd_http_error(mcp_client, mocker):
    """Tests that an HTTP error is handled correctly."""
    # Arrange
    mock_response = httpx.Response(500, text="Internal Server Error")
    mock_post = AsyncMock(return_value=mock_response)
    mocker.patch("httpx.AsyncClient.post", mock_post)

    # Act & Assert
    with pytest.raises(httpx.HTTPStatusError):
        await mcp_client.execute_rfd({}, "http://test-node.com")

@pytest.mark.anyio
async def test_execute_rfd_json_rpc_error(mcp_client, mocker):
    """Tests that a JSON-RPC error in the response body is handled."""
    # Arrange
    mock_response = httpx.Response(
        200,
        json={"jsonrpc": "2.0", "error": {"code": -32000, "message": "Server error"}, "id": 1}
    )
    mock_post = AsyncMock(return_value=mock_response)
    mocker.patch("httpx.AsyncClient.post", mock_post)

    # Act & Assert
    with pytest.raises(RuntimeError, match="MCP Error: Server error"):
        await mcp_client.execute_rfd({}, "http://test-node.com") 