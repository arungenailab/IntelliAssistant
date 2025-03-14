# Integration Instructions for Data-Agnostic Analysis Framework

This document provides instructions for integrating the enhanced analysis framework into the IntelliAssistant application.

## Overview

The enhanced analysis framework is designed to be completely data-agnostic, automatically detecting the type of dataset being analyzed and applying appropriate analysis techniques and visualizations. This framework works with financial data, sales data, geographic data, time series data, and generic datasets.

## Required Dependencies

Add these dependencies to your environment:

```bash
pip install pandas numpy plotly seaborn matplotlib
```

## Files to Add or Update

Add/update the following files in your project:

1. **data_visualization.py**: Core module for dataset type detection and visualization generation
2. **enhanced_analysis.py**: Module for comprehensive dataset analysis with data type detection
3. **sample_visualizations.py**: Sample data and visualization examples (for testing)
4. **utils/enhanced_gemini_helper.py**: Enhanced version of the Gemini helper with improved analysis and fallback

## API Integration

To integrate the enhanced analysis with your existing API:

1. **Update the `/api/chat` endpoint in `api.py`**:

```python
from utils.enhanced_gemini_helper import analyze_data, suggest_query_improvements

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    dataset_name = data.get('dataset', DEFAULT_DATASET)
    
    # Load the selected dataset
    try:
        df = load_dataset(dataset_name)
    except Exception as e:
        return jsonify({'error': f'Error loading dataset: {str(e)}'})
    
    # Use the enhanced analyze_data function
    response_data = analyze_data(df, user_message)
    
    # Return the enhanced response including visualizations
    return jsonify({
        'message': response_data.get('markdown', ''),
        'visualizations': response_data.get('visualization_data', {}),
        'api_used': response_data.get('api_used', False)
    })
```

## Frontend Updates

The frontend should be updated to handle the enhanced analysis results:

1. **Update the Chat component to render markdown content**:
   - Use a Markdown rendering library like `react-markdown`
   - Ensure proper styling for tables and formatted numbers

2. **Add visualization rendering**:
   - Use Plotly.js to render the visualization JSON data
   - Create a `Visualization` component that accepts the visualization specs

```jsx
// Example Visualization component
import Plot from 'react-plotly.js';

function Visualization({ visualizationData }) {
  const chartData = JSON.parse(visualizationData);
  
  return (
    <div className="visualization-container">
      <Plot
        data={chartData.data}
        layout={chartData.layout}
        config={{ responsive: true }}
        style={{ width: '100%', height: '500px' }}
      />
    </div>
  );
}
```

## Testing

To test the integration:

1. **Test with Gemini API enabled**:
   - Verify that detailed analysis is generated
   - Check that visualizations are correct

2. **Test with Gemini API disabled**:
   - Set `GEMINI_API_KEY` to `None` in the environment
   - Verify that the fallback analysis still provides useful results
   - Check that visualizations are still generated

3. **Test with different dataset types**:
   - Financial data (stock data)
   - Sales/revenue data
   - Geographic data with location columns
   - Generic datasets with various column structures

## Recommended Additional Steps

For an even better user experience:

1. **Add dataset type detection feedback**:
   - Show the detected dataset type to users
   - Allow manual override if needed

2. **Add visualization controls**:
   - Allow users to switch between different visualizations
   - Enable zooming, panning, and saving visualizations

3. **Implement progressive enhancement**:
   - Show statistical analysis immediately
   - Load AI-enhanced analysis when ready
   - Display visualizations as they are generated 