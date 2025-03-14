import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import traceback
import numpy as np

def create_visualization(data, plot_type, user_query=None, params=None):
    """
    Create a visualization based on the data and parameters.
    
    Args:
        data (pd.DataFrame): The data to visualize
        plot_type (str): The type of plot to create (bar, line, scatter, etc.)
        user_query (str, optional): The user's query
        params (dict, optional): Parameters for the visualization
        
    Returns:
        dict: The visualization data
    """
    try:
        # Default parameters
        x = params.get('x')
        y = params.get('y')
        color = params.get('color')
        facet = params.get('facet')
        title = params.get('title', f"{plot_type.capitalize()} Chart")
        orientation = params.get('orientation', 'vertical')
        aggregation = params.get('aggregation')
        top_n = params.get('top_n')
        sort_by = params.get('sort_by', y)
        ascending = params.get('ascending', False)
        show_values = params.get('show_values', True)
        value_position = params.get('value_position', 'auto')
        marker_color = params.get('marker_color', '#3366ff')
        tick_angle = params.get('tick_angle', -45)
        font_family = params.get('font_family', 'Arial, sans-serif')
        base_font_size = params.get('base_font_size', 14)
        title_font_size = params.get('title_font_size', 18)
        
        # Legend position
        legend_position = params.get('legend_position', {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'right',
            'x': 1
        })
        
        # Margins
        margins = params.get('margins', {
            't': 50,
            'l': 50,
            'r': 50,
            'b': 100
        })
        
        # If data parameter is provided in params, use it directly
        if 'data' in params:
            print("[DEBUG] Using data from params")
            # Extract the data from params but ensure we still have the original data for processing
            params_data = params.get('data')
            
            # Create the visualization
            print(f"Creating {plot_type} plot")
            
            # Create result with the provided data
            result = {
                'type': plot_type,
                'title': title,
                'data': params_data
            }
            print("Creating visualization result")
            print("Successfully created visualization")
            return result
        
        # Debug information
        print(f"[DEBUG] Plot type: {plot_type}")
        print(f"[DEBUG] Data shape: {data.shape}")
        print(f"[DEBUG] Data columns: {data.columns.tolist()}")
        print(f"[DEBUG] Parameters: {params}")
        print(f"[DEBUG] Using columns - x: {x}, y: {y}, color: {color}, facet: {facet}")
        
        # Process data based on parameters
        plot_data = data.copy()
        
        # Aggregate data if needed
        if aggregation and x and y:
            print(f"[DEBUG] Aggregating data with method: {aggregation}")
            if aggregation == 'sum':
                plot_data = data.groupby(x)[y].sum().reset_index()
            elif aggregation == 'mean':
                plot_data = data.groupby(x)[y].mean().reset_index()
            elif aggregation == 'count':
                plot_data = data.groupby(x)[y].count().reset_index()
            elif aggregation == 'min':
                plot_data = data.groupby(x)[y].min().reset_index()
            elif aggregation == 'max':
                plot_data = data.groupby(x)[y].max().reset_index()
            
            # Sort data
            if sort_by:
                plot_data = plot_data.sort_values(by=sort_by, ascending=ascending)
            
            # Take top N if specified
            if top_n and top_n > 0:
                plot_data = plot_data.head(top_n)
            
            print(f"[DEBUG] Processed data shape: {plot_data.shape}")
        else:
            plot_data = data
        
        # Create the visualization
        print(f"Creating {plot_type} plot")
        
        # Convert data to format expected by react-plotly.js
        plot_data_list = []
        
        if plot_type == 'bar':
            trace = {
                'type': 'bar',
                'name': y.replace('_', ' ').title() if y else 'Value',
                'orientation': 'v' if orientation == 'vertical' else 'h',
                'marker': {
                    'color': marker_color
                }
            }
            
            # Only add x and y data if they are provided
            if x is not None and y is not None:
                if orientation == 'vertical':
                    trace['x'] = plot_data[x].tolist()
                    trace['y'] = plot_data[y].tolist()
                else:
                    trace['x'] = plot_data[y].tolist()
                    trace['y'] = plot_data[x].tolist()
                
                # Add value labels if requested
                if show_values:
                    trace['text'] = plot_data[y].round(0).astype(int).tolist()
                    trace['textposition'] = value_position
            
            plot_data_list.append(trace)
        
        # Create layout with dynamic configuration
        layout = {
            'title': title,
            'showlegend': True,
            'legend': legend_position,
            'margin': margins,
            'xaxis': {
                'title': x.replace('_', ' ').title() if x else '',
                'tickangle': tick_angle if orientation == 'vertical' else 0,
                'automargin': True
            },
            'yaxis': {
                'title': y.replace('_', ' ').title() if y else '',
                'automargin': True
            },
            'hovermode': 'closest',
            'font': {
                'family': font_family,
                'size': base_font_size
            },
            'titlefont': {
                'family': font_family,
                'size': title_font_size
            }
        }
        
        # Add color axis if color parameter is provided
        if color and color in data.columns:
            layout['coloraxis'] = {'colorbar': {'title': color.replace('_', ' ').title()}}
        
        print("Creating visualization result")
        
        # Ensure all data is JSON serializable
        for i, trace in enumerate(plot_data_list):
            # Convert any datetime values to strings
            if 'x' in trace and isinstance(trace['x'], (list, pd.Series, np.ndarray)):
                plot_data_list[i]['x'] = [str(val) if pd.api.types.is_datetime64_dtype(pd.Series([val])) or 
                                         isinstance(val, (pd.Timestamp, np.datetime64)) else val 
                                         for val in trace['x']]
            
            if 'y' in trace and isinstance(trace['y'], (list, pd.Series, np.ndarray)):
                plot_data_list[i]['y'] = [float(val) if isinstance(val, (int, float, np.number)) else str(val) 
                                         for val in trace['y']]
        
        result = {
            'type': plot_type,
            'title': title,
            'data': {
                'data': plot_data_list,
                'layout': layout,
                'config': {
                    'displayModeBar': True,
                    'displaylogo': False,
                    'responsive': True,
                    'scrollZoom': True
                }
            }
        }
        print("Successfully created visualization")
        return result
        
    except Exception as e:
        print(f"Error creating visualization: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return None 