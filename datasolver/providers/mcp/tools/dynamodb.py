"""DynamoDB tool for MCP data generation."""

import boto3
from typing import Dict, Any, List, Optional
from .tool import MCPTool

class DynamoDBTool(MCPTool):
    """MCP tool for DynamoDB operations"""
    
    def __init__(self):
        super().__init__(
            name="dynamodb_tool",
            description="Query and generate DynamoDB data"
        )
        self.ddb = boto3.resource('dynamodb')
        self.client = boto3.client('dynamodb')
    
    def generate(self, rfd: Dict, **kwargs) -> List[Dict[str, Any]]:
        """Query or generate DynamoDB data based on RFD
        
        Args:
            rfd: The RFD containing query/generation requirements
            **kwargs: Additional arguments
            
        Returns:
            List of DynamoDB records
        """
        # Check if this is a query request
        if self._is_query_request(rfd):
            return self._query_table(rfd)
        else:
            return self._generate_data(rfd, **kwargs)
    
    def validate_rfd(self, rfd: Dict) -> bool:
        """Validate if this tool can handle the RFD
        
        Args:
            rfd: The RFD to validate
            
        Returns:
            True if the tool can handle the RFD
        """
        # For query requests
        if self._is_query_request(rfd):
            return self._validate_query_rfd(rfd)
        # For generation requests
        else:
            return self._validate_generation_rfd(rfd)
    
    def _is_query_request(self, rfd: Dict) -> bool:
        """Check if RFD is a query request
        
        Args:
            rfd: The RFD to check
            
        Returns:
            True if RFD is a query request
        """
        return "query" in rfd and "table_name" in rfd["query"]
    
    def _validate_query_rfd(self, rfd: Dict) -> bool:
        """Validate query RFD
        
        Args:
            rfd: The RFD to validate
            
        Returns:
            True if query RFD is valid
        """
        query = rfd.get("query", {})
        required = {"table_name", "key_condition"}
        return all(field in query for field in required)
    
    def _validate_generation_rfd(self, rfd: Dict) -> bool:
        """Validate generation RFD
        
        Args:
            rfd: The RFD to validate
            
        Returns:
            True if generation RFD is valid
        """
        schema = rfd.get("schema", {})
        properties = schema.get("properties", {})
        valid_types = {"string", "number", "binary", "boolean", "null", "list", "map"}
        return all(
            field_schema.get("type") in valid_types
            for field_schema in properties.values()
        )
    
    def _query_table(self, rfd: Dict) -> List[Dict[str, Any]]:
        """Query DynamoDB table based on RFD
        
        Args:
            rfd: The RFD containing query parameters
            
        Returns:
            List of matching records
        """
        query = rfd["query"]
        table = self.ddb.Table(query["table_name"])
        
        # Build query parameters
        params = {
            "KeyConditionExpression": query["key_condition"]
        }
        
        # Add filter expression if provided
        if "filter_expression" in query:
            params["FilterExpression"] = query["filter_expression"]
        
        # Add expression attribute values
        if "expression_values" in query:
            params["ExpressionAttributeValues"] = query["expression_values"]
        
        # Add projection expression if provided
        if "projection" in query:
            params["ProjectionExpression"] = query["projection"]
        
        # Execute query
        try:
            response = table.query(**params)
            return response.get("Items", [])
        except Exception as e:
            self.logger.error(f"Failed to query table: {e}")
            raise
    
    def _generate_data(self, rfd: Dict, **kwargs) -> List[Dict[str, Any]]:
        """Generate DynamoDB-compatible data
        
        Args:
            rfd: The RFD containing schema
            **kwargs: Additional arguments
            
        Returns:
            List of generated records
        """
        num_records = kwargs.get("num_records", 100)
        schema = rfd.get("schema", {})
        properties = schema.get("properties", {})
        
        records = []
        for i in range(num_records):
            record = {}
            for field, field_schema in properties.items():
                record[field] = self._generate_dynamodb_value(field_schema, i)
            records.append(record)
        
        return records
    
    def _get_capabilities(self) -> Dict[str, Any]:
        """Get the tool's capabilities
        
        Returns:
            Dict describing what the tool can do
        """
        return {
            "operations": [
                "query",
                "generate"
            ],
            "query_features": [
                "Key condition expressions",
                "Filter expressions",
                "Projection expressions",
                "Expression attribute values"
            ],
            "generation_features": [
                "DynamoDB-compatible data generation",
                "Schema validation",
                "Primary key generation"
            ],
            "constraints": {
                "max_item_size": 400 * 1024,
                "max_string_length": 1024
            }
        }
    
    def _generate_dynamodb_value(self, field_schema: Dict[str, Any], index: int) -> Any:
        """Generate a DynamoDB-compatible value
        
        Args:
            field_schema: The schema for the field
            index: Record index
            
        Returns:
            DynamoDB-compatible value
        """
        field_type = field_schema.get("type")
        
        if field_type == "string":
            if "format" in field_schema and "date" in field_schema["format"]:
                return f"2024-{index % 12 + 1:02d}-{index % 28 + 1:02d}"
            return f"value_{index}"
            
        elif field_type == "number":
            return float(index)
            
        elif field_type == "boolean":
            return index % 2 == 0
            
        elif field_type == "null":
            return None
            
        elif field_type == "list":
            return [self._generate_dynamodb_value({"type": "string"}, i) 
                   for i in range(3)]
            
        elif field_type == "map":
            return {
                "key1": self._generate_dynamodb_value({"type": "string"}, index),
                "key2": self._generate_dynamodb_value({"type": "number"}, index)
            }
            
        return None 