import json
from pathlib import Path
from datasolver.router import Router

def test_router_load_success(tmp_path: Path):
    """Tests that the router successfully loads a valid registry file."""
    registry_content = {"service1": "http://node1.com"}
    registry_file = tmp_path / "nodes.json"
    registry_file.write_text(json.dumps(registry_content))
    
    router = Router(registry_path=registry_file)
    assert router._node_registry == registry_content

def test_router_file_not_found(caplog):
    """Tests that the router handles a missing registry file gracefully."""
    router = Router(registry_path=Path("non_existent_file.json"))
    assert router._node_registry == {}
    assert "Node registry file not found" in caplog.text

def test_router_malformed_json(tmp_path: Path, caplog):
    """Tests that the router handles a malformed JSON file."""
    registry_file = tmp_path / "nodes.json"
    registry_file.write_text("{'invalid_json': 'test'")
    
    router = Router(registry_path=registry_file)
    assert router._node_registry == {}
    assert "Failed to decode JSON" in caplog.text

def test_get_node_url_success(tmp_path: Path):
    """Tests retrieving a URL for a known service."""
    registry_content = {"service1": "http://node1.com", "service2": "http://node2.com"}
    registry_file = tmp_path / "nodes.json"
    registry_file.write_text(json.dumps(registry_content))
    
    router = Router(registry_path=registry_file)
    assert router.get_node_url("service1") == "http://node1.com"

def test_get_node_url_not_found(tmp_path: Path, caplog):
    """Tests retrieving a URL for an unknown service."""
    registry_content = {"service1": "http://node1.com"}
    registry_file = tmp_path / "nodes.json"
    registry_file.write_text(json.dumps(registry_content))
    
    router = Router(registry_path=registry_file)
    assert router.get_node_url("unknown_service") is None
    assert "No node found in registry for service: unknown_service" in caplog.text 