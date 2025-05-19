# solverNode.py
import os
from dotenv import load_dotenv
from rfdListener import RFDListener
from dataSolver import DataSolver, DatasetConfig, ProviderType
from ipfsUploader import upload_to_ipfs
from nftAuthorizer import NFTAuthorizer
from submitSolution import SolutionSubmitter
from typing import Dict
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

load_dotenv()

class SolverNode:
    def __init__(self, config_path: str = "config.json", test_mode: bool = False, mock_mode: bool = False):
        """Initialize the solver node with configuration
        
        Args:
            config_path: Path to configuration file
            test_mode: Run in test mode (uses real data generation)
            mock_mode: Run in mock mode (uses mock data and responses)
        """
        # Initialize logger
        self.logger = logging.getLogger('SolverNode')
        
        # Load configuration from file or environment
        try:
            with open(config_path) as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # Fallback to environment variables
            self.config = {
                "wallet_address": os.getenv("WALLET_ADDRESS", "0xMockWalletAddress"),  # Default mock wallet for mock mode
                "web3_rpc_url": os.getenv("WEB3_RPC_URL"),
                "chain_id": os.getenv("CHAIN_ID"),
                "private_key": os.getenv("PRIVATE_KEY"),
                "exchange_contract_address": os.getenv("EXCHANGE_CONTRACT_ADDRESS"),
                "nft_contract_address": os.getenv("NFT_CONTRACT_ADDRESS"),
                "pinata_api_key": os.getenv("PINATA_API_KEY"),
                "pinata_secret_api_key": os.getenv("PINATA_SECRET_API_KEY")
            }
            if not self.config["wallet_address"] and not mock_mode:
                raise ValueError("WALLET_ADDRESS must be set in environment or config.json")
        
        # Set operation mode
        self.test_mode = test_mode
        self.mock_mode = mock_mode
        
        # Validate mode configuration
        if self.test_mode and self.mock_mode:
            print("Warning: Both test and mock modes specified. Using test mode.")
            self.mock_mode = False
        
        # Initialize components based on mode
        if self.mock_mode:
            # Mock mode uses mock provider
            solver_config = DatasetConfig(
                provider_type=ProviderType.MOCK,
                num_records=100,
                date_range=["2024-01-01", "2024-12-31"],
                number_range=[0, 100],
                output_dir="data"
            )
        else:
            # Test mode MUST use HuggingFace provider
            if self.test_mode:
                solver_config = DatasetConfig(
                    provider_type=ProviderType.HUGGINGFACE,  # Force HuggingFace in test mode
                    num_records=100,
                    date_range=["2024-01-01", "2024-12-31"],
                    number_range=[0, 100],
                    output_dir="data",
                    provider_config={
                        "token": os.getenv("HUGGINGFACE_TOKEN"),
                        "model": "mistralai/Mistral-7B-Instruct-v0.2"
                    }
                )
            else:
                # Production mode
                solver_config = DatasetConfig(
                    provider_type=ProviderType.HUGGINGFACE,
                    num_records=100,
                    date_range=["2024-01-01", "2024-12-31"],
                    number_range=[0, 100],
                    output_dir="data",
                    provider_config={
                        "token": os.getenv("HUGGINGFACE_TOKEN"),
                        "model": "mistralai/Mistral-7B-Instruct-v0.2"
                    }
                )
        
        # Initialize solver with appropriate config
        self.solver = DataSolver(solver_config)
        
        # Initialize other components based on mode
        self.wallet_address = self.config.get("wallet_address")
        if not self.wallet_address:
            raise ValueError("WALLET_ADDRESS must be set in environment or config.json")
            
        self.authorizer = None if (self.test_mode or self.mock_mode) else NFTAuthorizer()
        self.submitter = None if (self.test_mode or self.mock_mode) else SolutionSubmitter(self.config)

        # Print mode information only once during initialization
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

    def process_rfd(self, rfd: Dict):
        """Process an RFD through the full flow"""
        rfd_id = rfd["rfd_id"]
        print(f"Processing RFD #{rfd_id} with wallet {self.wallet_address}")

        # Skip NFT check in test/mock modes
        if self.authorizer and not self.authorizer.has_nft(self.wallet_address):
            print(f"Wallet {self.wallet_address} does not own a Reppo NFT. Skipping RFD #{rfd_id}")
            return

        # Generate dataset
        if self.mock_mode:
            # In mock mode, always generate mock data
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
            file_path = os.path.join("data", f"rfd_{rfd_id}_solution.json")
            os.makedirs("data", exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(mock_data, f, indent=2)
            print(f"Generated mock dataset at: {file_path}")
        else:
            # Normal mode - use configured provider
            file_path = self.solver.solve_rfd(rfd)
            if file_path is None:
                if self.test_mode:
                    raise Exception("dataSolver.py not configured. Use --mock mode to continue without setting up dataSolver.py")
                return
            elif not os.path.exists(file_path):
                print(f"Failed to generate dataset for RFD #{rfd_id}")
                return

        # Handle IPFS upload
        try:
            if self.mock_mode:
                ipfs_uri = f"ipfs://mockCID_{rfd_id}_{int(time.time())}"
                print(f"Mock mode: Generated IPFS URI: {ipfs_uri}")
            else:
                ipfs_uri = upload_to_ipfs(file_path) if self.submitter else "ipfs://mockCID"
            print(f"Uploaded to IPFS: {ipfs_uri}")
        except Exception as e:
            print(f"IPFS upload failed for RFD #{rfd_id}: {str(e)}")
            return

        # Handle solution submission
        if self.mock_mode:
            # Generate a deterministic but unique mock transaction hash
            mock_tx = f"0x{'0' * 40}_{rfd_id}_{int(time.time())}"
            print(f"Mock mode: Generated transaction hash: {mock_tx}")
            print(f"Solution submitted for RFD #{rfd_id} by {self.wallet_address}. Tx hash: {mock_tx}")
        else:
            tx_hash = self.submitter.submit_solution(rfd_id, file_path) if self.submitter else "0xMockTransactionHash"
            if tx_hash:
                print(f"Solution submitted for RFD #{rfd_id} by {self.wallet_address}. Tx hash: {tx_hash}")
            else:
                print(f"Failed to submit solution for RFD #{rfd_id}")

    def run(self):
        """Run the Solver Node"""
        if self.mock_mode:
            print("\nProcessing sample RFD in mock mode...")
            try:
                # Load and process sample RFD
                with open("sample_rfd.json") as f:
                    sample_rfd = json.load(f)
                self.process_rfd(sample_rfd)
                return
            except FileNotFoundError:
                print("Error: sample_rfd.json not found. Please create a sample RFD file.")
                return
            except Exception as e:
                print(f"Error processing sample RFD: {str(e)}")
                return
        elif self.test_mode:
            print("Test mode: Processing sample RFD file")
            try:
                with open("sample_rfd.json") as f:
                    sample_rfd = json.load(f)
                self.process_rfd(sample_rfd)
                return
            except FileNotFoundError:
                print("Error: sample_rfd.json not found. Please create a sample RFD file.")
                return
            except Exception as e:
                print(f"Error processing sample RFD: {str(e)}")
                return
        else:
            if not self.authorizer:
                raise RuntimeError("Cannot run in production mode without authorizer")
            print("Production mode: Starting RFD listener")
            self.listener.listen_for_rfds(self.process_rfd)