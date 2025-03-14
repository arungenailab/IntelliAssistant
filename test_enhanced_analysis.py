import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta

# Add the current directory to sys.path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from enhanced_gemini_helper
from utils.enhanced_gemini_helper import (
    generate_enhanced_dataset_analysis,
    format_analysis_to_markdown,
    generate_enhanced_visualizations,
    analyze_data
)

def load_sample_tsla_data():
    """
    Load a sample TSLA dataset for testing
    """
    # Generate sample dates
    end_date = datetime.strptime('2024-12-27', '%Y-%m-%d')
    dates = [end_date - timedelta(days=i) for i in range(100)]
    dates.reverse()  # Put in chronological order
    
    # Create a DataFrame with sample data
    data = {
        'date': dates,
        'open': [348.03 + (i % 50) * 2.5 for i in range(100)],
        'high': [356.00 + (i % 50) * 2.6 for i in range(100)],
        'low': [338.11 + (i % 50) * 2.4 for i in range(100)],
        'close': [346.78 + (i % 50) * 2.5 for i in range(100)],
        'volume': [91894850 + (i % 30) * 4000000 for i in range(100)]
    }
    
    # Adjust the last few rows to match the top 5 values mentioned
    data['open'][-1] = 475.90
    data['open'][-2] = 466.50
    data['open'][-3] = 465.16
    data['open'][-4] = 451.88
    data['open'][-5] = 449.52
    
    data['high'][-1] = 488.54
    data['high'][-2] = 484.00
    data['high'][-3] = 465.33
    data['high'][-4] = 463.19
    data['high'][-5] = 462.78
    
    return pd.DataFrame(data)

def main():
    """
    Test the enhanced analysis functionality
    """
    print("Loading TSLA sample data...")
    df = load_sample_tsla_data()
    print(f"Loaded data with shape: {df.shape}")
    
    # Test 1: Generate enhanced dataset analysis
    print("\n=== Testing Enhanced Dataset Analysis ===")
    analysis_result = generate_enhanced_dataset_analysis(df)
    
    # Print overview of the analysis result
    print(f"Analysis contains {len(analysis_result)} sections:")
    for section, content in analysis_result.items():
        if isinstance(content, dict):
            print(f"- {section}: {len(content)} items")
        else:
            print(f"- {section}: {type(content)}")
    
    # Test 2: Format analysis as markdown
    print("\n=== Testing Markdown Formatting ===")
    markdown = format_analysis_to_markdown(analysis_result)
    
    # Save the markdown to a file
    with open("test_analysis_output.md", "w") as f:
        f.write(markdown)
    print(f"Markdown report saved to test_analysis_output.md")
    
    # Test 3: Generate enhanced visualizations
    print("\n=== Testing Enhanced Visualizations ===")
    visualizations = generate_enhanced_visualizations(df)
    
    # Save the visualizations to a JSON file for inspection
    with open("test_visualization_output.json", "w") as f:
        json.dump({k: "<<JSON data>>" for k in visualizations.keys()}, f, indent=2)
    print(f"Visualization specs saved to test_visualization_output.json")
    print(f"Generated {len(visualizations)} visualizations:")
    for viz_name in visualizations.keys():
        print(f"- {viz_name}")
    
    # Test 4: Full analysis with a query
    print("\n=== Testing Full Analysis with Query ===")
    query = "Analyze the TSLA dataset: What are the trends in the stock price and volume?"
    analysis_response = analyze_data(query, df)
    
    # Check if the analysis was successful
    if "text" in analysis_response:
        print("Analysis successful!")
        print(f"Response contains {len(analysis_response)} elements:")
        for key in analysis_response.keys():
            print(f"- {key}")
        
        # Save the insights if available
        if "insights" in analysis_response and analysis_response["insights"]:
            with open("test_insights_output.md", "w") as f:
                f.write(analysis_response["insights"])
            print(f"AI insights saved to test_insights_output.md")
    else:
        print("Analysis failed!")
        print(analysis_response)
    
    print("\nTesting complete!")

if __name__ == "__main__":
    main() 