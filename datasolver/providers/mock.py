"""Mock provider implementation for testing."""

import random
import logging
from datetime import datetime
from typing import Dict, Any, List
from .provider import DataProvider

class MockProvider(DataProvider):
    """Mock data provider for testing and development.
    
    This provider generates synthetic data based on the RFD schema,
    useful for testing and development without external dependencies.
    """
    
    def __init__(self):
        super().__init__()
        self.logger.info("Initialized mock provider")
    
    def generate_dataset(self, rfd: Dict) -> Dict[str, Any]:
        """Generate mock dataset based on RFD schema.
        
        Args:
            rfd: Request for data containing schema
            
        Returns:
            Generated mock dataset
        """
        try:
            schema = rfd.get("schema", {})
            properties = schema.get("properties", {})
            num_records = rfd.get("num_records", 10)
            
            records = []
            for i in range(num_records):
                record = {}
                for field, field_schema in properties.items():
                    record[field] = self._generate_mock_value(field_schema, i)
                records.append(record)
            
            return {"data": records}
            
        except Exception as e:
            self.logger.error(f"Failed to generate mock dataset: {e}")
            raise
    
    def _generate_mock_value(self, field_schema: Dict[str, Any], index: int) -> Any:
        """Generate a mock value based on field schema.
        
        Args:
            field_schema: The schema for the field
            index: Record index
            
        Returns:
            Generated mock value
        """
        field_type = field_schema.get("type")
        
        if field_type == "string":
            if "format" in field_schema:
                if "date" in field_schema["format"]:
                    return f"2024-{index % 12 + 1:02d}-{index % 28 + 1:02d}"
                elif "email" in field_schema["format"]:
                    return f"user_{index}@example.com"
                elif "uri" in field_schema["format"]:
                    return f"https://example.com/resource/{index}"
            return f"mock_value_{index}"
            
        elif field_type == "number":
            return float(random.randint(1, 1000)) / 10
            
        elif field_type == "integer":
            return random.randint(1, 100)
            
        elif field_type == "boolean":
            return random.choice([True, False])
            
        elif field_type == "array":
            item_schema = field_schema.get("items", {"type": "string"})
            return [self._generate_mock_value(item_schema, i) for i in range(3)]
            
        elif field_type == "object":
            properties = field_schema.get("properties", {})
            return {
                key: self._generate_mock_value(schema, index)
                for key, schema in properties.items()
            }
            
        return None 