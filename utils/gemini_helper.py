# This is a placeholder

import os
import time
import json
import re
import pandas as pd
from typing import Dict, List, Any, Optional, Union
import traceback
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Import API key from config file
try:
    from config import GEMINI_API_KEY as CONFIG_API_KEY
except ImportError:
    CONFIG_API_KEY = None

# Set API key from environment with a fallback to config file
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or CONFIG_API_KEY

# For testing purposes, if the API key is not in environment variables or config, use None
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables or config file")
    GEMINI_API_KEY = None  # Set to None to trigger the fallback response

# Initialize Gemini API
try:
    import google.generativeai as genai
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        # Default model for text generation
        DEFAULT_MODEL = "models/gemini-2.0-flash"

        # Print available Gemini models
        print("Available Gemini models:")
        for model in genai.list_models():
            if "gemini" in model.name:
                print(f"- {model.name}")
    else:
        print("Warning: GEMINI_API_KEY not found in environment variables or config file")
        DEFAULT_MODEL = None
except ImportError:
    print("Google Generative AI package not installed. Some features will be limited.")
    genai = None
    DEFAULT_MODEL = None
except Exception as e:
    print(f"Error initializing Gemini API: {str(e)}")
    genai = None
    DEFAULT_MODEL = None

def analyze_data(user_query: str, data: pd.DataFrame, conversation_history: Optional[List] = None, model_id: str = None, use_cache: bool = True) -> Dict[str, Any]:
    """
    Analyze data based on user query using Gemini API.
    
    Args:
        user_query: The user's query about the data
        data: The DataFrame to analyze
        conversation_history: Optional conversation history
        model_id: Optional model ID to use for the analysis
        use_cache: Whether to use cached results
        
    Returns:
        Dict containing the analysis result and visualization parameters if applicable
    """
    try:
        # Check if Gemini API is available
        if genai is None or DEFAULT_MODEL is None:
            # Provide a fallback response with basic dataset information
            fallback_response = {
                "text": f"I'm unable to provide a detailed analysis because the Gemini API is not configured properly. Here's some basic information about your dataset:\n\n"
                        f"- Dataset shape: {data.shape[0]} rows, {data.shape[1]} columns\n"
                        f"- Columns: {', '.join(data.columns.tolist())}\n\n"
                        f"Basic statistics:\n{data.describe().to_string()}\n\n"
                        f"To get more detailed analysis, please ensure the GEMINI_API_KEY environment variable is set correctly.",
                "visualization": extract_visualization_parameters(data, None, user_query),
                "model_used": "fallback",
                "is_fallback": True
            }
            return fallback_response
            
        # Check if visualization is requested
        visualization_requested = any(keyword in user_query.lower() for keyword in 
                                     ["plot", "chart", "graph", "visual", "visualize", "visualization", "show", "display"])
        
        # Prepare data context with complete dataset
        data_context = {
            "shape": data.shape,
            "columns": list(data.columns),
            "dtypes": {col: str(dtype) for col, dtype in zip(data.columns, data.dtypes)},
            "data": data.to_string(),  # Send complete dataset
            "stats": data.describe(include='all').to_string(),
        }
        
        # Calculate and add explicit dataset statistics for reliable results
        data_context["explicit_stats"] = {}
        
        # Calculate key metrics for all numerical columns
        for col in data.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns:
            try:
                # Calculate statistics directly, not relying on the describe() function
                col_values = data[col].dropna()
                if len(col_values) > 0:
                    # Find the dates associated with min and max values if there's a date column
                    date_min_max = {}
                    if 'date' in data.columns:
                        try:
                            max_idx = col_values.idxmax()
                            min_idx = col_values.idxmin()
                            max_date = data.loc[max_idx, 'date']
                            min_date = data.loc[min_idx, 'date']
                            
                            # Format dates as strings if they're timestamps
                            if hasattr(max_date, 'strftime'):
                                max_date = max_date.strftime('%Y-%m-%d')
                            if hasattr(min_date, 'strftime'):
                                min_date = min_date.strftime('%Y-%m-%d')
                                
                            date_min_max = {
                                "max_date": max_date,
                                "min_date": min_date
                            }
                        except Exception as e:
                            logger.warning(f"Error getting date min/max for column {col}: {str(e)}")
                    
                    # Safely convert numeric values
                    try:
                        min_val = float(col_values.min()) if not pd.isna(col_values.min()) else None
                        max_val = float(col_values.max()) if not pd.isna(col_values.max()) else None
                        mean_val = float(col_values.mean()) if not pd.isna(col_values.mean()) else None
                        median_val = float(col_values.median()) if not pd.isna(col_values.median()) else None
                        
                        # Get top 5 values safely
                        top_values = []
                        for val in sorted(col_values.unique(), reverse=True)[:5]:
                            if pd.isna(val):
                                continue
                            try:
                                top_values.append(float(val))
                            except (TypeError, ValueError):
                                top_values.append(str(val))
                        
                        data_context["explicit_stats"][col] = {
                            "min": min_val,
                            "max": max_val,
                            "mean": mean_val,
                            "median": median_val,
                            "count": int(len(col_values)),
                            "top_5_values": top_values
                        }
                        
                        # Add date information if available
                        if date_min_max:
                            data_context["explicit_stats"][col].update(date_min_max)
                    except Exception as e:
                        logger.warning(f"Error calculating statistics for column {col}: {str(e)}")
            except Exception as e:
                logger.warning(f"Error processing numeric column {col}: {str(e)}")
        
        # Add value counts for categorical columns
        for col in data.select_dtypes(include=['object', 'category', 'string']).columns:
            try:
                if len(data[col].unique()) < 50:  # Only for columns with reasonable number of categories
                    data_context[f"{col}_value_counts"] = data[col].value_counts().to_dict()
            except Exception as e:
                logger.warning(f"Error getting value counts for column {col}: {str(e)}")
        
        # Add aggregated data for the most relevant entity-metric pair (generic approach)
        # First, identify potential entity columns (categorical) and metric columns (numerical)
        entity_columns = data.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
        metric_columns = data.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        # If we have both entity and metric columns, create aggregations
        if entity_columns and metric_columns:
            try:
                # Find the most likely entity column (prefer columns with 'name', 'person', 'customer', etc.)
                entity_keywords = ['name', 'person', 'customer', 'client', 'product', 'category', 'type', 'region', 'country', 'city']
                entity_col = None
                
                # Try to find a column that matches our entity keywords
                for keyword in entity_keywords:
                    matching_cols = [col for col in entity_columns if keyword.lower() in col.lower()]
                    if matching_cols:
                        entity_col = matching_cols[0]
                        break
                
                # If no keyword match, use the first entity column
                if not entity_col and entity_columns:
                    entity_col = entity_columns[0]
                
                # Find the most likely metric column (prefer columns with 'amount', 'value', 'price', etc.)
                metric_keywords = ['amount', 'value', 'price', 'sales', 'revenue', 'cost', 'profit', 'quantity', 'count']
                metric_col = None
                
                # Try to find a column that matches our metric keywords
                for keyword in metric_keywords:
                    matching_cols = [col for col in metric_columns if keyword.lower() in col.lower()]
                    if matching_cols:
                        metric_col = matching_cols[0]
                        break
                
                # If no keyword match, use the first metric column
                if not metric_col and metric_columns:
                    metric_col = metric_columns[0]
                
                # If we have both entity and metric columns, create aggregations
                if entity_col and metric_col:
                    try:
                        # Group by entity and sum the metric
                        grouped = data.groupby(entity_col)[metric_col].sum().sort_values(ascending=False)
                        
                        # Get the top entities by the metric
                        top_entities = grouped.head(10).to_dict()
                        
                        # Add to data context
                        data_context['top_entities'] = {
                            'entity_column': entity_col,
                            'metric_column': metric_col,
                            'data': top_entities
                        }
                        
                        # Also add entity counts
                        entity_counts = data[entity_col].value_counts().head(10).to_dict()
                        data_context['entity_counts'] = {
                            'entity_column': entity_col,
                            'data': entity_counts
                        }
                    except Exception as e:
                        logger.warning(f"Error creating entity-metric aggregations: {str(e)}")
            except Exception as e:
                logger.warning(f"Error identifying entity-metric columns: {str(e)}")
        
        # Build system prompt with data context
        system_prompt = """You are a data analysis assistant. Your responses should be:
1. Direct and concise - answer exactly what was asked
2. Focused on key insights without unnecessary elaboration
3. Numerical and fact-based
4. Free of implementation details or technical instructions

IMPORTANT: You must ONLY use the exact numerical values provided in this prompt. Do not round, approximate, or make up values.

Current dataset summary:
"""
        # Add dataset shape and column information
        system_prompt += f"\nDataset shape: {data_context['shape'][0]} rows, {data_context['shape'][1]} columns"
        system_prompt += f"\nColumns: {', '.join(data_context['columns'])}"
        
        # Add explicit statistics first to ensure they're prioritized
        if "explicit_stats" in data_context:
            system_prompt += "\n\n## VERIFIED DATASET STATISTICS (Use these exact values):\n"
            for col, stats in data_context["explicit_stats"].items():
                try:
                    system_prompt += f"\n### {col} statistics:\n"
                    if "min" in stats and stats["min"] is not None:
                        system_prompt += f"- Minimum value: {stats['min']}\n"
                    if "min_date" in stats:
                        system_prompt += f"- Date of minimum value: {stats['min_date']}\n"
                    if "max" in stats and stats["max"] is not None:
                        system_prompt += f"- Maximum value: {stats['max']}\n"
                    if "max_date" in stats:
                        system_prompt += f"- Date of maximum value: {stats['max_date']}\n"
                    if "mean" in stats and stats["mean"] is not None:
                        system_prompt += f"- Mean: {stats['mean']}\n"
                    if "median" in stats and stats["median"] is not None:
                        system_prompt += f"- Median: {stats['median']}\n"
                    if "count" in stats:
                        system_prompt += f"- Count: {stats['count']}\n"
                    if "top_5_values" in stats and stats["top_5_values"]:
                        system_prompt += f"- Top values: {stats['top_5_values']}\n"
                except Exception as e:
                    logger.warning(f"Error adding statistics for column {col} to system prompt: {str(e)}")
        
        # Add value counts and other statistical information
        for key, value in data_context.items():
            try:
                if key.endswith('_value_counts'):
                    col_name = key.replace('_value_counts', '')
                    system_prompt += f"\nDistribution for {col_name}:\n{json.dumps(value, indent=2)}\n"
                elif key == 'top_entities':
                    entity_col = value['entity_column']
                    metric_col = value['metric_column']
                    system_prompt += f"\nTop {entity_col} by {metric_col}:\n{json.dumps(value['data'], indent=2)}\n"
                elif key == 'entity_counts':
                    entity_col = value['entity_column']
                    system_prompt += f"\nTop {entity_col} by count:\n{json.dumps(value['data'], indent=2)}\n"
            except Exception as e:
                logger.warning(f"Error adding {key} to system prompt: {str(e)}")
        
        # Add instructions for response formatting with emphasis on accuracy
        system_prompt += """
VERIFICATION INSTRUCTIONS:
1. Double-check all numerical values in your response against the VERIFIED DATASET STATISTICS section
2. If asked for a specific statistic like maximum or minimum value, use EXACTLY the value from the statistics section
3. DO NOT hallucinate or make up data that isn't explicitly provided

Your response should:
1. Be clear, concise, and informative
2. Use markdown formatting for better readability
3. Provide specific insights based on the complete dataset
4. Include numerical evidence and statistics to support insights
5. Not hallucinate information that isn't in the data
6. Be complete and comprehensive without asking follow-up questions
"""

        # Query Gemini with complete data context
        response_text = query_gemini(
            user_query=user_query,
            system_prompt=system_prompt,
            model=model_id if model_id else "models/gemini-1.5-pro"  # Use the specified model or default to Pro model
        )
        
        # Extract visualization parameters if visualization is requested
        visualization = None
        if visualization_requested:
            visualization = extract_visualization_parameters(data, response_text, user_query)
        
        return {
            "text": response_text,
            "visualization": visualization,
            "model_used": model_id if model_id else "models/gemini-1.5-pro",
            "is_fallback": False
        }
    
    except Exception as e:
        error_message = f"Error analyzing data: {str(e)}"
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        return {
            "text": error_message,
            "visualization": None,
            "model_used": model_id if model_id else "models/gemini-1.5-pro",
            "is_fallback": True
        }

def ensure_proper_formatting(text: str) -> str:
    """
    Ensure the response text has proper formatting with line breaks and spacing.
    
    Args:
        text (str): The response text from the model
        
    Returns:
        str: Properly formatted text
    """
    # First, normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Split into lines and remove excessive whitespace
    lines = [line.strip() for line in text.split('\n')]
    
    # Join back with proper formatting
    text = '\n'.join(lines)
    
    # Clean up excessive line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Final cleanup
    text = text.strip()
    
    return text

def query_gemini(user_query: str, system_prompt: Optional[str] = None, model: str = DEFAULT_MODEL) -> str:
    """
    Query Gemini with user input and an optional system prompt.
    
    Args:
        user_query (str): The user's query
        system_prompt (str, optional): System instructions for the model
        model (str, optional): The Gemini model to use
        
    Returns:
        str: The model's response
    """
    # Maximum number of retries
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Create model instance using the specified model or default
            model_to_use = model if model else "models/gemini-2.0-flash"
            print(f"Using Gemini model: {model_to_use}")
            model_instance = genai.GenerativeModel(model_to_use)
            
            # Set generation config with reduced tokens for quota efficiency
            generation_config = {
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 4096,  # Reduced from 8192 for quota efficiency
                "candidate_count": 1
            }
            
            # Prepare the prompt
            if system_prompt:
                # Add specific instruction to provide complete answers
                enhanced_system_prompt = system_prompt.strip() + """
                
                IMPORTANT: Provide complete, comprehensive answers that anticipate the user's needs.
                DO NOT ask follow-up questions in your response. Instead, provide all relevant information
                in a single, thorough answer.
                """
                
                # Combine prompts
                combined_prompt = f"{enhanced_system_prompt}\n\nUser query: {user_query}"
                response = model_instance.generate_content(
                    combined_prompt,
                    generation_config=generation_config
                )
            else:
                # Add instruction to the raw query
                enhanced_query = f"""
                Please provide a complete answer to the following query without asking follow-up questions.
                Format your response with proper line breaks and spacing:
                
                {user_query}
                """
                response = model_instance.generate_content(
                    enhanced_query,
                    generation_config=generation_config
                )
            
            # Apply proper formatting to the response text
            formatted_response = ensure_proper_formatting(response.text.strip())
            
            # Return the formatted text response
            return formatted_response
        
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                if "429" in str(e) or "quota" in str(e).lower():
                    return "I apologize, but we've temporarily exceeded our quota limits. Please try again in a few minutes."
                else:
                    return f"I encountered an error analyzing the data: {str(e)}"
            
            # Exponential backoff with longer initial wait
            wait_time = 5 * (2 ** retry_count)  # Starts at 10 seconds, then 20, 40, etc.
            print(f"Error querying Gemini: {str(e)}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

def suggest_query_improvements(user_query: str, data_context: Dict) -> Dict[str, Any]:
    """
    Suggest improvements to user's query based on available data.
    
    Args:
        user_query (str): The user's original query
        data_context (dict): Context about available data
        
    Returns:
        dict: Suggested improvements and clarifying questions
    """
    system_prompt = f"""
    You are an expert data analyst assistant. 
    Given a user's query and the available data context, suggest improvements to the query 
    or ask clarifying questions that would help produce better results.
    
    Available data context: {json.dumps(data_context)}
    
    Return your response in JSON format with these fields:
    1. improved_query (str): An improved version of the query if possible
    2. clarifying_questions (list): Questions to ask the user if needed
    3. explanation (str): Explanation of why improvements were suggested
    """
    
    try:
        response = query_gemini(
            user_query=user_query,
            system_prompt=system_prompt,
            model=DEFAULT_MODEL
        )
        
        # Parse response as JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Extract JSON if not properly formatted
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                return {
                    "improved_query": user_query,
                    "clarifying_questions": ["Could you provide more details about what you're looking for?"],
                    "explanation": "I processed your query but couldn't format the response properly."
                }
    except Exception as e:
        return {
            "improved_query": user_query,
            "clarifying_questions": ["Could you provide more details about what you're looking for?"],
            "explanation": f"I encountered an issue analyzing your query: {str(e)}"
        }

def extract_visualization_parameters(data, query_result, user_query):
    """
    Extract visualization parameters from the query result and data context.
    
    Args:
        data (pd.DataFrame): The dataset
        query_result (str): The result from the LLM query
        user_query (str): The original user query
        
    Returns:
        dict: Visualization parameters including type, x and y columns, etc.
            or None if visualization is not needed
    """
    try:
        # Debug information
        print(f"[DEBUG] Extracting visualization parameters")
        print(f"[DEBUG] Data columns: {data.columns.tolist()}")
        print(f"[DEBUG] User query: {user_query}")
        
        # Dictionary of visualization types and their keywords
        vis_types = {
            'bar': ['bar chart', 'bar graph', 'barchart', 'bargraph', 'column chart', 'histogram'],
            'line': ['line chart', 'line graph', 'linechart', 'linegraph', 'trend', 'time series'],
            'scatter': ['scatter plot', 'scatterplot', 'scatter chart', 'scattergraph', 'correlation'],
            'pie': ['pie chart', 'piechart', 'pie graph', 'piegraph', 'donut chart']
        }
        
        # Combine query result and user query for better analysis
        combined_text = f"{user_query.lower()}"
        if query_result:
            combined_text = f"{query_result.lower()} {combined_text}"
        
        # Determine visualization type based on keywords
        vis_type = 'bar'  # Default to bar chart
        for vtype, keywords in vis_types.items():
            if any(keyword in combined_text for keyword in keywords):
                vis_type = vtype
                break
        
        # Check for "top N" request
        top_n = None
        top_n_match = re.search(r'top\s+(\d+)', combined_text)
        if top_n_match:
            top_n = int(top_n_match.group(1))
        
        # Common aggregation keywords
        aggregation_keywords = {
            'sum': ['sum', 'total', 'overall', 'amount'],
            'average': ['average', 'avg', 'mean'],
            'count': ['count', 'frequency', 'occurrences', 'number of', 'number of sales', 'sales count', 'count of sales'],
            'max': ['maximum', 'max', 'highest', 'top', 'best'],
            'min': ['minimum', 'min', 'lowest', 'bottom', 'worst']
        }
        
        # Determine aggregation method
        aggregation = 'sum'  # Default
        for agg_type, keywords in aggregation_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                aggregation = agg_type
                break
                
        # Special case for "number of sales" or similar phrases
        if 'number of sales' in combined_text or 'by number of sales' in combined_text or 'count of sales' in combined_text:
            print("[DEBUG] Detected request for number of sales - setting aggregation to count")
            aggregation = 'count'
        
        # Extract column names from the query
        x_col = None
        y_col = None
        
        # Try to identify column names mentioned in the query
        for col in data.columns:
            col_lower = col.lower()
            # Check if column is mentioned in the query
            if col_lower in combined_text:
                # Determine if this should be x or y based on data type
                if data[col].dtype in ['object', 'category', 'string'] and x_col is None:
                    x_col = col
                elif data[col].dtype in ['int64', 'float64', 'int32', 'float32'] and y_col is None:
                    y_col = col
        
        # Make educated guesses if columns weren't explicitly found
        if x_col is None or y_col is None:
            # Get categorical and numerical columns
            categorical_cols = data.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
            numerical_cols = data.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()
            
            # For bar charts, prefer categorical for x and numerical for y
            if vis_type == 'bar':
                # Check for specific entity types in the query
                entity_types = {
                    'salesperson': ['sales person', 'salesperson', 'sales rep', 'representative', 'seller'],
                    'customer': ['customer', 'client', 'buyer', 'purchaser'],
                    'product': ['product', 'item', 'merchandise', 'goods']
                }
                
                entity_type = None
                for etype, keywords in entity_types.items():
                    if any(keyword in combined_text for keyword in keywords):
                        entity_type = etype
                        break
                
                if x_col is None and categorical_cols:
                    # If we detected a specific entity type, look for matching columns
                    if entity_type:
                        entity_cols = [col for col in categorical_cols if any(term in col.lower() for term in entity_types[entity_type])]
                        if entity_cols:
                            x_col = entity_cols[0]
                            print(f"[DEBUG] Selected {x_col} as x-axis based on entity type {entity_type}")
                    
                    # If no entity-specific column found, use general heuristics
                    if x_col is None:
                        entity_cols = [col for col in categorical_cols if any(term in col.lower() for term in 
                                      ['name', 'person', 'product', 'category', 'type', 'region', 'country', 'city'])]
                        x_col = entity_cols[0] if entity_cols else categorical_cols[0]
                
                if y_col is None and numerical_cols:
                    # If aggregation is count, we don't need a specific y column
                    if aggregation == 'count':
                        # For count aggregation, y_col will be determined by the aggregation
                        # We'll use a column that makes sense to count
                        count_cols = [col for col in numerical_cols if any(term in col.lower() for term in 
                                     ['id', 'order', 'transaction', 'sale'])]
                        y_col = count_cols[0] if count_cols else numerical_cols[0]
                        print(f"[DEBUG] Using {y_col} for counting with aggregation {aggregation}")
                    else:
                        # For other aggregations, prioritize columns that might represent metrics
                        metric_cols = [col for col in numerical_cols if any(term in col.lower() for term in 
                                      ['sales', 'revenue', 'profit', 'count', 'amount', 'total', 'sum', 'value', 'quantity', 'shipped', 'boxes'])]
                        y_col = metric_cols[0] if metric_cols else numerical_cols[0]
            
            # For line charts, prefer date/time for x and numerical for y
            elif vis_type == 'line':
                date_cols = [col for col in data.columns if data[col].dtype in ['datetime64[ns]', 'datetime64']]
                if x_col is None:
                    x_col = date_cols[0] if date_cols else (categorical_cols[0] if categorical_cols else data.columns[0])
                if y_col is None and numerical_cols:
                    y_col = numerical_cols[0]
        
        # If we still don't have columns, use the first two appropriate columns
        if x_col is None:
            x_col = data.columns[0]
        if y_col is None:
            # Try to find a numeric column different from x_col
            for col in data.columns:
                if col != x_col and data[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                    y_col = col
                    break
            # If no numeric column found, use the second column if available
            if y_col is None and len(data.columns) > 1:
                y_col = data.columns[1]
            # Last resort, use the same as x_col
            if y_col is None:
                y_col = x_col
        
        # Extract or generate title
        title = None
        # Look for lines that might contain a title
        title_indicators = ['title:', 'chart title:', 'graph title:', 'visualization title:']
        if query_result:
            for line in query_result.split('\n'):
                line_lower = line.lower()
                if any(indicator in line_lower for indicator in title_indicators):
                    title = line.split(':', 1)[1].strip()
                    break
        
        # If no title found, generate one based on the columns and visualization type
        if not title:
            if top_n:
                if aggregation == 'count':
                    title = f"Top {top_n} {x_col} by Number of Sales"
                else:
                    title = f"Top {top_n} {x_col} by {y_col}"
            else:
                if aggregation == 'count':
                    title = f"Number of Sales by {x_col}"
                else:
                    title = f"{y_col} by {x_col}"
        
        # Create visualization parameters
        vis_params = {
            'type': vis_type,
            'x': x_col,
            'y': y_col,
            'title': title,
            'aggregation': aggregation
        }
        
        if top_n:
            vis_params['top_n'] = top_n
        
        print(f"[DEBUG] Visualization parameters: {vis_params}")
        return vis_params
        
    except Exception as e:
        print(f"Error extracting visualization parameters: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return None

