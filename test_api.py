import requests
import json
import os
import sys
import time
import socket

# Set environment variable for testing
os.environ["ENABLE_LANGGRAPH_SQL"] = "true"

def is_port_open(host, port):
    """Check if the port is open for a given host."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def wait_for_server(host, port, max_retries=10, delay=2):
    """Wait for the server to be available."""
    for i in range(max_retries):
        print(f"Checking if server is running (attempt {i+1}/{max_retries})...")
        if is_port_open(host, port):
            print(f"Server is up and running on {host}:{port}")
            return True
        print(f"Server not available yet. Retrying in {delay} seconds...")
        time.sleep(delay)
    return False

# Server details
host = "localhost"
port = 5000
url = f"http://{host}:{port}/api/convert_nl_to_sql"

# Wait for server to be up
if not wait_for_server(host, port):
    print("Server did not start within the timeout period.")
    sys.exit(1)

# Sample payload
payload = {
    "query": "Show me all customers",
    "connection_params": {
        "server": "test_server",
        "database": "test_db",
        "username": "test_user", 
        "password": "test_password",
        "driver": "ODBC Driver 17 for SQL Server"
    },
    "execute": False
}

print(f"Sending request to: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")

try:
    # Send the request
    response = requests.post(url, json=payload)
    
    # Print the response
    print(f"Status code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
except Exception as e:
    print(f"Error: {e}")

def test_dataset_availability():
    """Test API for dataset availability."""
    try:
        payload = {
            "connection_params": payload["connection_params"]
        }
        test_url = f"http://{host}:{port}/api/test_connection"
        print(f"\nTesting connection: {test_url}")
        response = requests.post(test_url, json=payload)
        print(f"Status code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

# Optional: Test connection
# test_dataset_availability()

def test_analyze_data(dataset_name="MSFT"):
    """Test if the analyze_data endpoint works"""
    data = {
        "message": f"Analyze the {dataset_name} dataset: What's the highest open price?", 
        "datasetName": dataset_name
    }
    response = requests.post("http://localhost:5000/api/chat", json=data)
    if response.status_code == 200:
        result = response.json()
        print(f"Analysis response: {result['text'][:100]}...")
        if "visualization" in result and result["visualization"]:
            print(f"Visualization type: {result['visualization']['type']}")
        return True
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return False

if __name__ == "__main__":
    print("Testing API...")
    if test_dataset_availability():
        print("Dataset test: SUCCESS")
        if test_analyze_data():
            print("Analysis test: SUCCESS")
        else:
            print("Analysis test: FAILED")
    else:
        print("Dataset test: FAILED") 