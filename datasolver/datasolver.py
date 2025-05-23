"""Main data solver implementation."""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Type
from pathlib import Path

from .types import ProviderType
from .config import DatasetConfig
from .providers.provider import DataProvider
from .providers.mcp.tools.tool import MCPTool
from .providers.huggingface import HuggingFaceProvider
from .providers.mcp.client import MCPClient
from .providers.mock import MockProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DataSolver')

class DataSolver:
    """Data solver for generating datasets"""
    
    @classmethod
    def from_env(cls, config_file: str = "config.json", mock_mode: bool = False) -> "DataSolver":
        """Factory method to instantiate a DataSolver from environment variables and a JSON config file.
        
        Reads a JSON config file (if it exists) and then overrides with environment variables (for secrets and overrides).
        Environment variables take precedence.
        
        Args:
            config_file (str): Path to the JSON config file (default: "config.json")
            mock_mode (bool): Whether to run in mock mode (default: False)
        Returns:
            DataSolver: A fully configured DataSolver instance.
        """
        if mock_mode:
            return cls(provider_type=ProviderType.MOCK)
            
        config: Dict[str, Any] = {}
        if os.path.isfile(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
        else:
            logger.warning(f"Config file {config_file} not found; using defaults and environment variables.")
        
        # Override config with environment variables (for secrets and overrides)
        provider_type_env = os.getenv("PROVIDER_TYPE")
        if provider_type_env:
            config["provider_type"] = provider_type_env
        mcp_tools_env = os.getenv("MCP_TOOLS")
        if mcp_tools_env:
            # Assume MCP_TOOLS is a comma-separated list of fully qualified class names (e.g. "datasolver.providers.mcp.tools.dynamodb.DynamoDBTool")
            mcp_tool_names = mcp_tools_env.split(",")
            mcp_tools = []
            for tool_name in mcp_tool_names:
                try:
                    mod_name, cls_name = tool_name.rsplit(".", 1)
                    mod = __import__(mod_name, fromlist=[cls_name])
                    mcp_tools.append(getattr(mod, cls_name))
                except (ImportError, AttributeError) as e:
                    logger.warning(f"Could not import MCP tool {tool_name} (error: {e}). Skipping.")
            config["mcp_tools"] = mcp_tools
        # (Add other env overrides as needed, e.g. HUGGINGFACE_TOKEN, etc.)
        
        provider_type_str = config.get("provider_type", "huggingface")
        try:
            provider_type = ProviderType(provider_type_str)
        except ValueError as e:
            logger.warning(f"Invalid provider type {provider_type_str} (error: {e}). Defaulting to HUGGINGFACE.")
            provider_type = ProviderType.HUGGINGFACE
        mcp_tools = config.get("mcp_tools", [])
        return cls(provider_type=provider_type, mcp_tools=mcp_tools)

    def __init__(self, provider_type: ProviderType = ProviderType.HUGGINGFACE, mcp_tools: Optional[List[Type]] = None):
        """Initialize solver with provider type
        
        Args:
            provider_type: Type of provider to use
            mcp_tools: List of MCP tool classes to use (only for MCP provider)
        """
        if provider_type == ProviderType.MOCK:
            self.provider = MockProvider()
        elif provider_type == ProviderType.HUGGINGFACE:
            from .providers.huggingface import HuggingFaceProvider
            self.provider = HuggingFaceProvider()
        elif provider_type == ProviderType.MCP:
            from .providers.mcp.client import MCPClient
            self.provider = MCPClient(tools=mcp_tools)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
        logger.info(f"Initialized DataSolver with provider: {provider_type.value}")
    
    def solve(self, rfd: Dict) -> Optional[str]:
        """Generate dataset for RFD
        
        Args:
            rfd: Request for data
            
        Returns:
            Path to generated dataset file
        """
        try:
            dataset = self.provider.generate_dataset(rfd)
            if not dataset:
                return None
                
            file_path = f"data/rfd_{rfd.get('rfd_id', 'unknown')}_solution.json"
            os.makedirs("data", exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(dataset, f, indent=2)
            
            logger.info(f"Dataset generated successfully at: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to generate dataset: {e}")
            return None 