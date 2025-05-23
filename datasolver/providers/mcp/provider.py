"""MCP provider implementation for the data solver."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ..provider import DataProvider
import os

class MCPProvider(DataProvider):
    """Base class for MCP-based data providers.
    
    This class provides common functionality for MCP providers, including
    server configuration and tool management. Specific MCP implementations
    (like MCPClient) should extend this class.
    """
    
    def __init__(self):
        super().__init__()
        self.server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
        self.logger.info(f"Initialized MCP provider with server: {self.server_url}")
    
    @abstractmethod
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get an MCP tool by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            The tool instance if found, None otherwise
        """
        pass
    
    @abstractmethod
    def list_tools(self) -> List[str]:
        """List all available MCP tools.
        
        Returns:
            List of tool names that are currently registered
        """
        pass 