# main.py
import click
import json
from solverNode import SolverNode

BANNER = """
  ____                          _   _           _      
 |  _ \\ ___ _ __  _ __   ___   | \\ | | ___   __| | ___ 
 | |_) / _ \\ '_ \\| '_ \\ / _ \\  |  \\| |/ _ \\ / _` |/ _ \\
 |  _ <  __/ |_) | |_) | (_) | | |\\  | (_) | (_| |  __/
 |_| \\_\\___| .__/| .__/ \\___/  |_| \\_|\\___/ \\__,_|\\___|
           |_|   |_|                                   
"""

@click.group()
def cli():
    """Reppo Solver Node CLI"""
    pass

@cli.command()
@click.option('--test', is_flag=True, help='Test mode: Process a sample RFD file with real data generation')
@click.option('--mock', is_flag=True, help='Mock mode: Simulate the entire pipeline with mock data and services')
@click.option('--rfd-file', default='sample_rfd.json', help='Path to sample RFD JSON file (used in test mode)')
def start(test, mock, rfd_file):
    """Start the solver node
    
    Test mode (--test):
    - Processes a sample RFD file
    - Uses real data generation (HuggingFace if available)
    - Skips blockchain interactions
    - Good for testing data generation logic
    
    Mock mode (--mock):
    - Simulates the entire pipeline
    - Uses mock data generation
    - Uses mock blockchain responses
    - Good for development and debugging
    """
    print(BANNER)
    
    if test and mock:
        print("Warning: Both test and mock modes specified. Mock mode will take precedence.")
        test = False
    
    node = SolverNode(test_mode=test, mock_mode=mock)
    
    if mock:
        # Mock mode uses node.run() which handles sample RFD processing
        node.run()
    elif test:
        print("Running in TEST mode:")
        print("- Processing sample RFD file")
        print("- Using real data generation (if available)")
        print("- Skipping blockchain interactions")
        try:
            with open(rfd_file, 'r') as f:
                sample_rfd = json.load(f)
            print(f"Processing test RFD from {rfd_file}")
            node.process_rfd(sample_rfd)
        except FileNotFoundError:
            print(f"Error: Sample RFD file not found at {rfd_file}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {rfd_file}")
        except Exception as e:
            print(f"Error processing test RFD: {str(e)}")
    else:
        print(f"Starting Reppo Solver Node in PRODUCTION mode for wallet {node.wallet_address}")
        print("- Listening for RFDs on blockchain")
        print("- Using real data generation (if available)")
        print("- Using real blockchain interactions")
        node.run()

if __name__ == "__main__":
    cli()