import os
import time
import google.generativeai as genai
import json
import re
import pandas as pd
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

def analyze_data(user_query: str, data: pd.DataFrame, conversation_history: Optional[List] = None) -> Dict[str, Any]:
    """
    Analyze data based on user query and return insights with visualization suggestions
    
    Args:
        user_query (str): User's question or request
        data (pd.DataFrame): Data to analyze
        conversation_history (List, optional): Previous conversation messages
        
    Returns:
        Dict with text response and visualization config
    """
    try:
        # Create system prompt with data context
        system_prompt = "You are an expert data analyst. Analyze the data and provide insights based on the user's query.\n\n"
        
        # Add formatting instructions
        system_prompt += "FORMAT YOUR RESPONSES WITH PROPER STRUCTURE:\n"
        system_prompt += "- Use paragraph breaks between different points or sections\n"
        system_prompt += "- Use bullet points or numbered lists for multiple items\n"
        system_prompt += "- Include proper spacing and indentation for readability\n"
        system_prompt += "- Format numbers and statistics clearly\n\n"
        
        # Add data context
        system_prompt += f"Data shape: {data.shape[0]} rows, {data.shape[1]} columns\n"
        system_prompt += f"Columns: {', '.join(data.columns)}\n\n"
        
        # Add sample data
        system_prompt += "Sample data (first 3 rows):\n"
        system_prompt += data.head(3).to_string()
        system_prompt += "\n\nSummary statistics:\n"
        system_prompt += data.describe().to_string()
        
        # Add conversation history if available
        if conversation_history:
            system_prompt += "\n\nPrevious conversation:\n"
            for msg in conversation_history[-3:]:  # Last 3 messages
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                system_prompt += f"{role}: {content}\n"
        
        # Query Gemini
        response = query_gemini(
            user_query=user_query,
            system_prompt=system_prompt,
            model=DEFAULT_MODEL
        )
        
        # Ensure response has proper formatting
        response = ensure_proper_formatting(response)
        
        # Determine if visualization would be helpful
        viz_config = None
        viz_keywords = ['trend', 'compare', 'distribution', 'relationship', 'show', 'plot', 'graph', 'chart', 'visualize']
        
        if any(keyword in user_query.lower() for keyword in viz_keywords):
            # Get visualization parameters
            viz_config = extract_visualization_parameters(data, response, user_query)
        
        return {
            'text': response,
            'visualization': viz_config
        }
        
    except Exception as e:
        print(f"Error analyzing data: {str(e)}")
        return {
            'text': f"I encountered an error analyzing the data: {str(e)}",
            'visualization': None
        }

def ensure_proper_formatting(text: str) -> str:
    """
    Ensure the response text has proper formatting with line breaks and spacing.
    
    Args:
        text (str): The response text from the model
        
    Returns:
        str: Properly formatted text
    """
    # Replace single newlines with double newlines for paragraph breaks
    text = re.sub(r'(?<!\n)\n(?!\n)', '\n\n', text)
    
    # Ensure bullet points and numbered lists have proper spacing
    text = re.sub(r'(\n[*\-•])', '\n\n$1', text)
    text = re.sub(r'(\n\d+\.)', '\n\n$1', text)
    
    # Remove excessive newlines (more than 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
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
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Create model instance
            model_instance = genai.GenerativeModel(model)
            
            # Set generation config
            generation_config = {
                "temperature": 0.2,  # Lower temperature for more focused responses
                "top_p": 0.95,       # More deterministic output
                "top_k": 40,         # More focused token selection
                "max_output_tokens": 2048,  # Allow for comprehensive answers
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
                Please provide a complete answer to the following query without asking follow-up questions:
                
                {user_query}
                """
                response = model_instance.generate_content(
                    enhanced_query,
                    generation_config=generation_config
                )
            
            # Return the text response
            return response.text.strip()
        
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                raise Exception(f"Failed to query Gemini after {max_retries} attempts: {str(e)}")
            
            # Exponential backoff
            wait_time = 2 ** retry_count
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
    """Extract visualization parameters from the Gemini model response."""
    system_prompt = """You are a data visualization expert. Based on the data and query results provided,
determine the most effective visualization parameters to represent the insights.

APPROACH:
1. INTERNALLY analyze the data structure and values
2. Consider the user's question and what insights they're seeking
3. Choose the most appropriate visualization type
4. Determine the optimal configuration parameters

IMPORTANT:
1. Return ONLY a valid JSON configuration object
2. DO NOT include any explanatory text or code snippets
3. DO NOT use markdown code blocks
4. Ensure all parameters match the data columns exactly
5. Include all required parameters for the chosen visualization type

The configuration MUST follow this exact format:
{
    "type": "bar|line|scatter|pie|histogram|box",
    "x": "exact_column_name_for_x_axis",
    "y": "exact_column_name_for_y_axis",
    "title": "Clear and descriptive title",
    "color": "column_name_for_color_grouping",  // Optional
    "orientation": "horizontal|vertical",  // Optional
    "aggregation": "sum|mean|count",  // Optional
    "additional_params": {}  // Optional
}
"""

    user_message = f"""
Data structure: {data.dtypes.to_dict()}
Sample data: {data.head(3).to_dict()}
Query result: {query_result}
Available columns: {list(data.columns)}
User question: {user_query}

Based on this information, provide the visualization configuration that will best represent the insights.
"""

    try:
        model = genai.GenerativeModel('gemini-1.0-pro')
        response = model.generate_content([
            {'role': 'system', 'parts': [system_prompt]},
            {'role': 'user', 'parts': [user_message]}
        ])
        
        # Extract and validate JSON configuration
        try:
            config = json.loads(response.text)
            
            # Validate required fields
            required_fields = ['type', 'title']
            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                print(f"Warning: Missing required fields in visualization config: {missing_fields}")
                return None
            
            # Validate column names
            if 'x' in config and config['x'] not in data.columns:
                print(f"Warning: x-axis column '{config['x']}' not found in data")
                return None
            if 'y' in config and config['y'] not in data.columns:
                print(f"Warning: y-axis column '{config['y']}' not found in data")
                return None
            
            return config
            
        except json.JSONDecodeError as e:
            print(f"Error parsing visualization configuration: {str(e)}")
            return None
            
    except Exception as e:
        print(f"Error generating visualization configuration: {str(e)}")
        return None