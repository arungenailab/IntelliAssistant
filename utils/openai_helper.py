import os
import json
from openai import OpenAI

# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def query_openai(user_query, system_prompt=None, model="gpt-4o"):
    """
    Query OpenAI with user input and an optional system prompt.
    
    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
    do not change this unless explicitly requested by the user
    
    Args:
        user_query (str): The user's query
        system_prompt (str, optional): System instructions for the model
        model (str, optional): The OpenAI model to use
        
    Returns:
        str: The model's response
    """
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": user_query})
    
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,  # Low temperature for more deterministic responses
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")

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
    system_prompt = f"""
    You are an assistant that converts natural language queries into SQL-like queries.
    Available data sources: {', '.join(available_sources)}
    
    For each data source, here are the available columns:
    """
    
    if dataframes_info:
        for source, info in dataframes_info.items():
            if source in available_sources:
                system_prompt += f"\n{source}: {', '.join(info['columns'])}"
    
    system_prompt += """
    Generate a SQL-like query that would answer the user's question. 
    If multiple data sources are needed, include JOIN operations.
    If visualization is requested, include appropriate GROUP BY or aggregate functions.
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.1,  # Very low temperature for consistent SQL generation
        )
        return response.choices[0].message.content
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
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        # If there's an error, return a default response
        return {
            "improved_query": user_query,
            "clarifying_questions": ["Could you provide more details about what you're looking for?"],
            "explanation": "I encountered an issue analyzing your query."
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
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        # If there's an error, return None and let the calling function handle it
        return None
