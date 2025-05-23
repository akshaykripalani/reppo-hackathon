from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import logging
from enum import Enum
import random
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Pipeline')

# Load environment variables
load_dotenv()

class PipelineStageType(Enum):
    """Pipeline processing stages"""
    INITIALIZATION = "initialization"
    VALIDATION = "validation"
    DATA_GENERATION = "data_generation"
    STORAGE = "storage"
    SUBMISSION = "submission"

@dataclass
class PipelineContext:
    """Context object passed through the pipeline stages"""
    rfd: Dict[str, Any]
    stage_results: Dict[PipelineStageType, Any] = None
    errors: List[str] = None
    
    def __post_init__(self):
        self.stage_results = {}
        self.errors = []
    
    def add_stage_result(self, stage: PipelineStageType, result: Any):
        """Add a result from a pipeline stage"""
        self.stage_results[stage] = result
    
    def get_stage_result(self, stage: PipelineStageType) -> Optional[Any]:
        """Get a result from a pipeline stage"""
        return self.stage_results.get(stage)
    
    def add_error(self, error: str):
        """Add an error to the context"""
        self.errors.append(error)

class PipelineStage(ABC):
    """Abstract base class for pipeline stages"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"
        self.test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    
    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext:
        """Process the pipeline stage
        
        Args:
            context: The pipeline context containing RFD and stage results
            
        Returns:
            Updated pipeline context
        """
        pass
    
    @abstractmethod
    def validate(self, context: PipelineContext) -> bool:
        """Validate if the stage can process the context
        
        Args:
            context: The pipeline context to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass

class ValidationStage(PipelineStage):
    """Validates RFD and configuration"""
    
    def validate(self, context: PipelineContext) -> bool:
        required_fields = ["rfd_id", "name", "description", "schema"]
        return all(field in context.rfd for field in required_fields)
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.validate(context):
            context.add_error("Invalid RFD format")
            return context
            
        # Add validation logic here
        context.add_stage_result(PipelineStageType.VALIDATION, {"valid": True})
        return context

class DataGenerationStage(PipelineStage):
    """Generates dataset based on RFD requirements"""
    
    def __init__(self, provider: Any):
        super().__init__()
        self.provider = provider
    
    def validate(self, context: PipelineContext) -> bool:
        return (
            context.get_stage_result(PipelineStageType.VALIDATION) is not None
            and (self.provider is not None or self.mock_mode)
        )
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.validate(context):
            context.add_error("Cannot generate data: Invalid context or provider")
            return context
            
        try:
            if self.mock_mode:
                # Generate mock dataset
                mock_data = {
                    "data": [
                        {
                            "mock_field_1": f"mock_value_{i}",
                            "mock_field_2": random.randint(1, 100),
                            "mock_field_3": random.choice([True, False]),
                            "mock_field_4": datetime.now().strftime("%Y-%m-%d")
                        }
                        for i in range(10)  # Generate 10 mock records
                    ]
                }
                self.logger.info("Generated mock dataset")
                context.add_stage_result(PipelineStageType.DATA_GENERATION, mock_data)
            else:
                dataset = self.provider.generate_dataset(context.rfd)
                context.add_stage_result(PipelineStageType.DATA_GENERATION, dataset)
        except Exception as e:
            context.add_error(f"Data generation failed: {str(e)}")
            
        return context

class StorageStage(PipelineStage):
    """Handles dataset storage (e.g., IPFS upload)"""
    
    def validate(self, context: PipelineContext) -> bool:
        return context.get_stage_result(PipelineStageType.DATA_GENERATION) is not None
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.validate(context):
            context.add_error("Cannot store data: No dataset generated")
            return context
            
        try:
            # In mock mode, just generate a mock URI without checking credentials
            if self.mock_mode:
                rfd_id = context.rfd.get("rfd_id", "unknown")
                mock_cid = f"mockCID_{rfd_id}_{int(time.time())}"
                storage_uri = f"ipfs://{mock_cid}"
                self.logger.info(f"Generated mock IPFS URI: {storage_uri}")
                context.add_stage_result(PipelineStageType.STORAGE, {"uri": storage_uri})
                return context

            # Only check credentials and perform actual storage in non-mock mode
            pinata_api_key = os.getenv("PINATA_API_KEY")
            pinata_secret = os.getenv("PINATA_SECRET_API_KEY")
            if not pinata_api_key or not pinata_secret:
                raise ValueError("Pinata credentials not found in environment variables")
            
            # Add actual IPFS upload logic here
            storage_uri = "ipfs://mock_cid"  # Placeholder
            context.add_stage_result(PipelineStageType.STORAGE, {"uri": storage_uri})
            
        except Exception as e:
            context.add_error(f"Storage failed: {str(e)}")
            
        return context

class SubmissionStage(PipelineStage):
    """Handles solution submission to blockchain"""
    
    def validate(self, context: PipelineContext) -> bool:
        storage_result = context.get_stage_result(PipelineStageType.STORAGE)
        return storage_result is not None and "uri" in storage_result
    
    def process(self, context: PipelineContext) -> PipelineContext:
        if not self.validate(context):
            context.add_error("Cannot submit solution: No storage URI")
            return context
            
        try:
            if self.mock_mode:
                # Generate mock transaction hash
                rfd_id = context.rfd.get("rfd_id", "unknown")
                mock_tx = f"0x{'0' * 40}_{rfd_id}_{int(time.time())}"
                self.logger.info(f"Generated mock transaction hash: {mock_tx}")
                context.add_stage_result(PipelineStageType.SUBMISSION, {"tx_hash": mock_tx})
            else:
                # Get blockchain credentials from environment
                wallet_address = os.getenv("WALLET_ADDRESS")
                private_key = os.getenv("PRIVATE_KEY")
                web3_rpc_url = os.getenv("WEB3_RPC_URL")
                if not all([wallet_address, private_key, web3_rpc_url]):
                    raise ValueError("Blockchain credentials not found in environment variables")
                
                # Add actual submission logic here
                tx_hash = "0xmock_tx_hash"  # Placeholder
                context.add_stage_result(PipelineStageType.SUBMISSION, {"tx_hash": tx_hash})
        except Exception as e:
            context.add_error(f"Submission failed: {str(e)}")
            
        return context

class Pipeline:
    """Orchestrates the data processing pipeline"""
    
    def __init__(self, stages: List[PipelineStage]):
        self.stages = stages
        self.logger = logging.getLogger('Pipeline')
    
    def process(self, context: PipelineContext) -> PipelineContext:
        """Process an RFD through the pipeline stages
        
        Args:
            context: The pipeline context containing RFD
            
        Returns:
            Pipeline context containing results and any errors
        """
        for stage in self.stages:
            self.logger.info(f"Processing stage: {stage.__class__.__name__}")
            context = stage.process(context)
            
            if context.errors:
                self.logger.error(f"Pipeline failed: {context.errors[-1]}")
                break
                
        return context 