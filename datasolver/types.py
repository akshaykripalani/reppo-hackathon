"""Type definitions for the data solver package."""

from enum import Enum

class ProviderType(Enum):
    """Data provider types supported by the solver"""
    MOCK = "mock"                # Mock data generation for testing
    HUGGINGFACE = "huggingface"  # HuggingFace model-based generation
    MCP = "mcp"                  # MCP tool-based generation 