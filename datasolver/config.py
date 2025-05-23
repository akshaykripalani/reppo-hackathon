"""Configuration management for the data solver."""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv
from .types import ProviderType

# Load environment variables
load_dotenv()

@dataclass
class DatasetConfig:
    """Dataset generation configuration"""
    provider_type: ProviderType
    output_dir: str = "data"
    
    def __post_init__(self):
        """Ensure output directory exists"""
        os.makedirs(self.output_dir, exist_ok=True) 