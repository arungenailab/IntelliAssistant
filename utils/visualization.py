import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from datetime import datetime

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
    if data is None or data.empty:
        return None
    
    # Generate a title if not provided
    title = custom_title or f"Visualization of {query_text}"
    
    try:
        # Create different types of visualizations
        if vis_type.lower() == 'bar':
            fig = create_bar_chart(data, title)
        elif vis_type.lower() == 'line':
            fig = create_line_chart(data, title)
        elif vis_type.lower() == 'scatter':
            fig = create_scatter_plot(data, title)
        elif vis_type.lower() == 'pie':
            fig = create_pie_chart(data, title)
        elif vis_type.lower() == 'histogram':
            fig = create_histogram(data, title)
        elif vis_type.lower() == 'heatmap':
            fig = create_heatmap(data, title)
        elif vis_type.lower() == 'box':
            fig = create_box_plot(data, title)
        else:
            # Default to bar chart
            fig = create_bar_chart(data, title)
            vis_type = 'bar'
        
        # Return the visualization result
        return {
            'fig': fig,
            'type': vis_type,
            'title': title,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except Exception as e:
        # If there's an error, try a simpler visualization
        try:
            # Default to a simple bar chart of the first two columns
            cols = data.columns[:2] if len(data.columns) >= 2 else data.columns
            fig = px.bar(data, x=cols[0], y=cols[1], title=f"Simplified visualization of {query_text}")
            
            return {
                'fig': fig,
                'type': 'bar',
                'title': f"Simplified visualization of {query_text}",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'error': str(e)
            }
        except:
            # If that fails too, return None
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
    result = []
    for vis_type in vis_types:
        viz = create_visualization(data, vis_type, query_text)
        if viz:
            result.append(viz)
    
    return result

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
        'title': 'Data Analysis Dashboard',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'visualizations': []
    }
    
    for name, df in data_dict.items():
        query = queries.get(name, f"Analysis of {name}") if queries else f"Analysis of {name}"
        best_vis_type = determine_best_visualization(df)
        viz = create_visualization(df, best_vis_type, query, f"Analysis of {name}")
        
        if viz:
            dashboard['visualizations'].append(viz)
    
    return dashboard

def determine_best_visualization(df):
    """
    Determine the best visualization type for a given dataframe.
    
    Args:
        df (DataFrame): The dataframe to visualize
        
    Returns:
        str: Recommended visualization type
    """
    # Check dataframe properties to determine the best visualization
    if df is None or df.empty:
        return 'bar'  # Default
    
    num_rows = len(df)
    num_cols = len(df.columns)
    
    # Get numeric and categorical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    
    num_numeric = len(numeric_cols)
    num_categorical = len(categorical_cols)
    
    # Decision logic for visualization type
    
    # Time series data
    if date_cols and num_numeric >= 1:
        return 'line'
    
    # Few categories, good for pie chart
    if num_categorical == 1 and num_numeric == 1 and df[categorical_cols[0]].nunique() <= 7:
        return 'pie'
    
    # Correlation or relationship between two numeric variables
    if num_numeric >= 2:
        # If many points, scatter plot is good
        if num_rows > 30:
            return 'scatter'
        # For fewer points, a line chart might be better
        else:
            return 'line'
    
    # One numeric and one categorical, bar chart is usually good
    if num_numeric >= 1 and num_categorical >= 1:
        # But if there are too many categories, a box plot might be better
        if df[categorical_cols[0]].nunique() > 10:
            return 'box'
        else:
            return 'bar'
    
    # Distribution of a single numeric variable
    if num_numeric == 1 and num_categorical == 0:
        return 'histogram'
    
    # Correlation matrix for multiple numeric variables
    if num_numeric > 2:
        return 'heatmap'
    
    # Default to bar chart
    return 'bar'

def create_bar_chart(df, title):
    """Create a bar chart from dataframe."""
    # For a bar chart, we need at least one categorical and one numeric column
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(categorical_cols) > 0 and len(numeric_cols) > 0:
        # Use the first categorical column for x-axis and first numeric for y-axis
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        
        # If too many categories, limit to top 10
        if df[x_col].nunique() > 10:
            top_categories = df.groupby(x_col)[y_col].sum().nlargest(10).index
            filtered_df = df[df[x_col].isin(top_categories)]
            fig = px.bar(filtered_df, x=x_col, y=y_col, title=title)
            fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)
        else:
            fig = px.bar(df, x=x_col, y=y_col, title=title)
            fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)
    elif len(numeric_cols) >= 2:
        # If no categorical columns, use the first numeric column for x and second for y
        fig = px.bar(df, x=numeric_cols[0], y=numeric_cols[1], title=title)
        fig.update_layout(xaxis_title=numeric_cols[0], yaxis_title=numeric_cols[1])
    else:
        # If only one column or no valid columns, create a count plot
        if len(df.columns) > 0:
            first_col = df.columns[0]
            count_df = df[first_col].value_counts().reset_index()
            count_df.columns = [first_col, 'count']
            fig = px.bar(count_df, x=first_col, y='count', title=title)
            fig.update_layout(xaxis_title=first_col, yaxis_title='Count')
        else:
            # Empty dataframe
            fig = go.Figure()
            fig.update_layout(title=title)
    
    return fig

def create_line_chart(df, title):
    """Create a line chart from dataframe."""
    # For a line chart, we'd prefer a date/time column and a numeric column
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if date_cols and len(numeric_cols) > 0:
        # Use the first date column for x-axis and first numeric for y-axis
        fig = px.line(df, x=date_cols[0], y=numeric_cols[0], title=title)
        fig.update_layout(xaxis_title=date_cols[0], yaxis_title=numeric_cols[0])
    elif len(numeric_cols) >= 2:
        # If no date columns, use the first numeric column for x and second for y
        fig = px.line(df, x=numeric_cols[0], y=numeric_cols[1], title=title)
        fig.update_layout(xaxis_title=numeric_cols[0], yaxis_title=numeric_cols[1])
    else:
        # If only one numeric column, use index as x-axis
        if len(numeric_cols) > 0:
            fig = px.line(df, y=numeric_cols[0], title=title)
            fig.update_layout(xaxis_title='Index', yaxis_title=numeric_cols[0])
        else:
            # No numeric columns
            fig = go.Figure()
            fig.update_layout(title=title)
    
    return fig

def create_scatter_plot(df, title):
    """Create a scatter plot from dataframe."""
    # For a scatter plot, we need at least two numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) >= 2:
        # Use the first two numeric columns for x and y
        x_col = numeric_cols[0]
        y_col = numeric_cols[1]
        
        # If there's a third numeric column, use it for size
        size_col = numeric_cols[2] if len(numeric_cols) > 2 else None
        
        # If there's a categorical column, use it for color
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        color_col = categorical_cols[0] if len(categorical_cols) > 0 else None
        
        if size_col and color_col:
            fig = px.scatter(df, x=x_col, y=y_col, size=size_col, color=color_col, title=title)
        elif color_col:
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title)
        elif size_col:
            fig = px.scatter(df, x=x_col, y=y_col, size=size_col, title=title)
        else:
            fig = px.scatter(df, x=x_col, y=y_col, title=title)
        
        fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)
    else:
        # Not enough numeric columns
        fig = go.Figure()
        fig.update_layout(title=title)
    
    return fig

def create_pie_chart(df, title):
    """Create a pie chart from dataframe."""
    # For a pie chart, we need one categorical and one numeric column
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(categorical_cols) > 0 and len(numeric_cols) > 0:
        # Use the first categorical column for names and first numeric for values
        names_col = categorical_cols[0]
        values_col = numeric_cols[0]
        
        # If too many categories, limit to top 8
        if df[names_col].nunique() > 8:
            # Group data by category and sum values
            grouped_df = df.groupby(names_col)[values_col].sum().reset_index()
            
            # Get top 7 categories
            top_categories = grouped_df.sort_values(values_col, ascending=False).head(7)
            
            # Create "Other" category for the rest
            other_value = grouped_df[~grouped_df[names_col].isin(top_categories[names_col])][values_col].sum()
            other_df = pd.DataFrame({names_col: ['Other'], values_col: [other_value]})
            
            # Combine top categories with "Other"
            plot_df = pd.concat([top_categories, other_df])
            
            fig = px.pie(plot_df, names=names_col, values=values_col, title=title)
        else:
            # Group data by category and sum values
            grouped_df = df.groupby(names_col)[values_col].sum().reset_index()
            fig = px.pie(grouped_df, names=names_col, values=values_col, title=title)
    elif len(categorical_cols) > 0:
        # If only categorical columns, use value counts
        count_df = df[categorical_cols[0]].value_counts().reset_index()
        count_df.columns = [categorical_cols[0], 'count']
        
        # If too many categories, limit to top 8
        if count_df.shape[0] > 8:
            top_categories = count_df.head(7)
            other_value = count_df.iloc[7:]['count'].sum()
            other_df = pd.DataFrame({categorical_cols[0]: ['Other'], 'count': [other_value]})
            plot_df = pd.concat([top_categories, other_df])
            fig = px.pie(plot_df, names=categorical_cols[0], values='count', title=title)
        else:
            fig = px.pie(count_df, names=categorical_cols[0], values='count', title=title)
    else:
        # No suitable columns
        fig = go.Figure()
        fig.update_layout(title=title)
    
    return fig

def create_histogram(df, title):
    """Create a histogram from dataframe."""
    # For a histogram, we need at least one numeric column
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) > 0:
        # Use the first numeric column
        x_col = numeric_cols[0]
        
        # If there's a categorical column, use it for color
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        color_col = categorical_cols[0] if len(categorical_cols) > 0 else None
        
        if color_col:
            fig = px.histogram(df, x=x_col, color=color_col, title=title)
        else:
            fig = px.histogram(df, x=x_col, title=title)
        
        fig.update_layout(xaxis_title=x_col, yaxis_title='Count')
    else:
        # No numeric columns
        fig = go.Figure()
        fig.update_layout(title=title)
    
    return fig

def create_heatmap(df, title):
    """Create a heatmap from dataframe."""
    # For a heatmap, we need numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) > 1:
        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr()
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu_r',
            zmin=-1, zmax=1
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Features',
            yaxis_title='Features',
            height=600,
            width=800
        )
    else:
        # Not enough numeric columns
        fig = go.Figure()
        fig.update_layout(title=title)
    
    return fig

def create_box_plot(df, title):
    """Create a box plot from dataframe."""
    # For a box plot, we need one numeric column and possibly one categorical
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    
    if len(numeric_cols) > 0:
        # Use the first numeric column for y-axis
        y_col = numeric_cols[0]
        
        if len(categorical_cols) > 0:
            # Use the first categorical column for x-axis
            x_col = categorical_cols[0]
            
            # If too many categories, limit to top 10
            if df[x_col].nunique() > 10:
                top_categories = df[x_col].value_counts().nlargest(10).index
                filtered_df = df[df[x_col].isin(top_categories)]
                fig = px.box(filtered_df, x=x_col, y=y_col, title=title)
            else:
                fig = px.box(df, x=x_col, y=y_col, title=title)
        else:
            # No categorical column, use just the numeric column
            fig = px.box(df, y=y_col, title=title)
        
        if len(categorical_cols) > 0:
            fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)
        else:
            fig.update_layout(yaxis_title=y_col)
    else:
        # No numeric columns
        fig = go.Figure()
        fig.update_layout(title=title)
    
    return fig