import os
import time
import google.generativeai as genai
import json
import re
from typing import Dict, List, Any, Optional, Union

# Set API key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Default model for text generation
DEFAULT_MODEL = "models/gemini-1.5-pro"

# Print available Gemini models
print("Available Gemini models:")
for model in genai.list_models():
    if "gemini" in model.name:
        print(f"- {model.name}")

def query_gemini(user_query, system_prompt=None, model=DEFAULT_MODEL):
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
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Create model instance
            model_instance = genai.GenerativeModel(model)
            
            # Set generation config to improve quality and reduce questioning
            generation_config = {
                "temperature": 0.2,  # Lower temperature for more focused responses
                "top_p": 0.95,       # More deterministic output
                "top_k": 40,         # More focused token selection
                "max_output_tokens": 2048,  # Allow for comprehensive answers
            }
            
            # Prepare the prompt
            if system_prompt:
                # Add specific instruction to provide complete answers without questions
                enhanced_system_prompt = system_prompt.strip() + """
                
                IMPORTANT: Provide complete, comprehensive answers that anticipate the user's needs.
                DO NOT ask follow-up questions in your response. Instead, provide all relevant information
                in a single, thorough answer.
                """
                
                # Gemini doesn't support system role directly, so we'll prepend it to the user query
                combined_prompt = f"{enhanced_system_prompt}\n\nUser query: {user_query}"
                response = model_instance.generate_content(
                    combined_prompt,
                    generation_config=generation_config
                )
            else:
                # Add instruction to the raw query
                enhanced_query = f"""
                Please provide a complete answer to the following query without asking follow-up questions:
                
                {user_query}
                """
                response = model_instance.generate_content(
                    enhanced_query,
                    generation_config=generation_config
                )
            
            # Extract and return the text response
            return response.text
        
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise Exception(f"Failed to query Gemini after {max_retries} attempts: {str(e)}")
            
            # Exponential backoff
            wait_time = 2 ** retry_count
            print(f"Error querying Gemini: {str(e)}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

def generate_sql_query(user_query, available_sources, dataframes_info=None):
    """
    Generate a SQL-like query from a natural language query.
    
    Args:
        user_query (str): The user's natural language query
        available_sources (list): Available data sources
        dataframes_info (dict, optional): Information about available dataframes
        
    Returns:
        str: The generated SQL-like query
    """
    # Create a system prompt
    system_prompt = f"""
    You are an expert SQL query generator.
    
    The user is trying to query their data using natural language.
    Convert the natural language query into a SQL query that can be executed.
    
    Available data sources: {', '.join(available_sources)}
    """
    
    if dataframes_info:
        system_prompt += "\n\nInformation about available data sources:\n"
        for df_name, info in dataframes_info.items():
            system_prompt += f"\n{df_name}:\n"
            system_prompt += f"- Columns: {', '.join(info.get('columns', []))}\n"
            system_prompt += f"- Types: {info.get('types', {})}\n"
    
    system_prompt += """
    Return ONLY the SQL query without any explanation or additional text.
    Don't use backticks or other markdown formatting.
    """
    
    try:
        response = query_gemini(
            user_query=user_query,
            system_prompt=system_prompt,
            model=DEFAULT_MODEL
        )
        return response
    except Exception as e:
        raise Exception(f"Failed to generate SQL query: {str(e)}")

def suggest_query_improvements(user_query, data_context):
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
        
        # Attempt to parse the response as JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Extract JSON from the response if it's not properly formatted
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                # If JSON extraction fails, create a structured response
                return {
                    "improved_query": user_query,
                    "clarifying_questions": ["Could you provide more details about what you're looking for?"],
                    "explanation": "I processed your query but couldn't format the response properly."
                }
    except Exception as e:
        # If there's an error, return a default response
        return {
            "improved_query": user_query,
            "clarifying_questions": ["Could you provide more details about what you're looking for?"],
            "explanation": f"I encountered an issue analyzing your query: {str(e)}"
        }

def extract_visualization_parameters(user_query, data_sample):
    """
    Extract visualization parameters from a user query.
    
    Args:
        user_query (str): The user's query
        data_sample (dict): Sample of the data to be visualized
        
    Returns:
        dict: Visualization parameters (type, x_axis, y_axis, etc.)
    """
    system_prompt = f"""
    You are a data visualization expert. Given a user query and a sample of data,
    determine the best visualization type and parameters.
    
    Data sample: {json.dumps(data_sample)}
    
    Return your response in JSON format with these fields:
    1. visualization_type (str): The recommended visualization type (bar, line, scatter, pie, etc.)
    2. x_axis (str): The column to use for the x-axis
    3. y_axis (str or list): The column(s) to use for the y-axis
    4. title (str): A suggested title for the visualization
    5. color_by (str, optional): Column to use for color differentiation
    6. facet_by (str, optional): Column to use for faceting/small multiples
    """
    
    try:
        response = query_gemini(
            user_query=user_query,
            system_prompt=system_prompt,
            model=DEFAULT_MODEL
        )
        
        # Attempt to parse the response as JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Extract JSON from the response if it's not properly formatted
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                # If JSON extraction fails, return None and let the calling function handle it
                return None
    except Exception as e:
        # If there's an error, return None and let the calling function handle it
        return None