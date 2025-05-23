"""MCP client implementation for data generation."""

import os
import logging
from typing import Dict, Any, Optional, List, Type
from pathlib import Path

from .provider import MCPProvider
from .tools.tool import MCPTool

logger = logging.getLogger('MCPClient')

class MCPClient(MCPProvider):
    """MCP client for data generation"""
    
    def __init__(self, tools: Optional[List[Type[MCPTool]]] = None):
        """Initialize MCP client
        
        Args:
            tools: List of MCP tool classes to register (optional)
        """
        super().__init__()
        self._tools = {}
        self._initialize_client(tools or [])
    
    def _initialize_client(self, tool_classes: List[Type[MCPTool]]):
        """Initialize MCP client with tools
        
        Args:
            tool_classes: List of MCP tool classes to register
        """
        try:
            # Import MCP SDK
            from mcp_sdk import MCPClient as SDKClient
            
            # Get server configuration from environment
            server_url = os.getenv("MCP_SERVER_URL")
            if not server_url:
                raise ValueError("MCP_SERVER_URL must be set in .env file")
                
            # Optional server configuration
            server_config = {
                "timeout": int(os.getenv("MCP_SERVER_TIMEOUT", "30")),
                "retries": int(os.getenv("MCP_SERVER_RETRIES", "3")),
                "api_key": os.getenv("MCP_SERVER_API_KEY"),
                "verify_ssl": os.getenv("MCP_SERVER_VERIFY_SSL", "true").lower() == "true"
            }
            
            # Initialize SDK client
            self.client = SDKClient(server_url, **server_config)
            
            # Register tools
            for tool_class in tool_classes:
                tool = tool_class()
                self._tools[tool.name] = tool
                self.client.register_tool(tool)
                logger.info(f"Registered MCP tool: {tool.name}")
            
            if not self._tools:
                logger.warning("No MCP tools registered")
            
        except ImportError:
            logger.error("MCP SDK not installed. Install with: pip install mcp-sdk")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            raise
    
    def register_tool(self, tool: MCPTool):
        """Register a new MCP tool
        
        Args:
            tool: MCP tool instance to register
        """
        self._tools[tool.name] = tool
        self.client.register_tool(tool)
        logger.info(f"Registered MCP tool: {tool.name}")
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get tool by name
        
        Args:
            tool_name: Name of tool to get
            
        Returns:
            Tool instance if found
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List available tools
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def generate_dataset(self, rfd: Dict) -> Dict[str, Any]:
        """Generate dataset using MCP tools
        
        Args:
            rfd: Request for data
            
        Returns:
            Generated dataset
        """
        try:
            # Get tool from RFD or use default
            tool_name = rfd.get("mcp_tool")
            if not tool_name:
                # Use first available tool if none specified
                tool_name = next(iter(self._tools)) if self._tools else None
                if not tool_name:
                    raise ValueError("No MCP tools available")
            
            tool = self.get_tool(tool_name)
            if not tool:
                raise ValueError(f"MCP tool not found: {tool_name}")
            
            # Validate RFD
            if not tool.validate_rfd(rfd):
                raise ValueError(f"RFD not compatible with {tool_name} tool")
            
            # Generate data
            records = tool.generate(rfd)
            return {"data": records}
            
        except Exception as e:
            logger.error(f"Failed to generate dataset: {e}")
            raise 