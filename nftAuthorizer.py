import os
import json
from typing import List, Optional
from web3 import Web3
from web3.exceptions import ContractLogicError, Web3Exception
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NFTAuthorizer:
    """
    Class to verify NFT ownership for wallet addresses with enhanced security
    """
    def __init__(self):
        # Configuration from environment variables
        self.rpc_url = os.environ.get("WEB3_RPC_URL")
        self.nft_contract_address = os.environ.get("NFT_CONTRACT_ADDRESS")
        self.nft_contract_abi_path = os.environ.get(
            "NFT_CONTRACT_ABI_PATH", 
            "./abis/nft_abi.json"
        )
        self.chain_id = int(os.environ.get("CHAIN_ID", "1"))  # Default to Ethereum mainnet
        
        # Validate required environment variables
        if not all([self.rpc_url, self.nft_contract_address]):
            raise ValueError("Missing required environment variables: WEB3_RPC_URL or NFT_CONTRACT_ADDRESS")

        # Initialize Web3 connection with timeout and retry
        self.web3 = Web3(Web3.HTTPProvider(
            self.rpc_url,
            request_kwargs={'timeout': 30}
        ))
        
        # Load and initialize contract
        self._initialize_contract()

    def _initialize_contract(self) -> None:
        """Initialize the NFT contract with error handling"""
        try:
            with open(self.nft_contract_abi_path, 'r') as abi_file:
                self.nft_contract_abi = json.load(abi_file)
            
            self.nft_contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(self.nft_contract_address),
                abi=self.nft_contract_abi
            )
        except FileNotFoundError:
            raise ValueError(f"NFT contract ABI not found at {self.nft_contract_abi_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in NFT contract ABI at {self.nft_contract_abi_path}")
        except Exception as e:
            raise ValueError(f"Failed to initialize NFT contract: {str(e)}")

    def is_connected(self) -> bool:
        """Check network connection with chain ID verification"""
        try:
            return self.web3.is_connected() and self.web3.eth.chain_id == self.chain_id
        except Exception:
            return False

    def has_nft(self, wallet_address: str, block_number: Optional[int] = None) -> bool:
        """
        Check if a wallet address owns at least one NFT at the specified block
        
        Args:
            wallet_address: The wallet address to check
            block_number: Optional specific block number to check (defaults to latest)
            
        Returns:
            bool: True if wallet owns NFT, False otherwise
        """
        if not self.web3.is_address(wallet_address):
            raise ValueError(f"Invalid wallet address: {wallet_address}")
            
        try:
            checksum_address = self.web3.to_checksum_address(wallet_address)
            call_params = {'block_identifier': block_number} if block_number else {}
            
            balance = self.nft_contract.functions.balanceOf(checksum_address).call(call_params)
            return balance > 0
            
        except ContractLogicError as e:
            print(f"Contract error checking NFT ownership: {str(e)}")
            return False
        except Web3Exception as e:
            print(f"Web3 error checking NFT ownership: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error checking NFT ownership: {str(e)}")
            return False

    def get_owned_token_ids(self, wallet_address: str, block_number: Optional[int] = None) -> List[int]:
        """
        Get all token IDs owned by a wallet address at the specified block
        
        Args:
            wallet_address: The wallet address to check
            block_number: Optional specific block number to check (defaults to latest)
            
        Returns:
            List[int]: List of token IDs owned by the wallet
        """
        if not self.web3.is_address(wallet_address):
            raise ValueError(f"Invalid wallet address: {wallet_address}")

        checksum_address = self.web3.to_checksum_address(wallet_address)
        token_ids = []
        call_params = {'block_identifier': block_number} if block_number else {}
        
        try:
            balance = self.nft_contract.functions.balanceOf(checksum_address).call(call_params)
            if balance == 0:
                return []

            for i in range(balance):
                try:
                    token_id = self.nft_contract.functions.tokenOfOwnerByIndex(
                        checksum_address, 
                        i
                    ).call(call_params)
                    token_ids.append(token_id)
                except ContractLogicError as e:
                    print(f"Contract error getting token ID at index {i}: {str(e)}")
                    break
                    
            return token_ids
            
        except Web3Exception as e:
            print(f"Web3 error getting token IDs: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error getting token IDs: {str(e)}")
            return []

    def get_token_metadata(self, token_id: int, block_number: Optional[int] = None) -> Optional[dict]:
        """
        Get metadata for a specific token ID if supported by contract
        
        Args:
            token_id: The token ID to get metadata for
            block_number: Optional specific block number to check (defaults to latest)
            
        Returns:
            Optional[dict]: Token metadata if available, None otherwise
        """
        call_params = {'block_identifier': block_number} if block_number else {}
        
        try:
            if hasattr(self.nft_contract.functions, 'tokenURI'):
                uri = self.nft_contract.functions.tokenURI(token_id).call(call_params)
                return {'token_id': token_id, 'uri': uri}
            return None
        except Exception as e:
            print(f"Error getting token metadata: {str(e)}")
            return None

    def verify_ownership_at_block(self, wallet_address: str, block_number: int) -> bool:
        """
        Verify NFT ownership at a specific block number for additional security
        
        Args:
            wallet_address: The wallet address to check
            block_number: The specific block number to verify at
            
        Returns:
            bool: True if wallet owned NFT at specified block
        """
        return self.has_nft(wallet_address, block_number)

if __name__ == "__main__":
    try:
        authorizer = NFTAuthorizer()
        
        if not authorizer.is_connected():
            print("Error: Failed to connect to blockchain network")
            exit(1)

        wallet_to_check = os.environ.get("WALLET_ADDRESS")
        if not wallet_to_check:
            print("Error: WALLET_ADDRESS not set in environment")
            exit(1)

        # Check current ownership
        if authorizer.has_nft(wallet_to_check):
            token_ids = authorizer.get_owned_token_ids(wallet_to_check)
            print(f"✅ Wallet {wallet_to_check} owns {len(token_ids)} NFTs")
            print(f"Token IDs: {token_ids}")
            
            if token_ids:
                metadata = authorizer.get_token_metadata(token_ids[0])
                if metadata:
                    print(f"Metadata for token {token_ids[0]}: {metadata}")
        else:
            print(f"❌ Wallet {wallet_to_check} does not own any NFTs from the collection")
            
    except Exception as e:
        print(f"Error in NFT authorization process: {str(e)}")
        exit(1)