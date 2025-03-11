import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Union

def create_visualization(data, vis_type, query_text, custom_title=None):
    """
    Create a visualization based on the data and type.
    
    Args:
        data (DataFrame): The data to visualize
        vis_type (str): Type of visualization
        query_text (str): Text of the original query for context
        custom_title (str, optional): Custom title for the visualization
        
    Returns:
        dict: Visualization result containing the figure and metadata
    """
    # Determine visualization type if not specified
    if not vis_type or vis_type.lower() == 'auto':
        vis_type = determine_best_visualization(data)
    
    # Generate a title based on the query if not provided
    if not custom_title:
        custom_title = generate_title_from_query(query_text, vis_type)
    
    # Create the visualization
    if vis_type.lower() in ['bar', 'barplot', 'bar chart']:
        fig = create_bar_chart(data, custom_title)
    elif vis_type.lower() in ['line', 'lineplot', 'line chart']:
        fig = create_line_chart(data, custom_title)
    elif vis_type.lower() in ['scatter', 'scatterplot']:
        fig = create_scatter_plot(data, custom_title)
    elif vis_type.lower() in ['pie', 'piechart', 'pie chart']:
        fig = create_pie_chart(data, custom_title)
    elif vis_type.lower() in ['histogram', 'hist']:
        fig = create_histogram(data, custom_title)
    elif vis_type.lower() in ['heatmap', 'heat map']:
        fig = create_heatmap(data, custom_title)
    elif vis_type.lower() in ['box', 'boxplot', 'box plot']:
        fig = create_box_plot(data, custom_title)
    else:
        # Default to bar chart if type is not recognized
        fig = create_bar_chart(data, custom_title)
        vis_type = 'bar'
    
    # Return the visualization with metadata
    return {
        "fig": fig,
        "type": vis_type,
        "title": custom_title,
        "data_shape": data.shape
    }

def create_multi_visualization(data, vis_types, query_text):
    """
    Create multiple visualizations from the same data.
    
    Args:
        data (DataFrame): The data to visualize
        vis_types (list): List of visualization types to create
        query_text (str): Text of the original query for context
        
    Returns:
        list: List of visualization results
    """
    visualizations = []
    
    for vis_type in vis_types:
        visualizations.append(create_visualization(data, vis_type, query_text))
    
    return visualizations

def create_dashboard(data_dict, queries=None):
    """
    Create a dashboard with multiple visualizations from different datasets.
    
    Args:
        data_dict (dict): Dictionary of {name: dataframe} pairs
        queries (dict, optional): Dictionary of {name: query} that generated each dataframe
        
    Returns:
        dict: Dashboard configuration with figures
    """
    dashboard = {
        "title": "Data Analysis Dashboard",
        "visualizations": []
    }
    
    for name, df in data_dict.items():
        # Skip empty dataframes
        if df.empty:
            continue
        
        # Determine best visualization for this dataset
        vis_type = determine_best_visualization(df)
        
        # Get associated query if available
        query = queries.get(name, f"Analysis of {name}") if queries else f"Analysis of {name}"
        
        # Create visualization
        visualization = create_visualization(df, vis_type, query, custom_title=name)
        
        # Add to dashboard
        dashboard["visualizations"].append({
            "name": name,
            "visualization": visualization
        })
    
    return dashboard

def determine_best_visualization(df):
    """
    Determine the best visualization type for a given dataframe.
    
    Args:
        df (DataFrame): The dataframe to visualize
        
    Returns:
        str: Recommended visualization type
    """
    # Check dataframe size
    num_rows, num_cols = df.shape
    
    # Get numeric and categorical columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
    
    # Count column types
    num_numeric = len(numeric_cols)
    num_categorical = len(categorical_cols)
    num_datetime = len(datetime_cols)
    
    # Logic to determine visualization type
    if num_rows == 0 or num_cols == 0:
        return "table"  # Empty data, just show as table
    
    # Time series detection
    if num_datetime > 0 and num_numeric > 0:
        return "line"  # Time series data
    
    # Distribution analysis
    if num_numeric == 1 and num_categorical == 0:
        return "histogram"  # Single numeric column
    
    # Correlation analysis
    if num_numeric >= 2 and num_categorical == 0:
        return "scatter"  # Multiple numeric columns
    
    # Categorical data
    if num_numeric == 1 and num_categorical == 1:
        if df[categorical_cols[0]].nunique() <= 10:
            return "bar"  # One category with reasonable number of values
        else:
            return "box"  # One category with many values
    
    # Composition analysis
    if num_numeric == 1 and num_categorical == 1:
        if df[categorical_cols[0]].nunique() <= 7 and num_rows <= 20:
            return "pie"  # Small number of categories for pie chart
    
    # Multiple categories
    if num_categorical >= 2 and num_numeric >= 1:
        return "heatmap"  # Show relationships between categories
    
    # Default case
    if num_numeric >= 1:
        return "bar"  # Default to bar chart for numeric data
    else:
        return "table"  # Default to table for non-numeric data

def generate_title_from_query(query, vis_type):
    """Generate a title based on the query and visualization type."""
    # Clean the query
    query = query.strip()
    
    # Remove common prefixes
    prefixes = ["show me", "display", "visualize", "plot", "graph", "create a", "generate a"]
    for prefix in prefixes:
        if query.lower().startswith(prefix):
            query = query[len(prefix):].strip()
    
    # Capitalize first letter
    if query:
        query = query[0].upper() + query[1:]
    
    # Add visualization type if not in query
    if vis_type.lower() not in query.lower():
        return f"{query} ({vis_type.capitalize()} Chart)"
    else:
        return query

def create_bar_chart(df, title):
    """Create a bar chart from dataframe."""
    # Identify potential x and y columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Default columns
    if categorical_cols and numeric_cols:
        x_col = categorical_cols[0]  # First categorical column as x-axis
        y_col = numeric_cols[0]  # First numeric column as y-axis
    elif len(numeric_cols) >= 2:
        x_col = numeric_cols[0]  # First numeric column as x-axis
        y_col = numeric_cols[1]  # Second numeric column as y-axis
    elif numeric_cols and len(df.columns) >= 2:
        x_col = df.columns[0] if df.columns[0] != numeric_cols[0] else df.columns[1]  # Non-numeric column as x-axis
        y_col = numeric_cols[0]  # Numeric column as y-axis
    else:
        # Fallback if we can't determine appropriate columns
        x_col = df.columns[0]
        y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # Check for color column (if there's a second categorical column)
    color_col = None
    if len(categorical_cols) > 1 and categorical_cols[0] != x_col:
        color_col = categorical_cols[0]
    elif len(categorical_cols) > 1:
        color_col = categorical_cols[1]
    
    # Create the bar chart
    try:
        if color_col:
            fig = px.bar(df, x=x_col, y=y_col, color=color_col, title=title)
        else:
            fig = px.bar(df, x=x_col, y=y_col, title=title)
        
        # Format the layout
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            template="plotly_white"
        )
        
        return fig
    except Exception as e:
        # Fallback to a simpler chart if there's an error
        print(f"Error creating bar chart: {str(e)}")
        fig = px.bar(df, title=title)
        return fig

def create_line_chart(df, title):
    """Create a line chart from dataframe."""
    # Identify potential x and y columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime']).columns.tolist()
    
    # Default columns
    if datetime_cols and numeric_cols:
        x_col = datetime_cols[0]  # First datetime column as x-axis
        y_col = numeric_cols[0]  # First numeric column as y-axis
    elif len(numeric_cols) >= 2:
        x_col = numeric_cols[0]  # First numeric column as x-axis
        y_col = numeric_cols[1]  # Second numeric column as y-axis
    elif numeric_cols and len(df.columns) >= 2:
        x_col = df.columns[0] if df.columns[0] != numeric_cols[0] else df.columns[1]  # Non-numeric column as x-axis
        y_col = numeric_cols[0]  # Numeric column as y-axis
    else:
        # Fallback if we can't determine appropriate columns
        x_col = df.columns[0]
        y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # Check for color column (if there's a categorical column)
    color_col = categorical_cols[0] if categorical_cols else None
    
    # Create the line chart
    try:
        if color_col:
            fig = px.line(df, x=x_col, y=y_col, color=color_col, title=title)
        else:
            fig = px.line(df, x=x_col, y=y_col, title=title)
        
        # Format the layout
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            template="plotly_white"
        )
        
        return fig
    except Exception as e:
        # Fallback to a simpler chart if there's an error
        print(f"Error creating line chart: {str(e)}")
        fig = px.line(df, title=title)
        return fig

def create_scatter_plot(df, title):
    """Create a scatter plot from dataframe."""
    # Identify potential x and y columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Default columns
    if len(numeric_cols) >= 2:
        x_col = numeric_cols[0]  # First numeric column as x-axis
        y_col = numeric_cols[1]  # Second numeric column as y-axis
    elif numeric_cols and len(df.columns) >= 2:
        x_col = df.columns[0] if df.columns[0] != numeric_cols[0] else df.columns[1]  # Non-numeric column as x-axis
        y_col = numeric_cols[0]  # Numeric column as y-axis
    else:
        # Fallback if we can't determine appropriate columns
        x_col = df.columns[0]
        y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # Check for color column and size column
    color_col = categorical_cols[0] if categorical_cols else None
    size_col = numeric_cols[2] if len(numeric_cols) > 2 else None
    
    # Create the scatter plot
    try:
        if color_col and size_col:
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col, size=size_col, title=title)
        elif color_col:
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title)
        elif size_col:
            fig = px.scatter(df, x=x_col, y=y_col, size=size_col, title=title)
        else:
            fig = px.scatter(df, x=x_col, y=y_col, title=title)
        
        # Format the layout
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            template="plotly_white"
        )
        
        return fig
    except Exception as e:
        # Fallback to a simpler chart if there's an error
        print(f"Error creating scatter plot: {str(e)}")
        fig = px.scatter(df, title=title)
        return fig

def create_pie_chart(df, title):
    """Create a pie chart from dataframe."""
    # Identify potential name and value columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Default columns
    if categorical_cols and numeric_cols:
        names = categorical_cols[0]  # First categorical column for names
        values = numeric_cols[0]  # First numeric column for values
    elif len(df.columns) >= 2:
        names = df.columns[0]  # First column for names
        values = df.columns[1]  # Second column for values
    else:
        # Fallback if we can't determine appropriate columns
        names = df.index.name or 'index'
        values = df.columns[0]
        df = df.reset_index()
    
    # Create the pie chart
    try:
        fig = px.pie(df, names=names, values=values, title=title)
        
        # Format the layout
        fig.update_layout(
            template="plotly_white"
        )
        
        return fig
    except Exception as e:
        # Fallback to a simpler chart if there's an error
        print(f"Error creating pie chart: {str(e)}")
        fig = px.pie(df, title=title)
        return fig

def create_histogram(df, title):
    """Create a histogram from dataframe."""
    # Identify potential column for histogram
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    # Default column
    if numeric_cols:
        x_col = numeric_cols[0]  # First numeric column for histogram
    else:
        # Fallback if we can't determine appropriate column
        x_col = df.columns[0]
    
    # Check for color column
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    color_col = categorical_cols[0] if categorical_cols else None
    
    # Create the histogram
    try:
        if color_col:
            fig = px.histogram(df, x=x_col, color=color_col, title=title)
        else:
            fig = px.histogram(df, x=x_col, title=title)
        
        # Format the layout
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title="Count",
            template="plotly_white"
        )
        
        return fig
    except Exception as e:
        # Fallback to a simpler chart if there's an error
        print(f"Error creating histogram: {str(e)}")
        fig = px.histogram(df, title=title)
        return fig

def create_heatmap(df, title):
    """Create a heatmap from dataframe."""
    # For a heatmap, we need a pivot table or correlation matrix
    try:
        # If we have numeric columns, create a correlation matrix
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(numeric_cols) >= 2:
            corr_df = df[numeric_cols].corr()
            fig = go.Figure(data=go.Heatmap(
                z=corr_df.values,
                x=corr_df.columns,
                y=corr_df.columns,
                colorscale='Viridis'
            ))
            fig.update_layout(title=title + " (Correlation Matrix)")
        else:
            # If we have categorical columns, try to create a pivot table
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            if len(categorical_cols) >= 2 and numeric_cols:
                pivot_df = pd.pivot_table(
                    df, 
                    values=numeric_cols[0], 
                    index=categorical_cols[0], 
                    columns=categorical_cols[1], 
                    aggfunc='mean'
                )
                fig = go.Figure(data=go.Heatmap(
                    z=pivot_df.values,
                    x=pivot_df.columns,
                    y=pivot_df.index,
                    colorscale='Viridis'
                ))
                fig.update_layout(title=title)
            else:
                # If we can't create a meaningful heatmap, fallback to a basic heatmap
                fig = go.Figure(data=go.Heatmap(
                    z=df.values,
                    x=df.columns,
                    y=df.index,
                    colorscale='Viridis'
                ))
                fig.update_layout(title=title)
        
        # Format the layout
        fig.update_layout(
            template="plotly_white"
        )
        
        return fig
    except Exception as e:
        # Fallback to a simpler chart if there's an error
        print(f"Error creating heatmap: {str(e)}")
        fig = px.imshow(df.corr() if len(df.select_dtypes(include=['number']).columns) > 1 else df, title=title)
        return fig

def create_box_plot(df, title):
    """Create a box plot from dataframe."""
    # Identify potential columns for box plot
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Default columns
    if numeric_cols and categorical_cols:
        y = numeric_cols[0]  # First numeric column for values
        x = categorical_cols[0]  # First categorical column for categories
    elif numeric_cols:
        y = numeric_cols[0]  # First numeric column for values
        x = None  # No categories
    else:
        # Fallback if we can't determine appropriate columns
        y = df.columns[0]
        x = None
    
    # Check for color column
    color_col = categorical_cols[0] if categorical_cols else None
    
    # Create the box plot
    try:
        if x and color_col and x != color_col:
            fig = px.box(df, x=x, y=y, color=color_col, title=title)
        elif x:
            fig = px.box(df, x=x, y=y, title=title)
        else:
            fig = px.box(df, y=y, title=title)
        
        # Format the layout
        fig.update_layout(
            yaxis_title=y,
            template="plotly_white"
        )
        if x:
            fig.update_layout(xaxis_title=x)
        
        return fig
    except Exception as e:
        # Fallback to a simpler chart if there's an error
        print(f"Error creating box plot: {str(e)}")
        fig = px.box(df, title=title)
        return fig