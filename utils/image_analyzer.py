import os
import base64
import google.generativeai as genai
import io
import json
import pandas as pd
import re
import time
from PIL import Image
from typing import Tuple, Dict, List, Any, Optional, Union

# Set API key from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Default model for multimodal
DEFAULT_VISION_MODEL = "models/gemini-1.5-pro"

def encode_image_to_base64(image_path):
    """
    Encode an image to base64 string.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Base64 encoded image string
    """
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

def analyze_image(image_path, prompt=None):
    """
    Analyze an image using Gemini's multimodal capabilities.
    
    Args:
        image_path (str): Path to the image file
        prompt (str, optional): Specific prompt for image analysis
        
    Returns:
        str: Analysis result
    """
    # Default prompt if none is provided
    if not prompt:
        prompt = """
        Analyze this image in detail. 
        Describe what you see, the main elements, any text content, and the overall context.
        If there are any charts, graphs, or tables, describe their content and purpose.
        If there's text in the image, include it in your analysis.
        """
    
    # Maximum number of retries
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Load the image
            img = Image.open(image_path)
            
            # Create model
            model = genai.GenerativeModel(DEFAULT_VISION_MODEL)
            
            # Convert image to correct format for the model
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format=img.format or 'PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Create multimodal content parts
            response = model.generate_content([prompt, {"mime_type": f"image/{img.format.lower() if img.format else 'png'}", "data": img_byte_arr}])
            
            # Return the response text
            return response.text
        
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                return f"Error analyzing image after {max_retries} retries: {str(e)}"
            
            # Exponential backoff
            wait_time = 2 ** retry_count
            print(f"Error analyzing image: {str(e)}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

def extract_data_from_image(image_path, extraction_type="table"):
    """
    Extract structured data from an image.
    
    Args:
        image_path (str): Path to the image file
        extraction_type (str): Type of data to extract ("table", "chart", "text", "form")
        
    Returns:
        tuple: (extracted_data, format_type)
            - extracted_data: DataFrame or text
            - format_type: Type of extracted data ("dataframe", "text")
    """
    # Create extraction prompt based on type
    if extraction_type == "table":
        prompt = """
        Extract the table data visible in this image.
        Represent the table data as a formatted markdown table.
        Make sure to include all rows and columns.
        Only include the table data, nothing else.
        Make sure the data is accurately transcribed.
        """
    elif extraction_type == "chart":
        prompt = """
        Extract the data from this chart/graph image.
        Represent the underlying data as a markdown table with headers.
        Include all data points visible in the chart.
        If exact values are not clear, provide best estimates.
        """
    elif extraction_type == "form":
        prompt = """
        Extract all form fields and their values from this image.
        Format the results as a markdown table with two columns: Field and Value.
        Include all visible form fields and their corresponding values.
        """
    else:  # text
        prompt = """
        Extract all text content visible in this image.
        Preserve the structure and formatting as much as possible.
        Include all paragraphs, bullet points, headings, etc.
        Do not add any interpretations or analysis.
        """
    
    try:
        # Use the image analyzer to get the text response
        extraction_result = analyze_image(image_path, prompt)
        
        # For tables, charts, and forms, try to convert to a DataFrame
        if extraction_type in ["table", "chart", "form"]:
            # Check if there's a markdown table in the result
            if "|" in extraction_result and "-|-" in extraction_result.replace(" ", ""):
                # Extract the table data
                try:
                    # Parse markdown table (very basic parser)
                    lines = [line.strip() for line in extraction_result.split('\n') if line.strip() and '|' in line]
                    
                    # Skip separator lines (containing only |, -, and spaces)
                    lines = [line for line in lines if not all(c in '|-+ ' for c in line)]
                    
                    # Split by | and remove empty cells from start/end
                    rows = [row.split('|') for row in lines]
                    rows = [[cell.strip() for cell in row if cell.strip()] for row in rows]
                    
                    # First row as headers
                    headers = rows[0] if rows else []
                    data = rows[1:] if len(rows) > 1 else []
                    
                    # Create DataFrame
                    df = pd.DataFrame(data, columns=headers)
                    return df, "dataframe"
                except Exception as table_error:
                    print(f"Error converting to DataFrame: {str(table_error)}")
            
            # If table parsing failed, return the text
            return extraction_result, "text"
        else:
            # For text extraction, just return the result
            return extraction_result, "text"
    
    except Exception as e:
        return f"Error extracting data from image: {str(e)}", "text"

def analyze_image_data_trends(image_path):
    """
    Analyze data trends and insights from a chart or graph image.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        dict: Analysis results with extracted insights
    """
    prompt = """
    Analyze this chart/graph image and provide detailed insights.
    
    Your analysis should include:
    1. Type of chart/graph (bar, line, pie, scatter, etc.)
    2. Main trend or pattern shown
    3. Key data points and their significance
    4. Any anomalies or outliers
    5. Potential conclusions that can be drawn
    
    If possible, also extract the underlying data in a structured format.
    
    Format your response as JSON with these fields:
    {
      "chart_type": "The type of chart/graph",
      "main_trend": "Brief description of the main trend",
      "key_points": ["List of key insights"],
      "conclusions": ["List of potential conclusions"],
      "extracted_data": [{"x": value, "y": value}, ...] or appropriate structure
    }
    """
    
    try:
        # Analyze the image
        analysis_result = analyze_image(image_path, prompt)
        
        # Try to extract JSON from the response
        try:
            # Check if response contains JSON
            json_match = re.search(r'```json\s*({.*?})\s*```', analysis_result, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # Try direct JSON parsing
            json_match = re.search(r'{.*}', analysis_result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            # If we couldn't extract JSON, return the raw analysis
            return {"analysis": analysis_result}
        
        except json.JSONDecodeError:
            # Return raw analysis if JSON parsing fails
            return {"analysis": analysis_result}
    
    except Exception as e:
        return {"error": f"Error analyzing trends: {str(e)}"}
    
def ocr_document(image_path):
    """
    Perform Optical Character Recognition on a document image.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        dict: OCR results with extracted text and structure
    """
    prompt = """
    Perform OCR on this document image. Extract all text content with proper formatting.
    
    Your extraction should:
    1. Preserve paragraphs and line breaks
    2. Maintain headings and subheadings hierarchy
    3. Identify tables and lists
    4. Note any text that may be unclear or have low confidence
    
    Format your response as JSON with these fields:
    {
      "full_text": "The complete extracted text",
      "sections": [
        {
          "type": "heading/paragraph/list/table",
          "content": "The section content"
        }
      ],
      "confidence": "high/medium/low"
    }
    """
    
    try:
        # Analyze the image
        ocr_result = analyze_image(image_path, prompt)
        
        # Try to extract JSON from the response
        try:
            # Check if response contains JSON
            json_match = re.search(r'```json\s*({.*?})\s*```', ocr_result, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # Try direct JSON parsing
            json_match = re.search(r'{.*}', ocr_result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            # If we couldn't extract JSON, return the raw text as full_text
            return {
                "full_text": ocr_result,
                "sections": [{"type": "paragraph", "content": ocr_result}],
                "confidence": "medium"
            }
        
        except json.JSONDecodeError:
            # Return basic structure if JSON parsing fails
            return {
                "full_text": ocr_result,
                "sections": [{"type": "paragraph", "content": ocr_result}],
                "confidence": "medium"
            }
    
    except Exception as e:
        return {"error": f"Error performing OCR: {str(e)}"}

def extract_table_from_image(image_path):
    """
    Extract specifically a data table from an image.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        DataFrame: Extracted table data
    """
    prompt = """
    Extract the data table from this image. Format the data as a clean markdown table.
    Include all rows and columns with proper alignment. 
    Include column headers if present.
    Do not include any text outside the table.
    Only return the markdown table, nothing else.
    """
    
    extracted_data, format_type = extract_data_from_image(image_path, "table")
    
    if format_type == "dataframe":
        return extracted_data
    else:
        # If we didn't get a dataframe directly, try to create one from the text
        try:
            # Check if there's a markdown table in the result
            if isinstance(extracted_data, str) and "|" in extracted_data and "-|-" in extracted_data.replace(" ", ""):
                # Parse markdown table
                lines = [line.strip() for line in extracted_data.split('\n') if line.strip() and '|' in line]
                
                # Skip separator lines
                lines = [line for line in lines if not all(c in '|-+ ' for c in line)]
                
                # Split by | and remove empty cells
                rows = [row.split('|') for row in lines]
                rows = [[cell.strip() for cell in row if cell.strip()] for row in rows]
                
                # First row as headers
                headers = rows[0] if rows else []
                data = rows[1:] if len(rows) > 1 else []
                
                # Create DataFrame
                return pd.DataFrame(data, columns=headers)
            
            # If no table found, return empty DataFrame
            return pd.DataFrame()
        
        except Exception as e:
            print(f"Error extracting table: {str(e)}")
            return pd.DataFrame()