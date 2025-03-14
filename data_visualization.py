import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List, Optional, Union
import os
from datetime import datetime

def load_sample_data(dataset_type: str = "generic") -> pd.DataFrame:
    """
    Create sample data for demonstration and testing
    
    Args:
        dataset_type: Type of data to generate ("financial", "sales", "geographic", "generic")
        
    Returns:
        DataFrame with sample data
    """
    if dataset_type == "financial":
        # Generate financial data similar to stock prices
        dates = pd.date_range(end=datetime.now(), periods=100)
        
        # Create DataFrame with sample financial data
        data = {
            'date': dates,
            'open': [348.03 + (i % 50) * 2.5 for i in range(100)],
            'high': [356.00 + (i % 50) * 2.6 for i in range(100)],
            'low': [338.11 + (i % 50) * 2.4 for i in range(100)],
            'close': [346.78 + (i % 50) * 2.5 for i in range(100)],
            'volume': [91894850 + (i % 30) * 4000000 for i in range(100)]
        }
        
        # Set some representative high values for demonstration
        data['open'][-1] = 475.90
        data['high'][-1] = 488.54
        
        return pd.DataFrame(data)
    
    elif dataset_type == "sales":
        # Generate sales data
        dates = pd.date_range(end=datetime.now(), periods=100)
        products = ['Product A', 'Product B', 'Product C', 'Product D', 'Product E']
        regions = ['North', 'South', 'East', 'West', 'Central']
        
        # Create sales records
        data = []
        for i in range(500):  # 500 sales records
            data.append({
                'date': dates[i % 100],
                'product': products[i % 5],
                'region': regions[i % 5],
                'quantity': np.random.randint(1, 50),
                'price': np.random.uniform(10, 100),
                'cost': np.random.uniform(5, 50),
            })
        
        df = pd.DataFrame(data)
        df['revenue'] = df['quantity'] * df['price']
        df['profit'] = df['revenue'] - (df['quantity'] * df['cost'])
        return df
    
    elif dataset_type == "geographic":
        # Generate geographic data
        countries = ['USA', 'Canada', 'UK', 'Germany', 'France', 'Japan', 'Australia', 'China', 'Brazil', 'India']
        metrics = ['GDP', 'Population', 'Life Expectancy', 'Education Index', 'Happiness Score']
        
        data = []
        for country in countries:
            data.append({
                'country': country,
                'continent': np.random.choice(['North America', 'Europe', 'Asia', 'Oceania', 'South America']),
                'GDP': np.random.uniform(1000, 50000),
                'Population': np.random.randint(1000000, 1500000000),
                'Life Expectancy': np.random.uniform(60, 85),
                'Education Index': np.random.uniform(0.5, 0.95),
                'Happiness Score': np.random.uniform(4, 8)
            })
        
        return pd.DataFrame(data)
    
    else:  # generic data
        # Generate generic numeric and categorical data
        n_rows = 100
        data = {
            'id': range(1, n_rows + 1),
            'category': np.random.choice(['A', 'B', 'C', 'D'], n_rows),
            'numeric1': np.random.normal(100, 20, n_rows),
            'numeric2': np.random.normal(50, 10, n_rows),
            'numeric3': np.random.exponential(10, n_rows),
            'date': pd.date_range(end=datetime.now(), periods=n_rows),
        }
        
        return pd.DataFrame(data)

def detect_dataset_type(df: pd.DataFrame) -> str:
    """
    Detect the type of dataset based on column names and data structure
    
    Args:
        df: The DataFrame to analyze
        
    Returns:
        String indicating dataset type: "financial", "sales", "geographic", "time_series", or "generic"
    """
    columns = df.columns.str.lower()
    
    # Check for financial/stock data
    if all(col in columns for col in ['open', 'high', 'low', 'close']):
        return "financial"
    
    # Check for sales data
    sales_indicators = ['sales', 'revenue', 'profit', 'product', 'customer', 'quantity', 'price']
    if sum(col in columns for col in sales_indicators) >= 3:
        return "sales"
    
    # Check for geographic data
    geo_indicators = ['country', 'region', 'city', 'latitude', 'longitude', 'state', 'province']
    if sum(col in columns for col in geo_indicators) >= 2:
        return "geographic"
    
    # Check for time series data
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    if date_cols and len(date_cols) >= 1:
        return "time_series"
    
    # Default to generic
    return "generic"

def generate_visualizations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate appropriate visualizations based on the dataset type
    
    Args:
        df: DataFrame to visualize
        
    Returns:
        Dictionary containing visualization specifications
    """
    # Detect dataset type
    dataset_type = detect_dataset_type(df)
    
    # Select visualization generator based on dataset type
    if dataset_type == "financial":
        return generate_financial_visualizations(df)
    elif dataset_type == "sales":
        return generate_sales_visualizations(df)
    elif dataset_type == "geographic":
        return generate_geographic_visualizations(df)
    elif dataset_type == "time_series":
        return generate_time_series_visualizations(df)
    else:
        return generate_generic_visualizations(df)

def generate_financial_visualizations(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate visualizations for financial/stock data"""
    visualizations = {}
    
    # Make sure we have all required columns
    if not all(col in df.columns for col in ['date', 'open', 'high', 'low', 'close', 'volume']):
        return generate_generic_visualizations(df)
    
    # Sort by date
    if 'date' in df.columns:
        df = df.sort_values('date')
    
    # 1. Price and Volume Overview
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Price Chart", "Trading Volume"),
        row_heights=[0.7, 0.3]
    )
    
    # Add price candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="Price"
        ),
        row=1, col=1
    )
    
    # Add volume bar chart
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['volume'],
            name="Volume",
            marker=dict(color='rgba(0, 0, 128, 0.5)')
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title="Price and Volume Analysis",
        yaxis_title="Price",
        yaxis2_title="Volume",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        showlegend=False,
        height=800,
        yaxis2=dict(tickformat=",.0f")
    )
    
    visualizations["price_volume_chart"] = fig.to_json()
    
    # 2. Top 5 Days Visualization
    top_days_fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Top 5 Days by Opening Price",
            "Top 5 Days by High Price",
            "Top 5 Days by Closing Price",
            "Top 5 Days by Trading Volume"
        )
    )
    
    # Get top 5 by each metric
    top_open = df.nlargest(5, 'open')[['date', 'open']]
    top_high = df.nlargest(5, 'high')[['date', 'high']]
    top_close = df.nlargest(5, 'close')[['date', 'close']]
    top_volume = df.nlargest(5, 'volume')[['date', 'volume']]
    
    # Format dates for display if they're timestamps
    for dframe in [top_open, top_high, top_close, top_volume]:
        if isinstance(dframe['date'].iloc[0], pd.Timestamp):
            dframe['date'] = dframe['date'].dt.strftime('%Y-%m-%d')
    
    # Add traces for each top 5
    top_days_fig.add_trace(
        go.Bar(x=top_open['date'], y=top_open['open'], marker=dict(color='royalblue')),
        row=1, col=1
    )
    
    top_days_fig.add_trace(
        go.Bar(x=top_high['date'], y=top_high['high'], marker=dict(color='green')),
        row=1, col=2
    )
    
    top_days_fig.add_trace(
        go.Bar(x=top_close['date'], y=top_close['close'], marker=dict(color='darkred')),
        row=2, col=1
    )
    
    top_days_fig.add_trace(
        go.Bar(x=top_volume['date'], y=top_volume['volume'], marker=dict(color='purple')),
        row=2, col=2
    )
    
    # Format y-axis for volume
    top_days_fig.update_yaxes(row=2, col=2, tickformat=",.0f")
    
    # Update layout
    top_days_fig.update_layout(
        title="Top Trading Days Analysis",
        showlegend=False,
        template="plotly_white",
        height=800
    )
    
    visualizations["top_days_chart"] = top_days_fig.to_json()
    
    # 3. Price Distribution
    dist_fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Open Price Distribution",
            "High Price Distribution", 
            "Low Price Distribution", 
            "Close Price Distribution"
        )
    )
    
    dist_fig.add_trace(
        go.Histogram(x=df['open'], nbinsx=20, marker=dict(color='royalblue')),
        row=1, col=1
    )
    
    dist_fig.add_trace(
        go.Histogram(x=df['high'], nbinsx=20, marker=dict(color='green')),
        row=1, col=2
    )
    
    dist_fig.add_trace(
        go.Histogram(x=df['low'], nbinsx=20, marker=dict(color='red')),
        row=2, col=1
    )
    
    dist_fig.add_trace(
        go.Histogram(x=df['close'], nbinsx=20, marker=dict(color='purple')),
        row=2, col=2
    )
    
    dist_fig.update_layout(
        title="Price Distribution Analysis",
        showlegend=False,
        template="plotly_white",
        height=800
    )
    
    visualizations["price_distribution"] = dist_fig.to_json()
    
    return visualizations

def generate_sales_visualizations(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate visualizations for sales data"""
    visualizations = {}
    
    # Check for required columns
    required_cols = ['quantity', 'price', 'product', 'revenue', 'profit']
    if not any(col in df.columns for col in required_cols):
        return generate_generic_visualizations(df)
    
    # 1. Revenue by product/category
    if 'product' in df.columns and 'revenue' in df.columns:
        # Group by product and sum revenue
        product_revenue = df.groupby('product')['revenue'].sum().reset_index()
        product_revenue = product_revenue.sort_values('revenue', ascending=False)
        
        # Create bar chart
        fig = px.bar(
            product_revenue, 
            x='product', 
            y='revenue',
            title='Revenue by Product',
            labels={'product': 'Product', 'revenue': 'Revenue'},
            template='plotly_white',
            color='revenue',
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            yaxis=dict(tickformat=",.0f"),
            xaxis_title="Product",
            yaxis_title="Revenue"
        )
        
        visualizations["product_revenue"] = fig.to_json()
    
    # 2. Profit margin by product
    if 'product' in df.columns and 'profit' in df.columns and 'revenue' in df.columns:
        # Calculate profit margin
        profit_data = df.groupby('product').agg({
            'profit': 'sum',
            'revenue': 'sum'
        }).reset_index()
        
        profit_data['margin'] = profit_data['profit'] / profit_data['revenue'] * 100
        profit_data = profit_data.sort_values('margin', ascending=False)
        
        fig = px.bar(
            profit_data,
            x='product',
            y='margin',
            title='Profit Margin by Product',
            labels={'product': 'Product', 'margin': 'Profit Margin (%)'},
            template='plotly_white',
            color='margin',
            color_continuous_scale='RdYlGn'
        )
        
        fig.update_layout(
            yaxis=dict(tickformat=".2f", ticksuffix="%"),
            xaxis_title="Product",
            yaxis_title="Profit Margin (%)"
        )
        
        visualizations["profit_margin"] = fig.to_json()
    
    # 3. Sales trend over time
    if 'date' in df.columns and any(col in df.columns for col in ['revenue', 'sales', 'quantity']):
        # Determine which metric to use
        metric = next(col for col in ['revenue', 'sales', 'quantity'] if col in df.columns)
        
        # Group by date
        date_col = 'date'
        df[date_col] = pd.to_datetime(df[date_col])
        
        # Aggregate by day
        daily_sales = df.groupby(df[date_col].dt.date)[metric].sum().reset_index()
        
        fig = px.line(
            daily_sales,
            x=date_col,
            y=metric,
            title=f'{metric.capitalize()} Over Time',
            labels={date_col: 'Date', metric: metric.capitalize()},
            template='plotly_white'
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title=metric.capitalize(),
            yaxis=dict(tickformat=",.0f" if metric in ['revenue', 'sales'] else None)
        )
        
        visualizations["sales_trend"] = fig.to_json()
    
    return visualizations

def generate_geographic_visualizations(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate visualizations for geographic data"""
    visualizations = {}
    
    # Check for required columns
    geo_columns = ['country', 'region', 'city', 'state', 'province']
    if not any(col in df.columns for col in geo_columns):
        return generate_generic_visualizations(df)
    
    # 1. Bar chart of metrics by geographic entity
    geo_col = next(col for col in geo_columns if col in df.columns)
    
    # Find numeric columns to visualize
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if numeric_cols:
        metric = numeric_cols[0]  # Use first numeric column by default
        
        # Group by geographic entity and calculate mean of the metric
        geo_metric = df.groupby(geo_col)[metric].mean().reset_index()
        geo_metric = geo_metric.sort_values(metric, ascending=False)
        
        fig = px.bar(
            geo_metric,
            x=geo_col,
            y=metric,
            title=f'{metric} by {geo_col.capitalize()}',
            labels={geo_col: geo_col.capitalize(), metric: metric.capitalize()},
            template='plotly_white',
            color=metric,
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_title=geo_col.capitalize(),
            yaxis_title=metric.capitalize()
        )
        
        visualizations["geo_metric"] = fig.to_json()
    
    # 2. Comparison of multiple metrics across geographic entities
    if len(numeric_cols) >= 2:
        # Select top 5 entities by first metric
        top_entities = df.groupby(geo_col)[numeric_cols[0]].mean().nlargest(5).index.tolist()
        
        # Filter data for these entities and melt for visualization
        top_data = df[df[geo_col].isin(top_entities)].copy()
        melted_data = pd.melt(
            top_data.groupby(geo_col)[numeric_cols[:3]].mean().reset_index(),
            id_vars=[geo_col],
            value_vars=numeric_cols[:3],
            var_name='Metric',
            value_name='Value'
        )
        
        fig = px.bar(
            melted_data,
            x=geo_col,
            y='Value',
            color='Metric',
            barmode='group',
            title=f'Comparison of Metrics by {geo_col.capitalize()}',
            labels={geo_col: geo_col.capitalize(), 'Value': 'Value', 'Metric': 'Metric'},
            template='plotly_white'
        )
        
        fig.update_layout(
            xaxis_title=geo_col.capitalize(),
            yaxis_title="Value"
        )
        
        visualizations["metric_comparison"] = fig.to_json()
    
    return visualizations

def generate_time_series_visualizations(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate visualizations for time series data"""
    visualizations = {}
    
    # Find datetime columns
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    
    if not date_cols:
        return generate_generic_visualizations(df)
    
    # Use the first date column
    date_col = date_cols[0]
    
    # Find numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        return generate_generic_visualizations(df)
    
    # 1. Line chart of numeric values over time
    metrics_to_plot = numeric_cols[:4]  # Plot up to 4 metrics
    
    fig = px.line(
        df,
        x=date_col,
        y=metrics_to_plot,
        title='Time Series Analysis',
        labels={date_col: 'Date'},
        template='plotly_white'
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Value",
        legend_title="Metric"
    )
    
    visualizations["time_series"] = fig.to_json()
    
    # 2. Monthly/yearly aggregation
    if len(df) > 30:  # Only if we have enough data
        df['year'] = df[date_col].dt.year
        df['month'] = df[date_col].dt.month
        
        # Group by year and month
        if df['year'].nunique() > 1:  # Multiple years
            monthly_data = df.groupby(['year', 'month'])[numeric_cols[0]].mean().reset_index()
            monthly_data['period'] = monthly_data['year'].astype(str) + '-' + monthly_data['month'].astype(str)
            
            fig = px.bar(
                monthly_data,
                x='period',
                y=numeric_cols[0],
                title=f'Monthly {numeric_cols[0]} Trends',
                labels={'period': 'Year-Month', numeric_cols[0]: numeric_cols[0]},
                template='plotly_white'
            )
            
            visualizations["monthly_trend"] = fig.to_json()
    
    # 3. Distribution of values
    if numeric_cols:
        dist_fig = make_subplots(
            rows=min(2, len(numeric_cols)), 
            cols=min(2, int(np.ceil(len(numeric_cols[:4])/2))),
            subplot_titles=[f"{col} Distribution" for col in numeric_cols[:4]]
        )
        
        for i, col in enumerate(numeric_cols[:4]):
            row = i // 2 + 1
            col_idx = i % 2 + 1
            
            dist_fig.add_trace(
                go.Histogram(
                    x=df[col],
                    nbinsx=20,
                    marker=dict(color=px.colors.qualitative.Plotly[i])
                ),
                row=row, col=col_idx
            )
        
        dist_fig.update_layout(
            title="Distribution of Metrics",
            showlegend=False,
            template="plotly_white",
            height=600
        )
        
        visualizations["distribution"] = dist_fig.to_json()
    
    return visualizations

def generate_generic_visualizations(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate visualizations for generic data"""
    visualizations = {}
    
    # Find numeric and categorical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # 1. Correlation heatmap for numeric columns
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr()
        
        fig = px.imshow(
            corr,
            text_auto=True,
            title='Correlation Matrix',
            color_continuous_scale='RdBu_r',
            zmin=-1, zmax=1,
            template='plotly_white'
        )
        
        visualizations["correlation"] = fig.to_json()
    
    # 2. Distribution of numeric columns
    if numeric_cols:
        n_cols = min(len(numeric_cols), 4)
        rows = int(np.ceil(n_cols / 2))
        
        dist_fig = make_subplots(
            rows=rows, 
            cols=min(2, n_cols),
            subplot_titles=[f"{col} Distribution" for col in numeric_cols[:n_cols]]
        )
        
        for i, col in enumerate(numeric_cols[:n_cols]):
            row = i // 2 + 1
            col_idx = i % 2 + 1
            
            dist_fig.add_trace(
                go.Histogram(
                    x=df[col],
                    nbinsx=20,
                    marker=dict(color=px.colors.qualitative.Plotly[i])
                ),
                row=row, col=col_idx
            )
        
        dist_fig.update_layout(
            title="Distribution of Numeric Variables",
            showlegend=False,
            template="plotly_white",
            height=600
        )
        
        visualizations["distribution"] = dist_fig.to_json()
    
    # 3. Bar chart for categorical columns
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        
        # Group by categorical column and calculate mean of numeric column
        grouped_data = df.groupby(cat_col)[num_col].mean().reset_index()
        grouped_data = grouped_data.sort_values(num_col, ascending=False)
        
        fig = px.bar(
            grouped_data,
            x=cat_col,
            y=num_col,
            title=f'{num_col} by {cat_col}',
            labels={cat_col: cat_col, num_col: num_col},
            template='plotly_white',
            color=num_col,
            color_continuous_scale='Viridis'
        )
        
        visualizations["categorical_summary"] = fig.to_json()
    
    # 4. Scatter plot if we have multiple numeric columns
    if len(numeric_cols) >= 2:
        # Use first categorical column for color if available
        color_col = categorical_cols[0] if categorical_cols else None
        
        fig = px.scatter(
            df,
            x=numeric_cols[0],
            y=numeric_cols[1],
            color=color_col,
            title=f'{numeric_cols[1]} vs {numeric_cols[0]}',
            labels={
                numeric_cols[0]: numeric_cols[0],
                numeric_cols[1]: numeric_cols[1],
                color_col: color_col if color_col else ""
            },
            template='plotly_white'
        )
        
        visualizations["scatter"] = fig.to_json()
    
    return visualizations

if __name__ == "__main__":
    # Test with different dataset types
    dataset_types = ["financial", "sales", "geographic", "generic"]
    
    for dtype in dataset_types:
        print(f"\nTesting with {dtype} dataset")
        df = load_sample_data(dtype)
        detected_type = detect_dataset_type(df)
        print(f"Detected as: {detected_type}")
        
        visualizations = generate_visualizations(df)
        print(f"Generated {len(visualizations)} visualizations:")
        for viz_name in visualizations.keys():
            print(f"- {viz_name}")
        
        # Create output directory for html files
        os.makedirs(f"visualizations/{dtype}", exist_ok=True)
        
        # Save JSON specs to files for inspection
        with open(f"visualizations/{dtype}/visualization_specs.json", "w") as f:
            import json
            json.dump({k: "<<JSON data>>" for k in visualizations.keys()}, f, indent=2)
    
    print("\nAll visualization tests completed successfully") 