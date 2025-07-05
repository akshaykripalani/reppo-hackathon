# main.py
"""Main entry point for the solver node."""

import click
import logging
from solverNode import SolverNode
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Main')

BANNER = """
 ██████╗ ██╗ ██████╗  █████╗ ███╗   ███╗ ██████╗██████╗ 
██╔════╝ ██║██╔════╝ ██╔══██╗████╗ ████║██╔════╝██╔══██╗
██║  ███╗██║██║  ███╗███████║██╔████╔██║██║     ██████╔╝
██║   ██║██║██║   ██║██╔══██║██║╚██╔╝██║██║     ██╔═══╝ 
╚██████╔╝██║╚██████╔╝██║  ██║██║ ╚═╝ ██║╚██████╗██║     
 ╚═════╝ ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝╚═╝     
"""

@click.group()
def cli():
    """Solver Node CLI - A tool for processing Requests for Data (RFDs)"""
    pass

@cli.command()
@click.option('--test', is_flag=True, help='Test mode: Process a sample RFD file with real data generation')
@click.option('--mock', is_flag=True, help='Mock mode: Simulate the entire pipeline with mock data and services')
@click.option('--rfd-file', default='sample_rfd.json', help='Path to sample RFD JSON file (used in test mode)')
def start(test: bool, mock: bool, rfd_file: str):
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
    
    # Initialize solver node
    try:
        node = SolverNode(
            test_mode=test,
            mock_mode=mock
        )
    except Exception as e:
        logger.error(f"Failed to initialize solver node: {str(e)}")
        return
    
    # Run the node
    try:
        if test or mock:
            node._run_test_mode()
        else:
            node._run_production_mode()
    except KeyboardInterrupt:
        logger.info("Solver node stopped by user")
    except Exception as e:
        logger.error(f"Solver node failed: {str(e)}")

if __name__ == '__main__':
    cli()