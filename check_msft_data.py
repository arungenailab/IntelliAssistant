import requests
import pandas as pd
import json

# Fetch the MSFT dataset
response = requests.get("http://localhost:5000/api/datasets")
data = response.json()

# Extract the MSFT preview data
msft_preview = data.get("MSFT", {}).get("preview", [])

# Create a DataFrame from the preview data
df_preview = pd.DataFrame(msft_preview)

# Print the highest open price from the preview
if not df_preview.empty and 'open' in df_preview.columns:
    max_open_preview = df_preview['open'].max()
    print(f"Highest open price in preview: {max_open_preview}")
    
    # Print all open prices sorted in descending order
    print("\nTop 5 open prices in preview:")
    for i, price in enumerate(sorted(df_preview['open'].tolist(), reverse=True)[:5]):
        print(f"{i+1}. {price}")

# Let's try to fetch the full MSFT dataset directly
try:
    # Create a request to fetch the MSFT data
    fetch_payload = {
        "api_source_id": "financial",
        "endpoint": "stocks",
        "params": {
            "function": "TIME_SERIES_DAILY",
            "symbol": "MSFT"
        },
        "dataset_name": "MSFT_FULL",
        "credentials": {
            "api_key": "AIzaSyDLh_1hzgStSEKBkky_I09jV65jw7Dqon8"
        }
    }
    
    fetch_response = requests.post("http://localhost:5000/api/external-data/fetch", json=fetch_payload)
    fetch_data = fetch_response.json()
    
    if fetch_data.get("success"):
        print("\nSuccessfully fetched full MSFT dataset")
        print(f"Shape: {fetch_data.get('shape')}")
        
        # Extract the full preview data
        full_preview = fetch_data.get("preview", [])
        df_full = pd.DataFrame(full_preview)
        
        if not df_full.empty and 'open' in df_full.columns:
            max_open_full = df_full['open'].max()
            print(f"Highest open price in full dataset: {max_open_full}")
            
            # Print all open prices sorted in descending order
            print("\nTop 5 open prices in full dataset:")
            for i, price in enumerate(sorted(df_full['open'].tolist(), reverse=True)[:5]):
                print(f"{i+1}. {price}")
    else:
        print(f"\nError fetching full dataset: {fetch_data.get('error')}")
except Exception as e:
    print(f"\nError in API request: {str(e)}")

# Let's also check the dataset info directly
try:
    # Create a debug request to get application state
    debug_response = requests.get("http://localhost:5000/api/debug/state")
    debug_data = debug_response.json()
    
    print("\nDebug state:")
    if "datasets" in debug_data and "MSFT" in debug_data["datasets"]:
        msft_info = debug_data["datasets"]["MSFT"]
        print(f"MSFT dataset shape: {msft_info.get('shape')}")
        print(f"MSFT dataset columns: {msft_info.get('columns')}")
    else:
        print("MSFT dataset not found in debug state")
except Exception as e:
    print(f"Error getting debug state: {str(e)}") 