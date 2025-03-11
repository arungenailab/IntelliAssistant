import os
import base64
import google.generativeai as genai
from PIL import Image
import io
import pandas as pd
import re

# Use the same Gemini API key from gemini_helper
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

# Configure the API
genai.configure(api_key=GEMINI_API_KEY)

# Default model for image analysis
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
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image(image_path, prompt=None):
    """
    Analyze an image using Gemini's multimodal capabilities.
    
    Args:
        image_path (str): Path to the image file
        prompt (str, optional): Specific prompt for image analysis
        
    Returns:
        str: Analysis result
    """
    try:
        # Create model instance
        model = genai.GenerativeModel(DEFAULT_VISION_MODEL)
        
        # Encode image
        encoded_image = encode_image_to_base64(image_path)
        
        # Prepare the prompt
        if not prompt:
            prompt = "Analyze this image in detail. Describe what you see, including any text, objects, people, or interesting elements."
        
        # Create the message with text and image parts
        message = {
            "role": "user",
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": encoded_image
                    }
                }
            ]
        }
        
        # Generate content
        response = model.generate_content([message])
        
        return response.text
    
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

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
    try:
        # Create model instance
        model = genai.GenerativeModel(DEFAULT_VISION_MODEL)
        
        # Encode image
        encoded_image = encode_image_to_base64(image_path)
        
        # Create specific prompt based on extraction type
        if extraction_type == "table":
            prompt = """
            Extract the data from this table image into a structured format. 
            Return the data as a CSV with headers. 
            Format your response as follows:
            
            EXTRACTED_DATA:
            column1,column2,column3
            value1,value2,value3
            value4,value5,value6
            
            Do not include any explanations, just the CSV data.
            """
        elif extraction_type == "chart":
            prompt = """
            Extract the data represented in this chart or graph.
            Return the underlying data as a CSV with headers.
            Format your response as follows:
            
            EXTRACTED_DATA:
            x_axis,y_axis
            value1,value2
            value3,value4
            
            Include a brief description of what the chart represents.
            """
        elif extraction_type == "form":
            prompt = """
            Extract all form fields and their values from this image.
            Format your response as follows:
            
            EXTRACTED_DATA:
            field1,value1
            field2,value2
            field3,value3
            
            Do not include any explanations, just the extracted fields and values.
            """
        else:  # Default to text extraction
            prompt = """
            Extract all text from this image.
            Format your response as follows:
            
            EXTRACTED_TEXT:
            [all extracted text here]
            
            Preserve paragraphs, bullet points, and other formatting elements.
            """
        
        # Create the message with text and image parts
        message = {
            "role": "user",
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": encoded_image
                    }
                }
            ]
        }
        
        # Generate content
        response = model.generate_content([message])
        response_text = response.text
        
        # Process the response based on extraction type
        if extraction_type in ["table", "chart", "form"]:
            # Try to extract CSV data
            csv_pattern = r"EXTRACTED_DATA:[\r\n]+([\s\S]+)"
            csv_match = re.search(csv_pattern, response_text)
            
            if csv_match:
                csv_text = csv_match.group(1).strip()
                try:
                    # Convert CSV to DataFrame
                    df = pd.read_csv(io.StringIO(csv_text), sep=",", skipinitialspace=True)
                    return df, "dataframe"
                except Exception as e:
                    # If CSV parsing fails, return the text
                    return csv_text, "text"
            else:
                # If no CSV format found, return the raw response
                return response_text, "text"
        else:
            # For text extraction
            text_pattern = r"EXTRACTED_TEXT:[\r\n]+([\s\S]+)"
            text_match = re.search(text_pattern, response_text)
            
            if text_match:
                return text_match.group(1).strip(), "text"
            else:
                return response_text, "text"
    
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
    try:
        # First, extract the data from the chart
        data, format_type = extract_data_from_image(image_path, extraction_type="chart")
        
        # Now ask for insights based on the extracted data or directly from the image
        insight_prompt = """
        This image contains a chart or graph. Analyze it and provide the following insights:
        
        1. What type of chart/graph is this?
        2. What is the main trend or pattern shown?
        3. What are the key data points or outliers?
        4. What conclusions can be drawn from this visualization?
        
        Format your response as JSON with the following structure:
        {
            "chart_type": "type of chart/graph",
            "main_trend": "description of main trend",
            "key_points": ["point 1", "point 2", "point 3"],
            "conclusions": ["conclusion 1", "conclusion 2"]
        }
        """
        
        # Create model instance
        model = genai.GenerativeModel(DEFAULT_VISION_MODEL)
        
        # Encode image
        encoded_image = encode_image_to_base64(image_path)
        
        # Create the message with text and image parts
        message = {
            "role": "user",
            "parts": [
                {"text": insight_prompt},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": encoded_image
                    }
                }
            ]
        }
        
        # Generate content
        response = model.generate_content([message])
        response_text = response.text
        
        # Try to extract JSON
        try:
            # Find JSON pattern
            json_pattern = r"\{[\s\S]*\}"
            json_match = re.search(json_pattern, response_text)
            
            if json_match:
                import json
                insights = json.loads(json_match.group(0))
                # Add the extracted data if available
                if format_type == "dataframe":
                    insights["extracted_data"] = data.to_dict(orient="records")
                return insights
        except:
            pass
        
        # If JSON extraction fails, return a simpler structure
        return {
            "analysis": response_text,
            "extracted_data": data if format_type == "dataframe" else None
        }
    
    except Exception as e:
        return {
            "error": f"Error analyzing image data trends: {str(e)}"
        }