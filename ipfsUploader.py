import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API credentials from environment variables
PINATA_API_KEY = os.environ.get("PINATA_API_KEY")
PINATA_SECRET_API_KEY = os.environ.get("PINATA_SECRET_API_KEY")

def upload_to_ipfs(file_path: str) -> str:
    """Uploads a file to IPFS using Pinata
    
    Args:
        file_path: Path to the file to upload
        
    Returns:
        str: IPFS URI (e.g., "ipfs://<CID>")
        
    Raises:
        Exception: If upload fails or credentials are missing
    """
    # Verify API keys exist
    if not PINATA_API_KEY or not PINATA_SECRET_API_KEY:
        raise Exception("Pinata API keys are missing. Please set PINATA_API_KEY and PINATA_SECRET_API_KEY in your .env file.")
    
    # Pinata API endpoint for file uploads
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    
    # Set up headers with Pinata API keys
    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_API_KEY
    }
    
    # Set up optional Pinata metadata
    file_name = os.path.basename(file_path)
    pinata_metadata = json.dumps({
        "name": file_name
    })
    
    # Open and read the file
    try:
        with open(file_path, 'rb') as file:
            files = {
                'file': (file_name, file)
            }
            
            data = {
                'pinataMetadata': pinata_metadata
            }
            
            # Make the request
            response = requests.post(url, files=files, headers=headers, data=data)
            
            # Check response
            if response.status_code == 200:
                # Extract CID from response
                data = response.json()
                cid = data.get('IpfsHash')
                if not cid:
                    raise Exception("No IPFS hash returned in response")
                return f"ipfs://{cid}"
            else:
                # Handle error
                error_message = response.text
                try:
                    error_data = response.json()
                    error_message = json.dumps(error_data)
                except json.JSONDecodeError:
                    pass
                raise Exception(f"Failed to upload to IPFS: {response.status_code} - {error_message}")
                
    except FileNotFoundError:
        raise Exception(f"File not found at path: {file_path}")
    except Exception as e:
        raise Exception(f"Unexpected error during IPFS upload: {str(e)}")

if __name__ == "__main__":
    file_path = "./data/solution.json"
    print("Current working directory:", os.getcwd())
    try:
        ipfs_uri = upload_to_ipfs(file_path)
        print("Uploaded to:", ipfs_uri)
    except Exception as e:
        print(f"Error: {e}")