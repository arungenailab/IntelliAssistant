import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from datetime import datetime
from data_visualization import load_sample_data, detect_dataset_type, generate_visualizations

def create_visualizations_from_sample(dataset_type="financial", output_dir="visualizations"):
    """
    Create a set of visualizations using sample data of the specified type
    
    Args:
        dataset_type: Type of dataset to generate ("financial", "sales", "geographic", "generic")
        output_dir: Directory to save visualization files
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.join(output_dir, dataset_type), exist_ok=True)
    
    # Load sample data of the specified type
    df = load_sample_data(dataset_type)
    
    # Detect dataset type and verify
    detected_type = detect_dataset_type(df)
    print(f"Generated sample {dataset_type} data (detected as: {detected_type})")
    print(f"Dataset shape: {df.shape}")
    
    # Generate visualizations
    visualizations = generate_visualizations(df)
    
    # Save each visualization to an HTML file
    for viz_name, viz_json in visualizations.items():
        viz_fig = go.Figure(url_json=viz_json)
        output_file = os.path.join(output_dir, dataset_type, f"{viz_name}.html")
        viz_fig.write_html(output_file)
        print(f"Saved visualization: {output_file}")

def create_all_sample_visualizations(output_dir="visualizations"):
    """
    Create visualizations for all sample dataset types
    
    Args:
        output_dir: Directory to save visualization files
    """
    dataset_types = ["financial", "sales", "geographic", "generic"]
    
    for dataset_type in dataset_types:
        print(f"\nGenerating visualizations for {dataset_type} data:")
        create_visualizations_from_sample(dataset_type, output_dir)

if __name__ == "__main__":
    # Create visualizations for all dataset types
    create_all_sample_visualizations()
    
    print("\nAll sample visualizations complete!") 