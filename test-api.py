"""
Test script to check if the API server is accessible
"""

import requests
import sys
import time

def test_api_connection(url="http://localhost:5000/api/status", max_retries=3):
    """Test connection to the API server"""
    print(f"Testing connection to {url}...")
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries}...")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Connection successful! Status code: {response.status_code}")
                print(f"Response: {data}")
                return True
            else:
                print(f"❌ Connection failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection error: Could not connect to {url}")
        except requests.exceptions.Timeout:
            print(f"❌ Timeout error: The request to {url} timed out")
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
        
        if attempt < max_retries:
            print(f"Retrying in 2 seconds...")
            time.sleep(2)
    
    print("\nTroubleshooting tips:")
    print("1. Make sure the backend server is running (python api.py)")
    print("2. Check that the server is running on port 5000")
    print("3. Verify there are no firewall or network issues")
    print("4. Check for any error messages in the server logs")
    
    return False

if __name__ == "__main__":
    # Allow custom URL from command line
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000/api/status"
    
    # Test the connection
    success = test_api_connection(url)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 