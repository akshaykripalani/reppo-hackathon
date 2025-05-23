"""Base class for MCP tools that handle specific data operations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json

class MCPTool(ABC):
    """Abstract base class for MCP tools.
    
    This class defines the interface that all MCP tools must implement.
    Tools are responsible for specific data operations like querying databases,
    generating synthetic data, or transforming data according to RFD requirements.
    
    Each tool must:
    1. Define its capabilities and requirements
    2. Validate incoming RFDs
    3. Generate or retrieve data according to the RFD
    4. Handle errors and edge cases
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the tool's unique identifier.
        
        Returns:
            A string identifier for the tool (e.g., 'dynamodb', 'synthetic')
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get a human-readable description of the tool.
        
        Returns:
            A string describing what the tool does and its capabilities
        """
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> Dict[str, Any]:
        """Get the tool's capabilities and requirements.
        
        Returns:
            A dictionary describing what the tool can do and what it needs
            to function (e.g., required parameters, supported data types)
        """
        pass
    
    @abstractmethod
    def validate_rfd(self, rfd: Dict[str, Any]) -> bool:
        """Validate if the tool can handle the given RFD.
        
        Args:
            rfd: The request for data to validate
            
        Returns:
            True if the tool can handle this RFD, False otherwise
        """
        pass
    
    @abstractmethod
    def generate_data(self, rfd: Dict[str, Any]) -> Dict[str, Any]:
        """Generate or retrieve data according to the RFD.
        
        Args:
            rfd: The request for data specifying what to generate
            
        Returns:
            A dictionary containing the generated dataset
            
        Raises:
            ValueError: If the RFD is invalid or requirements can't be met
            RuntimeError: If data generation fails
        """
        pass 