# solverNode.py
import os
from dotenv import load_dotenv
from rfdListener import RFDListener
from dataSolver import DataSolver
from ipfsUploader import upload_to_ipfs
from nftAuthorizer import NFTAuthorizer
from submitSolution import SolutionSubmitter
from typing import Dict

load_dotenv()

class SolverNode:
    def __init__(self, test_mode=False, mock_mode=False):
        self.wallet_address = os.environ.get("WALLET_ADDRESS")
        if not self.wallet_address:
            raise ValueError("WALLET_ADDRESS not set in environment")

        self.listener = RFDListener() if not test_mode else None
        self.solver = DataSolver()
        # Only initialize blockchain-related components if not in mock mode
        self.authorizer = NFTAuthorizer() if not mock_mode else None
        self.submitter = SolutionSubmitter() if not mock_mode else None

    def process_rfd(self, rfd: Dict):
        """Process an RFD through the full flow"""
        rfd_id = rfd["rfd_id"]
        print(f"Processing RFD #{rfd_id}...")

        if self.authorizer and not self.authorizer.has_nft(self.wallet_address):
            print(f"Wallet {self.wallet_address} does not own a Reppo NFT. Skipping RFD #{rfd_id}")
            return

        file_path = self.solver.solve_rfd(rfd)
        if not os.path.exists(file_path):
            print(f"Failed to generate dataset for RFD #{rfd_id}")
            return

        try:
            ipfs_uri = upload_to_ipfs(file_path) if self.submitter else "ipfs://mockCID"
            print(f"Uploaded to IPFS: {ipfs_uri}")
        except Exception as e:
            print(f"IPFS upload failed for RFD #{rfd_id}: {str(e)}")
            return

        if self.submitter:
            tx_hash = self.submitter.submit_solution(rfd_id, file_path)
        else:
            tx_hash = "0xMockTransactionHash"
        
        if tx_hash:
            print(f"Solution submitted for RFD #{rfd_id}. Tx hash: {tx_hash}")
        else:
            print(f"Failed to submit solution for RFD #{rfd_id}")

    def run(self):
        """Run the Solver Node"""
        if self.listener is None:
            raise RuntimeError("Cannot run in normal mode without listener")
        self.listener.listen_for_rfds(self.process_rfd)