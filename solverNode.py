# solverNode.py
import os
from dotenv import load_dotenv
from rfdListener import RFDListener
from datasolver import DataSolver
from ipfsUploader import upload_to_ipfs
from nftAuthorizer import NFTAuthorizer
from submitSolution import SolutionSubmitter
from typing import Dict, Optional, List, Type
import json
import random
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class SolverNode:
    def __init__(self, test_mode: bool = False, mock_mode: bool = False, mcp_tools: Optional[List[Type]] = None):
        """Initialize the solver node
        
        Args:
            test_mode: Run in test mode (uses real data generation)
            mock_mode: Run in mock mode (uses mock data and responses)
            mcp_tools: List of MCP tool classes to use (optional, e.g. [DynamoDBTool])
        """
        self.logger = logging.getLogger('SolverNode')
        self.test_mode = test_mode
        self.mock_mode = mock_mode
        # MCP tools should be passed in by the user or config if needed
        self.mcp_tools = mcp_tools
        # Load environment variables
        load_dotenv()
        # Initialize components based on mode
        self._initialize_components()
        # Print mode information
        self._print_mode_info()
    
    def _initialize_components(self):
        """Initialize node components based on mode"""
        # Set wallet address
        if self.mock_mode:
            self.wallet_address = "0xMockWalletAddress"
        else:
            self.wallet_address = os.getenv("WALLET_ADDRESS")
            if not self.wallet_address:
                raise ValueError("WALLET_ADDRESS must be set in .env file")
        
        # Initialize solver with appropriate configuration
        self.solver = DataSolver.from_env(mock_mode=self.mock_mode)
        
        # Initialize other components based on mode
        if self.test_mode or self.mock_mode:
            self.authorizer = None
            self.submitter = None
            self.listener = None
        else:
            self.authorizer = NFTAuthorizer()
            self.submitter = SolutionSubmitter()
            self.listener = RFDListener()
    
    def _print_mode_info(self):
        """Print information about the current mode"""
        if self.mock_mode:
            print("\nRunning in MOCK mode:")
            print("- Using mock data generation")
            print("- Using mock blockchain responses")
            print("- No external services required")
            print(f"- Using mock wallet: {self.wallet_address}")
        elif self.test_mode:
            print("\nRunning in TEST mode:")
            print("- Processing sample RFD file")
            print("- Using real data generation (if available)")
            print("- Skipping blockchain interactions")
            print(f"- Using wallet: {self.wallet_address}")
        else:
            print("\nRunning in PRODUCTION mode:")
            print("- Using real data generation")
            print("- Using real blockchain interactions")
            print("- Requires Reppo NFT ownership")
            print(f"- Using wallet: {self.wallet_address}")
    
    def process_rfd(self, rfd: Dict) -> Optional[Dict]:
        """Process an RFD and generate a solution
        
        Args:
            rfd: The RFD to process
            
        Returns:
            Optional[Dict]: Processing results if successful, None otherwise
        """
        rfd_id = rfd.get("rfd_id", "unknown")
        self.logger.info(f"Processing RFD #{rfd_id} with wallet {self.wallet_address}")
        
        # Skip NFT check in test/mock modes
        if self.authorizer and not self.authorizer.has_nft(self.wallet_address):
            self.logger.warning(f"Wallet {self.wallet_address} does not own a Reppo NFT. Skipping RFD #{rfd_id}")
            return None
        
        try:
            # Generate dataset
            dataset_path = self.solver.solve(rfd)
            if not dataset_path:
                self.logger.error(f"Failed to generate dataset for RFD #{rfd_id}")
                return None
            
            # In mock mode, generate mock storage and transaction info
            if self.mock_mode:
                mock_cid = f"mockCID_{rfd_id}_{int(time.time())}"
                mock_tx = f"0x{'0' * 40}_{rfd_id}_{int(time.time())}"
                results = {
                    "rfd_id": rfd_id,
                    "wallet": self.wallet_address,
                    "dataset_path": dataset_path,
                    "storage_uri": f"ipfs://{mock_cid}",
                    "tx_hash": mock_tx
                }
            else:
                # Upload to IPFS
                storage_uri = upload_to_ipfs(dataset_path)
                if not storage_uri:
                    self.logger.error(f"Failed to upload dataset for RFD #{rfd_id}")
                    return None
                
                # Submit solution
                tx_hash = self.submitter.submit_solution(rfd_id, storage_uri)
                if not tx_hash:
                    self.logger.error(f"Failed to submit solution for RFD #{rfd_id}")
                    return None
                
                results = {
                    "rfd_id": rfd_id,
                    "wallet": self.wallet_address,
                    "dataset_path": dataset_path,
                    "storage_uri": storage_uri,
                    "tx_hash": tx_hash
                }
            
            self.logger.info(f"Successfully processed RFD #{rfd_id}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing RFD #{rfd_id}: {str(e)}")
            return None
    
    def run(self):
        """Run the Solver Node"""
        if self.mock_mode or self.test_mode:
            self._run_test_mode()
        else:
            self._run_production_mode()
    
    def _run_test_mode(self):
        """Run in test/mock mode"""
        print("\nProcessing sample RFD...")
        try:
            with open("sample_rfd.json") as f:
                sample_rfd = json.load(f)
            results = self.process_rfd(sample_rfd)
            if results:
                print(f"Successfully processed sample RFD: {results}")
            else:
                print("Failed to process sample RFD")
        except FileNotFoundError:
            print("Error: sample_rfd.json not found. Please create a sample RFD file.")
        except Exception as e:
            print(f"Error processing sample RFD: {str(e)}")
    
    def _run_production_mode(self):
        """Run in production mode"""
        if not self.authorizer:
            raise RuntimeError("Cannot run in production mode without authorizer")
        
        print("Production mode: Starting RFD listener")
        self.listener.listen_for_rfds(self.process_rfd)