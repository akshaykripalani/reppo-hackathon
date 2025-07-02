"""
Service Router for finding the correct data node for a given RFD.
"""

import json
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class Router:
    """
    Reads a service registry and routes RFDs to the correct data node.
    """
    
    def __init__(self, registry_path: Path = Path("nodes.json")):
        """
        Initializes the Router and loads the node registry.
        
        Args:
            registry_path: The path to the node registry JSON file.
        """
        self.registry_path = registry_path
        self._node_registry = self._load_registry()

    def _load_registry(self) -> Dict[str, str]:
        """Loads the node registry from the specified JSON file."""
        try:
            with open(self.registry_path, 'r') as f:
                registry = json.load(f)
                logger.info(f"Successfully loaded node registry from {self.registry_path}")
                return registry
        except FileNotFoundError:
            logger.error(f"Node registry file not found at: {self.registry_path}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from node registry: {self.registry_path}")
            return {}

    def get_node_url(self, service: str) -> Optional[str]:
        """
        Gets the URL for the node that provides the specified service.
        
        Args:
            service: The name of the service (e.g., 'nba_player_stats').
            
        Returns:
            The URL of the data node, or None if the service is not found.
        """
        node_url = self._node_registry.get(service)
        if not node_url:
            logger.warning(f"No node found in registry for service: {service}")
        return node_url 