import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import traceback

def create_visualization(data, plot_type, query, params=None):
    """
    Create a visualization using Plotly based on the provided parameters.
    
    Args:
        data (pd.DataFrame): Input data
        plot_type (str): Type of plot to create
        query (str): User's query
        params (dict): Additional visualization parameters
        
    Returns:
        dict: Visualization configuration and data
    """
    try:
        print(f"Creating visualization with type: {plot_type}")
        print(f"Data shape: {data.shape}")
        print(f"Parameters: {params}")
        
        if params is None:
            params = {}
        
        # Extract parameters
        x = params.get('x')
        y = params.get('y')
        color = params.get('color')
        facet = params.get('facet')
        title = params.get('title', 'Data Visualization')
        orientation = params.get('orientation', 'vertical')
        aggregation = params.get('aggregation', 'sum')
        
        print(f"Using columns - x: {x}, y: {y}, color: {color}, facet: {facet}")
        
        # Prepare the data
        if aggregation and x and y:
            print(f"Aggregating data with method: {aggregation}")
            if aggregation == 'sum':
                plot_data = data.groupby(x)[y].sum().reset_index()
            elif aggregation == 'mean':
                plot_data = data.groupby(x)[y].mean().reset_index()
            elif aggregation == 'count':
                plot_data = data.groupby(x)[y].count().reset_index()
            elif aggregation == 'distribution':
                # For distribution plots, we don't aggregate
                plot_data = data
            else:
                plot_data = data
            print(f"Aggregated data shape: {plot_data.shape}")
        else:
            plot_data = data
        
        # Create the visualization
        print(f"Creating {plot_type} plot")
        
        # Convert data to format expected by react-plotly.js
        plot_data_list = []
        
        if plot_type == 'bar':
            if color:
                # Create grouped bar chart
                for group in plot_data[color].unique():
                    group_data = plot_data[plot_data[color] == group]
                    plot_data_list.append({
                        'type': 'bar',
                        'x': group_data[x].tolist(),
                        'y': group_data[y].tolist(),
                        'name': str(group)
                    })
            else:
                plot_data_list = [{
                    'type': 'bar',
                    'x': plot_data[x].tolist(),
                    'y': plot_data[y].tolist(),
                    'name': y.title()
                }]
                
        elif plot_type == 'line':
            if color:
                # Create multi-line chart
                for group in plot_data[color].unique():
                    group_data = plot_data[plot_data[color] == group]
                    plot_data_list.append({
                        'type': 'scatter',
                        'mode': 'lines+markers',
                        'x': group_data[x].tolist(),
                        'y': group_data[y].tolist(),
                        'name': str(group)
                    })
            else:
                plot_data_list = [{
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'x': plot_data[x].tolist(),
                    'y': plot_data[y].tolist(),
                    'name': y.title()
                }]
                
        elif plot_type == 'scatter':
            plot_data_list = [{
                'type': 'scatter',
                'mode': 'markers',
                'x': plot_data[x].tolist(),
                'y': plot_data[y].tolist(),
                'marker': {
                    'color': plot_data[color].tolist() if color else None,
                    'colorscale': 'Viridis'
                },
                'name': y.title()
            }]
            
        elif plot_type == 'pie':
            plot_data_list = [{
                'type': 'pie',
                'labels': plot_data[x].tolist(),
                'values': plot_data[y].tolist(),
                'name': y.title()
            }]
            
        elif plot_type == 'histogram':
            plot_data_list = [{
                'type': 'histogram',
                'x': plot_data[x].tolist(),
                'nbinsx': 30,
                'name': x.title()
            }]
            
        elif plot_type == 'box':
            if color:
                # Create grouped box plot
                for group in plot_data[color].unique():
                    group_data = plot_data[plot_data[color] == group]
                    plot_data_list.append({
                        'type': 'box',
                        'y': group_data[y].tolist(),
                        'name': str(group)
                    })
            else:
                plot_data_list = [{
                    'type': 'box',
                    'y': plot_data[y].tolist(),
                    'name': y.title()
                }]
                
        else:
            print(f"Unknown plot type: {plot_type}, defaulting to bar chart")
            plot_data_list = [{
                'type': 'bar',
                'x': plot_data[x].tolist(),
                'y': plot_data[y].tolist(),
                'name': y.title()
            }]
        
        # Create layout
        layout = {
            'title': title,
            'showlegend': True,
            'legend': {
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'right',
                'x': 1
            },
            'margin': {'t': 50, 'l': 50, 'r': 50, 'b': 50},
            'xaxis': {'title': x.title() if x else ''},
            'yaxis': {'title': y.title() if y else ''}
        }
        
        # Add faceting if specified
        if facet:
            layout['grid'] = {'rows': len(plot_data[facet].unique()), 'columns': 1}
            layout['height'] = 300 * len(plot_data[facet].unique())
        
        print("Creating visualization result")
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
