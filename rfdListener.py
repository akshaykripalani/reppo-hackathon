import os
import json
from web3 import Web3
from dotenv import load_dotenv
import time
from typing import Dict, Optional

# Load environment variables
load_dotenv()

class RFDListener:
    def __init__(self):
        self.rpc_url = os.environ.get("WEB3_RPC_URL")
        self.exchange_contract_address = os.environ.get("EXCHANGE_CONTRACT_ADDRESS")
        self.exchange_contract_abi_path = os.environ.get("EXCHANGE_CONTRACT_ABI_PATH", "./abis/exchange_abi.json")
        self.chain_id = int(os.environ.get("CHAIN_ID", "1"))

        if not all([self.rpc_url, self.exchange_contract_address]):
            raise ValueError("Missing required environment variables: WEB3_RPC_URL or EXCHANGE_CONTRACT_ADDRESS")

        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self._initialize_contract()

    def _initialize_contract(self):
        """Initialize the Exchange contract"""
        with open(self.exchange_contract_abi_path, 'r') as abi_file:
            abi = json.load(abi_file)
        self.contract = self.web3.eth.contract(
            address=self.web3.to_checksum_address(self.exchange_contract_address),
            abi=abi
        )

    def listen_for_rfds(self, callback: callable) -> None:
        """Listen for new RFD events and pass them to a callback function"""
        # Assumed event: RFDPosted(string rfdId, string name, string description, string schema)
        event_filter = self.contract.events.RFDPosted.create_filter(from_block="latest")
        print("Listening for new RFDs...")

        while True:
            try:
                for event in event_filter.get_new_entries():
                    rfd = {
                        "rfd_id": event['args']['rfdId'],
                        "name": event['args']['name'],
                        "description": event['args']['description'],
                        "schema": json.loads(event['args']['schema'])  # Parse schema from string to dict
                    }
                    print(f"New RFD detected: ID={rfd['rfd_id']}, Name={rfd['name']}")
                    callback(rfd)
            except Exception as e:
                print(f"Error listening for RFDs: {str(e)}")
            time.sleep(10)  # Poll every 10 seconds

if __name__ == "__main__":
    def dummy_callback(rfd: Dict):
        print(f"Processing RFD: {rfd}")

    listener = RFDListener()
    listener.listen_for_rfds(dummy_callback)