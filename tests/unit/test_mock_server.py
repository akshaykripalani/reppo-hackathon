from mock_mcp_server import process_rfd

def test_process_rfd_success():
    """
    Tests that the mock server's tool returns correct data for a valid RFD.
    """
    rfd = {
      "rfd_id": "nba_001",
      "service": "nba_player_stats",
      "metrics": ["points", "rebounds"],
      "season": "2023-24"
    }
    
    result = process_rfd(rfd)
    
    assert result["status"] == "success"
    assert len(result["data"]) == 3
    assert result["data"][0]["player"] == "LeBron James"
    assert result["data"][0]["season"] == "2023-24"
    assert "points" in result["data"][0]["stats"]
    assert "rebounds" in result["data"][0]["stats"]

def test_process_rfd_unsupported_service():
    """
    Tests that the tool returns an error for an unsupported service.
    """
    rfd = {
      "rfd_id": "other_001",
      "service": "unsupported_service"
    }
    
    result = process_rfd(rfd)
    
    assert "error" in result
    assert result["error"] == "Service not supported" 