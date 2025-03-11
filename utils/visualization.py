import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import re

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
    if data is None or not isinstance(data, pd.DataFrame) or data.empty:
        return None
    
    # Detect numeric and categorical columns
    numeric_cols = data.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()
    # Date columns might be datetime or objects that can be converted
    date_cols = []
    for col in data.columns:
        try:
            if pd.api.types.is_datetime64_any_dtype(data[col]):
                date_cols.append(col)
            elif col not in numeric_cols and pd.to_datetime(data[col], errors='coerce').notna().all():
                date_cols.append(col)
        except:
            continue
    
    # Set default title
    if custom_title:
        title = custom_title
    else:
        title = f"{vis_type.capitalize()} visualization of data"
    
    # Normalize visualization type
    vis_type = vis_type.lower()
    
    # Extract relevant columns from query text
    mentioned_cols = [col for col in data.columns if col.lower() in query_text.lower()]
    
    # Select x and y axes
    x_col = None
    y_cols = []
    
    # Try to determine relevant columns for the visualization
    if date_cols and (vis_type == 'line' or vis_type == 'time series' or 'trend' in query_text.lower()):
        # For time series, use date as x-axis
        x_col = date_cols[0]
        y_cols = [col for col in numeric_cols if col != x_col]
    elif categorical_cols and numeric_cols:
        # For categorical vs numeric visualizations
        x_col = categorical_cols[0]
        y_cols = [col for col in numeric_cols if col != x_col]
    elif len(numeric_cols) >= 2:
        # For numeric vs numeric visualizations
        x_col = numeric_cols[0]
        y_cols = [col for col in numeric_cols if col != x_col]
    elif len(numeric_cols) == 1 and categorical_cols:
        # Special case for single numeric column
        x_col = categorical_cols[0]
        y_cols = numeric_cols
    
    # Prioritize columns mentioned in the query
    for col in mentioned_cols:
        if col in numeric_cols:
            if not y_cols or col not in y_cols:
                y_cols = [col] + [c for c in y_cols if c != col]
        elif col in categorical_cols or col in date_cols:
            x_col = col
    
    # Limit to top 5 y columns
    y_cols = y_cols[:5]
    
    # Create the appropriate visualization
    try:
        if vis_type in ['bar', 'column']:
            # Use the first categorical column as x if available, otherwise first column
            if x_col is None:
                x_col = data.columns[0]
            
            # Use first numeric column as y if available, otherwise count
            if not y_cols and numeric_cols:
                y_cols = [numeric_cols[0]]
            
            if not y_cols:
                # Count records by x_col
                fig = px.bar(
                    data.groupby(x_col).size().reset_index(name='count'),
                    x=x_col,
                    y='count',
                    title=title
                )
            else:
                fig = px.bar(
                    data,
                    x=x_col,
                    y=y_cols[0],  # Use first y column
                    title=title,
                    color=categorical_cols[1] if len(categorical_cols) > 1 else None
                )
            
            return {"fig": fig, "type": "bar", "x": x_col, "y": y_cols[0]}
        
        elif vis_type in ['line', 'time series', 'trend']:
            if x_col is None:
                # Try to find a suitable x column
                if date_cols:
                    x_col = date_cols[0]
                elif len(data.columns) > 1:
                    x_col = data.columns[0]
                else:
                    # Create a sequence
                    data = data.reset_index()
                    x_col = 'index'
            
            if not y_cols and numeric_cols:
                y_cols = [numeric_cols[0]]
            
            if not y_cols:
                y_cols = ['value']
                # Melt the dataframe for visualization
                id_vars = [x_col]
                value_vars = [col for col in data.columns if col != x_col]
                data = pd.melt(data, id_vars=id_vars, value_vars=value_vars, var_name='variable', value_name='value')
                fig = px.line(
                    data,
                    x=x_col,
                    y='value',
                    color='variable',
                    title=title
                )
            else:
                fig = px.line(
                    data,
                    x=x_col,
                    y=y_cols,
                    title=title
                )
            
            return {"fig": fig, "type": "line", "x": x_col, "y": y_cols}
        
        elif vis_type in ['scatter', 'point']:
            if len(numeric_cols) < 2:
                # Not enough numeric columns for scatter
                return create_visualization(data, 'bar', query_text, custom_title)
            
            if x_col is None or x_col not in numeric_cols:
                x_col = numeric_cols[0]
            
            if not y_cols:
                y_cols = [numeric_cols[1]]
            
            fig = px.scatter(
                data,
                x=x_col,
                y=y_cols[0],  # Use first y column
                title=title,
                color=categorical_cols[0] if categorical_cols else None,
                size=numeric_cols[2] if len(numeric_cols) > 2 else None
            )
            
            return {"fig": fig, "type": "scatter", "x": x_col, "y": y_cols[0]}
        
        elif vis_type in ['pie', 'donut']:
            if not categorical_cols:
                # Create categories by binning a numeric column
                if numeric_cols:
                    bins = min(10, data[numeric_cols[0]].nunique())
                    data['binned'] = pd.cut(data[numeric_cols[0]], bins=bins)
                    categorical_cols = ['binned']
                else:
                    # Not suitable for pie chart
                    return create_visualization(data, 'bar', query_text, custom_title)
            
            values_col = numeric_cols[0] if numeric_cols else 'count'
            
            if values_col == 'count':
                # Count by category
                pie_data = data.groupby(categorical_cols[0]).size().reset_index(name='count')
                fig = px.pie(
                    pie_data,
                    names=categorical_cols[0],
                    values='count',
                    title=title
                )
            else:
                # Sum values by category
                pie_data = data.groupby(categorical_cols[0])[values_col].sum().reset_index()
                fig = px.pie(
                    pie_data,
                    names=categorical_cols[0],
                    values=values_col,
                    title=title
                )
            
            if vis_type == 'donut':
                fig.update_traces(hole=0.4)
            
            return {"fig": fig, "type": "pie", "names": categorical_cols[0], "values": values_col}
        
        elif vis_type in ['histogram']:
            if not numeric_cols:
                # Not suitable for histogram
                return create_visualization(data, 'bar', query_text, custom_title)
            
            target_col = y_cols[0] if y_cols else numeric_cols[0]
            
            fig = px.histogram(
                data,
                x=target_col,
                title=title,
                color=categorical_cols[0] if categorical_cols else None
            )
            
            return {"fig": fig, "type": "histogram", "x": target_col}
        
        elif vis_type in ['heatmap', 'correlation']:
            if len(numeric_cols) < 2:
                # Not enough numeric columns for heatmap
                return create_visualization(data, 'bar', query_text, custom_title)
            
            # Create correlation matrix
            corr_matrix = data[numeric_cols].corr()
            
            fig = px.imshow(
                corr_matrix,
                title=title or 'Correlation Matrix',
                color_continuous_scale='RdBu_r',
                zmin=-1,
                zmax=1
            )
            
            return {"fig": fig, "type": "heatmap"}
        
        elif vis_type in ['box', 'boxplot']:
            if not numeric_cols:
                # Not suitable for boxplot
                return create_visualization(data, 'bar', query_text, custom_title)
            
            target_col = y_cols[0] if y_cols else numeric_cols[0]
            category_col = x_col if x_col in categorical_cols else (categorical_cols[0] if categorical_cols else None)
            
            fig = px.box(
                data,
                y=target_col,
                x=category_col,
                title=title,
                color=categorical_cols[1] if category_col and len(categorical_cols) > 1 else None
            )
            
            return {"fig": fig, "type": "box", "y": target_col, "x": category_col}
        
        elif vis_type in ['violin']:
            if not numeric_cols:
                # Not suitable for violin plot
                return create_visualization(data, 'bar', query_text, custom_title)
            
            target_col = y_cols[0] if y_cols else numeric_cols[0]
            category_col = x_col if x_col in categorical_cols else (categorical_cols[0] if categorical_cols else None)
            
            fig = px.violin(
                data,
                y=target_col,
                x=category_col,
                title=title,
                color=categorical_cols[1] if category_col and len(categorical_cols) > 1 else None,
                box=True
            )
            
            return {"fig": fig, "type": "violin", "y": target_col, "x": category_col}
        
        else:
            # Default to bar chart if visualization type is unknown
            return create_visualization(data, 'bar', query_text, custom_title)
    
    except Exception as e:
        # If visualization creation fails, attempt a simple bar chart
        try:
            # Simple bar chart as fallback
            if len(data.columns) >= 2:
                fig = px.bar(data, x=data.columns[0], y=data.columns[1], title=f"Data visualization ({str(e)})")
                return {"fig": fig, "type": "bar", "error": str(e)}
            else:
                fig = px.bar(data, title=f"Data visualization ({str(e)})")
                return {"fig": fig, "type": "bar", "error": str(e)}
        except:
            # If even the fallback fails, return None
            return None

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
        result = create_visualization(data, vis_type, query_text)
        if result:
            visualizations.append(result)
    
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
    dashboard = {"figures": [], "layout": {}}
    
    # Create a visualization for each dataset
    for name, df in data_dict.items():
        query = queries.get(name, "") if queries else ""
        
        # Determine best visualization type based on data
        vis_type = determine_best_visualization(df)
        
        result = create_visualization(df, vis_type, query, custom_title=name)
        if result:
            dashboard["figures"].append({
                "name": name,
                "figure": result["fig"],
                "type": result["type"]
            })
    
    # Create a grid layout
    cols = min(2, len(dashboard["figures"]))
    rows = (len(dashboard["figures"]) + cols - 1) // cols
    
    dashboard["layout"] = {
        "grid": {"rows": rows, "columns": cols},
        "height": rows * 400  # 400px per row
    }
    
    return dashboard

def determine_best_visualization(df):
    """
    Determine the best visualization type for a given dataframe.
    
    Args:
        df (DataFrame): The dataframe to visualize
        
    Returns:
        str: Recommended visualization type
    """
    if df is None or df.empty:
        return "bar"  # Default
    
    # Detect column types
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = []
    for col in df.columns:
        try:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_cols.append(col)
            elif col not in numeric_cols and pd.to_datetime(df[col], errors='coerce').notna().all():
                date_cols.append(col)
        except:
            continue
    
    # Count unique values in categorical columns
    cat_unique_counts = {col: df[col].nunique() for col in categorical_cols if col in df.columns}
    
    # Time series
    if date_cols and numeric_cols:
        return "line"
    
    # Few categories with numeric values
    if categorical_cols and numeric_cols and any(count <= 10 for count in cat_unique_counts.values()):
        return "bar"
    
    # Many categories with numeric values
    if categorical_cols and numeric_cols and any(count > 10 for count in cat_unique_counts.values()):
        # For many categories, horizontal bar might be better
        if max(cat_unique_counts.values(), default=0) > 15:
            return "bar"  # Plotly automatically handles orientation
        return "bar"
    
    # Correlation between numeric columns
    if len(numeric_cols) > 5:
        return "heatmap"
    
    # Scatter plot for two numeric columns
    if len(numeric_cols) >= 2:
        return "scatter"
    
    # Pie chart for a categorical column with few unique values
    if categorical_cols and (len(categorical_cols) == 1 or df[categorical_cols[0]].nunique() <= 7):
        return "pie"
    
    # Distribution of a numeric column
    if numeric_cols:
        return "histogram"
    
    # Default to bar chart
    return "bar"
