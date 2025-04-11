import os
import json
from typing import Optional
from web3 import Web3
from dotenv import load_dotenv
from ipfsUploader import upload_to_ipfs  # Import your IPFS uploader

# Load environment variables
load_dotenv()

class SolutionSubmitter:
    """
    Class to handle solution submission to Reppo Exchange smart contract
    """
    def __init__(self):
        # Configuration from environment variables
        self.rpc_url = os.environ.get("WEB3_RPC_URL")
        self.exchange_contract_address = os.environ.get("EXCHANGE_CONTRACT_ADDRESS")
        self.exchange_contract_abi_path = os.environ.get(
            "EXCHANGE_CONTRACT_ABI_PATH",
            "./abis/exchange_abi.json"
        )
        self.private_key = os.environ.get("PRIVATE_KEY")
        self.chain_id = int(os.environ.get("CHAIN_ID", "1"))

        # Validate required environment variables
        required_vars = {
            "WEB3_RPC_URL": self.rpc_url,
            "EXCHANGE_CONTRACT_ADDRESS": self.exchange_contract_address,
            "PRIVATE_KEY": self.private_key
        }
        missing = [key for key, value in required_vars.items() if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Initialize Web3
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Load and initialize contract
        self._initialize_contract()

    def _initialize_contract(self) -> None:
        """Initialize the Exchange contract"""
        try:
            with open(self.exchange_contract_abi_path, 'r') as abi_file:
                self.exchange_contract_abi = json.load(abi_file)
            
            self.exchange_contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(self.exchange_contract_address),
                abi=self.exchange_contract_abi
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize Exchange contract: {str(e)}")

    def submit_solution(self, rfd_id: int, file_path: str) -> Optional[str]:
        """
        Submit solution URI to Reppo Exchange smart contract after uploading to IPFS
        
        Args:
            rfd_id: The Request for Data ID
            file_path: Path to the solution file to upload
            
        Returns:
            Optional[str]: Transaction hash if successful, None otherwise
        """
        try:
            # Upload to IPFS
            ipfs_uri = upload_to_ipfs(file_path)
            if not ipfs_uri:
                raise Exception("Failed to get IPFS URI")

            # Build transaction
            account = self.web3.eth.account.from_key(self.private_key)
            nonce = self.web3.eth.get_transaction_count(account.address)
            
            tx = self.exchange_contract.functions.submitSolution(
                rfd_id,
                ipfs_uri
            ).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price,
                'chain_id': self.chain_id
            })

            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return self.web3.to_hex(tx_hash)
            
        except Exception as e:
            print(f"Error submitting solution: {str(e)}")
            return None

    def is_connected(self) -> bool:
        """Check network connection"""
        try:
            return self.web3.is_connected() and self.web3.eth.chain_id == self.chain_id
        except Exception:
            return False

if __name__ == "__main__":
    try:
        # Initialize submitter
        submitter = SolutionSubmitter()
        
        if not submitter.is_connected():
            print("Error: Failed to connect to blockchain network")
            exit(1)

        # Step 1: Assume dataset is prepared at this path
        dataset_path = "/data/rfd_solution_dataset.json"
        if not os.path.exists(dataset_path):
            print(f"Error: Dataset not found at {dataset_path}")
            exit(1)

        # Step 2 & 3: Submit to smart contract (includes IPFS upload)
        rfd_id = int(os.environ.get("RFD_ID", "0"))
        print(f"Submitting solution for RFD #{rfd_id}...")
        
        tx_hash = submitter.submit_solution(rfd_id, dataset_path)
        if tx_hash:
            print(f"✅ Solution submitted successfully! Tx hash: {tx_hash}")
        else:
            print("❌ Failed to submit solution")
            exit(1)

    except Exception as e:
        print(f"Error in solution submission process: {str(e)}")
        exit(1)