"""Abstract base class for data providers."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

class DataProvider(ABC):
    """Abstract base class defining the interface for data providers.
    
    All data providers (HuggingFace, MCP, etc.) must implement this interface
    to ensure consistent dataset generation behavior.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def generate_dataset(self, rfd: Dict) -> Dict[str, Any]:
        """Generate a dataset based on the RFD requirements.
        
        Args:
            rfd: Request for data containing schema and requirements
            
        Returns:
            Generated dataset as a dictionary
        """
        pass 