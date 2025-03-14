import requests
import json

def test_dataset_availability():
    """Test if the MSFT dataset is available"""
    response = requests.get("http://localhost:5000/api/datasets")
    if response.status_code == 200:
        datasets = response.json()
        print(f"Available datasets: {list(datasets.keys())}")
        return "MSFT" in datasets
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return False

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