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
@click.option('--test', is_flag=True, help='Run in test mode with local RFD file')
@click.option('--mock', is_flag=True, help='Mock external services for offline testing')
@click.option('--rfd-file', default='sample_rfd.json', help='Path to sample RFD JSON file')
def start(test, mock, rfd_file):
    """Start the solver node"""
    print(BANNER)
    node = SolverNode(test_mode=test, mock_mode=mock)
    if mock:
        print("Mocking external services...")
        # Mocking is now handled in SolverNode initialization
    
    if test:
        print("Running in test mode...")
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
        print(f"Starting Reppo Solver Node for wallet {node.wallet_address}")
        node.run()

if __name__ == "__main__":
    cli()