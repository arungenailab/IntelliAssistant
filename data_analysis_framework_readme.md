# Data-Agnostic Analysis Framework

This framework provides a versatile data analysis solution that can automatically adapt to different types of datasets without requiring any dataset-specific configuration.

## Key Features

- **Automatic Dataset Type Detection**: The framework can identify whether your data is financial, sales, geographic, time series, or generic.
- **Type-Specific Analysis**: Once detected, the framework applies specialized metrics and visualizations tailored to that data type.
- **Fallback Analysis**: Even when AI services like Gemini are unavailable, the framework provides robust statistical analysis.
- **Interactive Visualizations**: Generates appropriate visualizations based on data structure.
- **Well-Formatted Reports**: Presents analysis in clean, well-formatted markdown.

## Supported Dataset Types

The framework automatically detects and provides specialized analysis for these dataset types:

1. **Financial Data**: Stock/pricing data with open, high, low, close values.
   - Specialized metrics: volatility, returns, moving averages
   - Visualizations: candlestick charts, volume analysis, price distributions

2. **Sales Data**: Revenue, product, and sales information.
   - Specialized metrics: profit margins, product performance, time-based sales
   - Visualizations: revenue by product, profit margin charts, sales trends

3. **Geographic Data**: Country, region, or location-based data.
   - Specialized metrics: aggregation by geographic entity
   - Visualizations: geographic comparisons, metric distributions by location

4. **Time Series Data**: Any data with significant time components.
   - Specialized metrics: trends, seasonality, significant changes
   - Visualizations: time plots, seasonal patterns, value distributions over time

5. **Generic Data**: Any dataset not matching the patterns above.
   - Provides core statistical analysis
   - Visualizations: correlations, distributions, categorical summaries

## How It Works

1. When data is loaded, the `detect_dataset_type()` function analyzes column names and data structure.
2. Based on the detected type, specialized analysis functions are applied.
3. Visualizations are generated appropriate to the dataset type.
4. Results are formatted as clean markdown with proper formatting of numbers, tables, and sections.

## Usage Example

```python
import pandas as pd
from enhanced_analysis import generate_enhanced_dataset_analysis, format_analysis_to_markdown
from data_visualization import generate_visualizations

# Load any dataset
df = pd.read_csv('your_dataset.csv')

# Generate analysis (automatically detects dataset type)
analysis_result = generate_enhanced_dataset_analysis(df)

# Generate visualizations
visualization_specs = generate_visualizations(df)

# Format as markdown
report = format_analysis_to_markdown(analysis_result)

# Display or save the report
print(report)
```

## Benefits

- **No Configuration Required**: The framework adapts to your data automatically.
- **Consistent Output**: Standard formatting regardless of data type.
- **Graceful Degradation**: Provides useful analysis even without AI services.
- **Extensible**: Easy to add support for new data types and metrics.

## Sample Files

- **data_visualization.py**: Core visualization generation with dataset type detection
- **enhanced_analysis.py**: Statistical analysis tailored to each dataset type
- **sample_visualizations.py**: Examples for different dataset types
- **utils/enhanced_gemini_helper.py**: Integration with Gemini AI (with fallback) 