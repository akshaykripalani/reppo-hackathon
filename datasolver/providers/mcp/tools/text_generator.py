"""Text generation tool for MCP data generation."""

from typing import Dict, Any, List
from .tool import MCPTool

class TextGeneratorTool(MCPTool):
    """MCP tool for generating text data"""
    
    def __init__(self):
        super().__init__(
            name="text_generator",
            description="Generates text data based on templates and patterns"
        )
    
    def generate(self, rfd: Dict, **kwargs) -> List[Dict[str, Any]]:
        """Generate text data based on RFD schema
        
        Args:
            rfd: The RFD containing schema and requirements
            **kwargs: Additional arguments including num_records
            
        Returns:
            List of generated text records
        """
        num_records = kwargs.get("num_records", 100)
        schema = rfd.get("schema", {})
        properties = schema.get("properties", {})
        
        records = []
        for _ in range(num_records):
            record = {}
            for field, field_schema in properties.items():
                if field_schema.get("type") == "string":
                    # Generate text based on field requirements
                    record[field] = self._generate_text(field_schema)
                else:
                    # For non-string fields, use default values
                    record[field] = self._get_default_value(field_schema)
            records.append(record)
        
        return records
    
    def validate_rfd(self, rfd: Dict) -> bool:
        """Validate if this tool can handle the RFD
        
        Args:
            rfd: The RFD to validate
            
        Returns:
            True if the tool can handle the RFD, False otherwise
        """
        schema = rfd.get("schema", {})
        properties = schema.get("properties", {})
        
        # Check if schema has any string fields
        return any(
            field_schema.get("type") == "string"
            for field_schema in properties.values()
        )
    
    def _get_capabilities(self) -> Dict[str, Any]:
        """Get the tool's capabilities
        
        Returns:
            Dict describing what the tool can do
        """
        return {
            "supported_types": ["string"],
            "features": [
                "template-based generation",
                "pattern matching",
                "context-aware generation"
            ],
            "constraints": {
                "max_length": 1000,
                "min_length": 1
            }
        }
    
    def _generate_text(self, field_schema: Dict[str, Any]) -> str:
        """Generate text for a field based on its schema
        
        Args:
            field_schema: The schema for the field
            
        Returns:
            Generated text value
        """
        # Implement text generation logic based on field schema
        # This could use templates, patterns, or other generation methods
        return f"Generated text for {field_schema.get('description', 'field')}"
    
    def _get_default_value(self, field_schema: Dict[str, Any]) -> Any:
        """Get a default value for a non-string field
        
        Args:
            field_schema: The schema for the field
            
        Returns:
            Default value based on field type
        """
        field_type = field_schema.get("type")
        if field_type == "number":
            return 0.0
        elif field_type == "integer":
            return 0
        elif field_type == "boolean":
            return False
        elif field_type == "string" and "date" in field_schema.get("format", ""):
            return "2024-01-01"
        return None 