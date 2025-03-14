import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# This script assumes you have a dataset named 'TSLA' in your application
# If not, you'll need to load it from a CSV or other source

def load_sample_data():
    """Mock function to create sample TSLA data for demonstration"""
    # Sample data based on the statistics provided
    dates = pd.date_range(end='2024-12-27', periods=100)
    
    # Create a DataFrame with rough approximations based on the statistics
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

def create_visualizations(df, output_dir="visualizations"):
    """Create a set of visualizations for the TSLA dataset"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Price Line Chart
    fig = px.line(df, x='date', y=['open', 'high', 'low', 'close'], 
                 title='TSLA Stock Price Over Time',
                 labels={'value': 'Price ($)', 'date': 'Date', 'variable': 'Price Type'},
                 template='plotly_white')
    fig.update_layout(legend_title_text='', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.write_html(os.path.join(output_dir, "tesla_price_history.html"))
    
    # 2. Candlestick Chart
    fig = go.Figure(data=[go.Candlestick(x=df['date'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'])])
    fig.update_layout(title='TSLA Candlestick Chart',
                     xaxis_title='Date',
                     yaxis_title='Price ($)',
                     template='plotly_white')
    fig.write_html(os.path.join(output_dir, "tesla_candlestick.html"))
    
    # 3. Volume Bar Chart
    fig = px.bar(df, x='date', y='volume', 
                title='TSLA Trading Volume',
                labels={'volume': 'Volume', 'date': 'Date'},
                template='plotly_white')
    fig.update_layout(yaxis=dict(title='Volume', tickformat=",.0f"))
    fig.write_html(os.path.join(output_dir, "tesla_volume.html"))
    
    # 4. Price Distribution
    fig = make_subplots(rows=2, cols=2, 
                       subplot_titles=("Open Price Distribution", "High Price Distribution", 
                                      "Low Price Distribution", "Close Price Distribution"))
    
    fig.add_trace(go.Histogram(x=df['open'], name="Open", marker_color='blue'), row=1, col=1)
    fig.add_trace(go.Histogram(x=df['high'], name="High", marker_color='green'), row=1, col=2)
    fig.add_trace(go.Histogram(x=df['low'], name="Low", marker_color='red'), row=2, col=1)
    fig.add_trace(go.Histogram(x=df['close'], name="Close", marker_color='purple'), row=2, col=2)
    
    fig.update_layout(title_text="TSLA Price Distributions", showlegend=False, height=800)
    fig.write_html(os.path.join(output_dir, "tesla_distributions.html"))
    
    # 5. Combined Top 5 Visualization
    # Get top 5 by each metric
    top_open = df.nlargest(5, 'open')[['date', 'open']]
    top_high = df.nlargest(5, 'high')[['date', 'high']]
    top_low = df.nlargest(5, 'low')[['date', 'low']]
    top_close = df.nlargest(5, 'close')[['date', 'close']]
    top_volume = df.nlargest(5, 'volume')[['date', 'volume']]
    
    # Format dates for better display
    top_open['date'] = top_open['date'].dt.strftime('%Y-%m-%d')
    top_high['date'] = top_high['date'].dt.strftime('%Y-%m-%d')
    top_low['date'] = top_low['date'].dt.strftime('%Y-%m-%d')
    top_close['date'] = top_close['date'].dt.strftime('%Y-%m-%d')
    top_volume['date'] = top_volume['date'].dt.strftime('%Y-%m-%d')
    
    # Create a subplot with 1 row and 5 columns
    fig = make_subplots(rows=3, cols=2, 
                      subplot_titles=("Top 5 Open Prices", "Top 5 High Prices", 
                                     "Top 5 Low Prices", "Top 5 Close Prices",
                                     "Top 5 Trading Volumes"),
                      specs=[[{}, {}], [{}, {}], [{"colspan": 2}, None]],
                      vertical_spacing=0.1)
    
    # Add traces for each top 5
    fig.add_trace(go.Bar(x=top_open['date'], y=top_open['open'], name="Open", marker_color='blue'), row=1, col=1)
    fig.add_trace(go.Bar(x=top_high['date'], y=top_high['high'], name="High", marker_color='green'), row=1, col=2)
    fig.add_trace(go.Bar(x=top_low['date'], y=top_low['low'], name="Low", marker_color='red'), row=2, col=1)
    fig.add_trace(go.Bar(x=top_close['date'], y=top_close['close'], name="Close", marker_color='purple'), row=2, col=2)
    fig.add_trace(go.Bar(x=top_volume['date'], y=top_volume['volume'], name="Volume", marker_color='orange'), row=3, col=1)
    
    # Update layout
    fig.update_layout(title_text="TSLA Top 5 Analysis", showlegend=False, height=1000)
    
    # Format y-axis for volume to use comma separators
    fig.update_yaxes(row=3, col=1, tickformat=",.0f")
    
    fig.write_html(os.path.join(output_dir, "tesla_top5_analysis.html"))
    
    print(f"Visualizations created in '{output_dir}' directory")

if __name__ == "__main__":
    # Load data (replace with actual data loading if available)
    tesla_data = load_sample_data()
    
    # Create visualizations
    create_visualizations(tesla_data)
    
    print("Tesla (TSLA) visualizations complete.") 