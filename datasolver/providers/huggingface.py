"""HuggingFace provider implementation for text generation."""

import os
import logging
from typing import Dict, Any, List
from .provider import DataProvider

try:
    from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
except ImportError:
    logging.warning("HuggingFace transformers not installed. Install with: pip install transformers")

class HuggingFaceProvider(DataProvider):
    """HuggingFace provider for text generation.
    
    This provider uses HuggingFace models to generate text data based on
    the RFD schema and requirements.
    """
    
    def __init__(self):
        super().__init__()
        self.token = os.getenv("HUGGINGFACE_TOKEN")
        self.model = os.getenv("HUGGINGFACE_MODEL", "gpt2")
        self._generator = None
        self._initialize_generator()
    
    def _initialize_generator(self):
        """Initialize the text generation pipeline."""
        try:
            if not self.token:
                self.logger.warning("HUGGINGFACE_TOKEN not set. Using model without authentication.")
            
            # Initialize model and tokenizer
            model = AutoModelForCausalLM.from_pretrained(
                self.model,
                token=self.token,
                trust_remote_code=True
            )
            tokenizer = AutoTokenizer.from_pretrained(
                self.model,
                token=self.token,
                trust_remote_code=True
            )
            
            # Create text generation pipeline
            self._generator = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device="cpu"  # Use CPU for testing
            )
            
            self.logger.info(f"Initialized HuggingFace provider with model: {self.model}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize HuggingFace provider: {e}")
            raise
    
    def generate_dataset(self, rfd: Dict) -> Dict[str, Any]:
        """Generate text dataset using HuggingFace model.
        
        Args:
            rfd: Request for data containing schema and requirements
            
        Returns:
            Generated text dataset
        """
        try:
            if not self._generator:
                raise RuntimeError("HuggingFace generator not initialized")
            
            schema = rfd.get("schema", {})
            properties = schema.get("properties", {})
            num_records = rfd.get("num_records", 3)
            
            records = []
            for _ in range(num_records):
                record = {}
                for field, field_schema in properties.items():
                    if field_schema.get("type") == "string":
                        # Generate text based on field description
                        prompt = field_schema.get("description", f"Generate {field}")
                        generated = self._generator(
                            prompt,
                            max_length=100,
                            num_return_sequences=1,
                            temperature=0.7
                        )
                        record[field] = generated[0]["generated_text"].strip()
                    else:
                        # For non-string fields, use default values
                        record[field] = self._get_default_value(field_schema)
                records.append(record)
            
            return {"data": records}
            
        except Exception as e:
            self.logger.error(f"Failed to generate dataset: {e}")
            raise
    
    def _get_default_value(self, field_schema: Dict[str, Any]) -> Any:
        """Get a default value for a non-string field.
        
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