import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import uuid
import base64
import plotly.express as px
import matplotlib.pyplot as plt
from datetime import datetime
from PIL import Image

# Import utility modules
from utils.gemini_helper import query_gemini, extract_visualization_parameters
from utils.conversation_manager import save_conversation, load_conversation_history, add_message_to_conversation
from utils.file_handler import process_uploaded_file, generate_preview
from utils.visualization import create_visualization, determine_best_visualization
from utils.data_processor import process_query, extract_features
from utils.admin_logger import log_action
from utils.database_connector import connect_to_database, list_tables, get_table_schema
from utils.image_analyzer import analyze_image, extract_data_from_image, analyze_image_data_trends

# Set page config
st.set_page_config(
    page_title="Analytical Chat Bot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_data" not in st.session_state:
    st.session_state.current_data = {}

if "db_connection" not in st.session_state:
    st.session_state.db_connection = None

if "feedback" not in st.session_state:
    st.session_state.feedback = {}

# Sidebar
with st.sidebar:
    st.title("Analytical Chat Bot")
    st.write("An AI-powered assistant for data analysis and visualization")
    
    st.divider()
    
    # File upload section
    st.subheader("Upload Data")
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "json"])
    
    if uploaded_file:
        try:
            df, file_type = process_uploaded_file(uploaded_file)
            
            # Generate a preview
            preview = generate_preview(df)
            
            # Store the dataframe
            dataset_name = st.text_input("Dataset Name", f"data_{len(st.session_state.current_data) + 1}")
            
            if st.button("Add Dataset"):
                if dataset_name in st.session_state.current_data:
                    st.warning(f"Dataset '{dataset_name}' already exists. Choose a different name.")
                else:
                    st.session_state.current_data[dataset_name] = df
                    st.success(f"Dataset '{dataset_name}' added successfully!")
                    
                    # Log the action
                    log_action(
                        st.session_state.user_id,
                        "upload_data",
                        {
                            "dataset_name": dataset_name,
                            "file_type": file_type,
                            "rows": df.shape[0],
                            "columns": df.shape[1]
                        }
                    )
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    
    st.divider()
    
    # Database connection section
    st.subheader("Database Connection")
    
    db_type = st.selectbox("Database Type", ["None", "PostgreSQL", "SQLite"])
    
    if db_type != "None":
        if st.button("Connect to Database"):
            try:
                st.session_state.db_connection = connect_to_database(db_type)
                
                # Get list of tables
                tables = list_tables(st.session_state.db_connection)
                
                st.success(f"Connected to {db_type} database!")
                st.write(f"Available tables: {', '.join(tables)}")
                
                # Log the action
                log_action(
                    st.session_state.user_id,
                    "connect_database",
                    {"database_type": db_type, "tables": tables}
                )
            
            except Exception as e:
                st.error(f"Error connecting to database: {str(e)}")
    
    st.divider()
    
    # Data explorer
    st.subheader("Available Datasets")
    
    if st.session_state.current_data:
        for name, df in st.session_state.current_data.items():
            with st.expander(f"{name} ({df.shape[0]} rows, {df.shape[1]} columns)"):
                st.dataframe(df.head(5))
                
                if st.button(f"Remove {name}", key=f"remove_{name}"):
                    del st.session_state.current_data[name]
                    st.rerun()
    else:
        st.info("No datasets available. Upload a file or connect to a database.")
    
    st.divider()
    
    # Admin section
    if st.checkbox("Show Admin Panel"):
        st.subheader("Admin Controls")
        
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.session_state.conversation_id = None
            st.success("Chat history cleared!")
        
        if st.button("Clear All Data"):
            st.session_state.current_data = {}
            st.session_state.db_connection = None
            st.success("All data cleared!")

# Main content area
st.title("Interactive Data Analysis")

# Create tabs for different functionality
tab1, tab2 = st.tabs(["Chat Interface", "Image Analysis"])

with tab2:
    st.header("Image Analysis")
    st.write("Upload an image for analysis or extract data from charts and tables.")
    
    # Image upload section
    uploaded_image = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"], key="image_uploader")
    
    if uploaded_image:
        # Display the uploaded image
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        
        # Save the image temporarily
        temp_image_path = f"temp_image_{uuid.uuid4()}.jpg"
        image.save(temp_image_path)
        
        # Analysis options
        analysis_type = st.radio(
            "Select Analysis Type",
            ["General Analysis", "Extract Table/Chart Data", "Data Trend Analysis"]
        )
        
        if st.button("Analyze Image"):
            with st.spinner("Analyzing image..."):
                try:
                    if analysis_type == "General Analysis":
                        # Perform general image analysis
                        analysis_result = analyze_image(temp_image_path)
                        st.write("### Analysis Results")
                        st.write(analysis_result)
                        
                        # Log the action
                        log_action(
                            st.session_state.user_id,
                            "image_analysis",
                            {"analysis_type": "general", "image_name": uploaded_image.name}
                        )
                    
                    elif analysis_type == "Extract Table/Chart Data":
                        # Extract data from table/chart
                        extraction_type = st.selectbox(
                            "What type of data to extract?",
                            ["table", "chart", "text", "form"]
                        )
                        
                        extracted_data, format_type = extract_data_from_image(temp_image_path, extraction_type)
                        
                        st.write("### Extracted Data")
                        if format_type == "dataframe" and isinstance(extracted_data, pd.DataFrame):
                            st.dataframe(extracted_data)
                            
                            # Option to add the extracted data as a dataset
                            if st.button("Add as Dataset"):
                                dataset_name = f"extracted_{extraction_type}_{len(st.session_state.current_data) + 1}"
                                st.session_state.current_data[dataset_name] = extracted_data
                                st.success(f"Added extracted data as dataset '{dataset_name}'")
                        else:
                            st.write(extracted_data)
                        
                        # Log the action
                        log_action(
                            st.session_state.user_id,
                            "image_data_extraction",
                            {
                                "extraction_type": extraction_type,
                                "image_name": uploaded_image.name,
                                "format": format_type
                            }
                        )
                    
                    else:  # Data Trend Analysis
                        # Analyze data trends in the image
                        trend_analysis = analyze_image_data_trends(temp_image_path)
                        
                        st.write("### Data Trend Analysis")
                        if "error" in trend_analysis:
                            st.error(trend_analysis["error"])
                        else:
                            if "chart_type" in trend_analysis:
                                st.write(f"**Chart Type:** {trend_analysis['chart_type']}")
                                st.write(f"**Main Trend:** {trend_analysis['main_trend']}")
                                
                                st.write("**Key Points:**")
                                key_points = trend_analysis.get('key_points', [])
                                if key_points and isinstance(key_points, list):
                                    for point in key_points:
                                        st.write(f"- {point}")
                                else:
                                    st.write("- No key points available")
                                
                                st.write("**Conclusions:**")
                                conclusions = trend_analysis.get('conclusions', [])
                                if conclusions and isinstance(conclusions, list):
                                    for conclusion in conclusions:
                                        st.write(f"- {conclusion}")
                                else:
                                    st.write("- No conclusions available")
                            else:
                                st.write(trend_analysis.get("analysis", "No analysis available"))
                            
                            # Display extracted data if available
                            if "extracted_data" in trend_analysis and trend_analysis["extracted_data"] is not None:
                                st.write("### Extracted Data")
                                extracted_df = pd.DataFrame(trend_analysis["extracted_data"])
                                st.dataframe(extracted_df)
                                
                                # Option to add the extracted data as a dataset
                                if st.button("Add as Dataset"):
                                    dataset_name = f"trend_data_{len(st.session_state.current_data) + 1}"
                                    st.session_state.current_data[dataset_name] = extracted_df
                                    st.success(f"Added trend data as dataset '{dataset_name}'")
                        
                        # Log the action
                        log_action(
                            st.session_state.user_id,
                            "image_trend_analysis",
                            {"image_name": uploaded_image.name}
                        )
                
                except Exception as e:
                    st.error(f"Error analyzing image: {str(e)}")
                
                # Clean up the temporary file
                try:
                    if os.path.exists(temp_image_path):
                        os.remove(temp_image_path)
                except:
                    pass
    else:
        # Example images
        st.write("### Try with example images")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Example 1: ACB Scope"):
                example_path = "attached_assets/IMG_20250311_215404247.jpg"
                if os.path.exists(example_path):
                    image = Image.open(example_path)
                    st.image(image, caption="ACB Scope Document", use_container_width=True)
                    
                    with st.spinner("Analyzing image..."):
                        analysis_result = analyze_image(example_path)
                        st.write("### Analysis Results")
                        st.write(analysis_result)
        
        with col2:
            if st.button("Example 2: ACB Features"):
                example_path = "attached_assets/IMG_20250311_215415678.jpg"
                if os.path.exists(example_path):
                    image = Image.open(example_path)
                    st.image(image, caption="ACB Features Document", use_container_width=True)
                    
                    with st.spinner("Analyzing image..."):
                        analysis_result = analyze_image(example_path)
                        st.write("### Analysis Results")
                        st.write(analysis_result)

# Chat interface in the first tab
with tab1:
    chat_container = st.container()

with chat_container:
    # Display chat history
    for i, message in enumerate(st.session_state.chat_history):
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])
                
                # Display any visualizations
                if "visualization" in message:
                    viz = message["visualization"]
                    st.plotly_chart(viz["fig"], use_container_width=True)
                
                # Remove feedback buttons to simplify the interface
                message_idx = i
                if message_idx in st.session_state.feedback:
                    st.write(f"Feedback: {st.session_state.feedback[message_idx]}")

# Define feedback function
def give_feedback(message_idx, feedback_type):
    """Record user feedback for a specific message."""
    st.session_state.feedback[message_idx] = feedback_type
    
    # Log the feedback
    log_action(
        st.session_state.user_id,
        "feedback",
        {
            "message_idx": message_idx,
            "feedback": feedback_type,
            "message": st.session_state.chat_history[message_idx]["content"]
        }
    )
    
    # Provide a thank you message
    if feedback_type == "positive":
        st.success("Thanks for the positive feedback!")
    else:
        st.warning("Thanks for the feedback. We'll try to improve!")

def handle_query(user_input):
    """Process the user query and generate a response."""
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Save conversation to file if needed
    if not st.session_state.conversation_id:
        st.session_state.conversation_id = save_conversation(
            st.session_state.user_id,
            st.session_state.chat_history
        )
    else:
        # Add to existing conversation
        add_message_to_conversation(
            st.session_state.conversation_id,
            {"role": "user", "content": user_input}
        )
    
    # Log the query
    log_action(
        st.session_state.user_id,
        "query",
        {"query": user_input}
    )
    
    # Get conversation context
    conversation_context = ""
    if len(st.session_state.chat_history) > 1:
        # Get last 5 messages for context
        context_messages = st.session_state.chat_history[-6:-1]
        conversation_context = "\n\nPrevious conversation:\n"
        for msg in context_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"]
            conversation_context += f"{role}: {content}\n"
    
    try:
        # Check if this is a data query
        data_query = False
        processing_result = None
        
        # Keywords that indicate a data query
        data_keywords = [
            "show", "plot", "visualize", "analyze", "query", "select", 
            "calculate", "compute", "compare", "trend", "distribution",
            "correlation", "graph", "chart"
        ]
        
        for keyword in data_keywords:
            if keyword.lower() in user_input.lower():
                data_query = True
                break
        
        if data_query and st.session_state.current_data:
            try:
                # Create system prompt with available data and conversation context
                system_prompt = get_data_analysis_prompt()
                
                # Add dataset information
                system_prompt += "\n\nAvailable datasets:"
                for name, df in st.session_state.current_data.items():
                    system_prompt += f"\n- {name}:"
                    system_prompt += f"\n  Columns: {list(df.columns)}"
                    system_prompt += f"\n  Types: {df.dtypes.to_dict()}"
                    system_prompt += f"\n  Sample: {df.head(2).to_dict()}"
                
                # Add conversation context
                system_prompt += f"\n\n{conversation_context}"
                
                # Debug logging
                st.write("Debug: Processing data query")
                
                # Get response from AI
                response = query_gemini(
                    user_query=user_input,
                    system_prompt=system_prompt
                )
                
                # Debug logging
                st.write("Debug: AI Response")
                st.write(response)
                
                # Process the response and create visualization
                if response:
                    try:
                # Parse the response
                        parsed_response = parse_ai_response(response)
                        
                        # Debug logging
                        if parsed_response:
                            st.write("Debug: Parsed response keys")
                            st.write(list(parsed_response.keys()))
                        
                        if parsed_response:
                            # Execute the query
                            result = execute_query(parsed_response, st.session_state.current_data)
                            
                            if result is not None and not result.empty:
                                # Display the result
                                st.write("### Query Result")
                                st.dataframe(result.head(10))
                                
                                # Create and display visualization
                                vis_type = parsed_response.get("visualization_type", "")
                                vis_params = parsed_response.get("visualization_params", {})
                                
                                visualization = create_and_display_visualization(
                                result, 
                                vis_type, 
                                    user_input,
                                    vis_params
                            )
                            
                            # Prepare response
                            processing_result = {
                                "result": result,
                                "visualization": visualization,
                                "explanation": parsed_response.get("explanation", "")
                            }
                
                except Exception as e:
                        st.error(f"Error processing AI response: {str(e)}")
            
            except Exception as e:
                st.error(f"Error processing data query: {str(e)}")
        
        # Generate final response
        if processing_result:
        assistant_message = {
            "role": "assistant",
                "content": processing_result["explanation"]
        }
        
            if "visualization" in processing_result and processing_result["visualization"]:
            assistant_message["visualization"] = processing_result["visualization"]
            
            # Log the visualization
            log_action(
                st.session_state.user_id,
                "visualization",
                {
                    "type": processing_result["visualization"]["type"],
                    "query": user_input
                }
            )
        else:
            # Handle non-data queries or failed data queries
            response = query_gemini(
                user_query=user_input,
                system_prompt=get_general_system_prompt() + conversation_context
            )
            
            assistant_message = {
                "role": "assistant",
                "content": response
            }
        
        # Add to chat history
        st.session_state.chat_history.append(assistant_message)
        
        # Save to conversation
        add_message_to_conversation(
            st.session_state.conversation_id,
            assistant_message
        )
    
    except Exception as e:
        handle_error(e, user_input)

def parse_ai_response(response):
    """Parse and validate the AI response."""
    try:
        # Debug logging
        st.write("Debug: Parsing AI response")
        
        # Extract JSON from response
        if isinstance(response, str):
            # Handle markdown code blocks
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                if json_end > json_start:
                    response = response[json_start:json_end].strip()
                    st.write("Debug: Extracted JSON from code block")
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                if json_end > json_start:
                    response = response[json_start:json_end].strip()
                    st.write("Debug: Extracted code block")
            
            # Try to find JSON object in the response
            json_pattern = r'\{(?:[^{}]|(?R))*\}'
            import re
            json_matches = re.findall(json_pattern, response)
            if json_matches:
                response = json_matches[0]
                st.write("Debug: Extracted JSON using regex")
        
        # Parse JSON
        try:
            parsed = json.loads(response)
            st.write("Debug: Successfully parsed JSON")
        except json.JSONDecodeError:
            # Try to clean the response
            cleaned_response = response.replace("'", '"')  # Replace single quotes with double quotes
            cleaned_response = re.sub(r'//.*?(\n|$)', '', cleaned_response)  # Remove comments
            parsed = json.loads(cleaned_response)
            st.write("Debug: Parsed JSON after cleaning")
        
        # Validate required fields
        required_fields = ["query", "visualization_type", "explanation"]
        missing_fields = [field for field in required_fields if field not in parsed]
        
        if missing_fields:
            st.warning(f"Warning: Missing required fields in AI response: {missing_fields}")
            
            # Try to fix missing fields with defaults
            if "query" not in parsed and "pandas_operation" in parsed:
                parsed["query"] = parsed["pandas_operation"]
            
            if "visualization_type" not in parsed and "visualization" in parsed:
                parsed["visualization_type"] = parsed["visualization"]
            
            # Check again after fixes
            missing_fields = [field for field in required_fields if field not in parsed]
            if missing_fields:
                st.error(f"Error: Still missing required fields: {missing_fields}")
                return None
        
        # Validate visualization parameters
        if "visualization_params" not in parsed:
            st.write("Debug: No visualization_params found, creating default")
            parsed["visualization_params"] = {}
        
        return parsed
    
    except Exception as e:
        st.error(f"Error parsing AI response: {str(e)}")
        st.write("Debug: Failed to parse response")
        st.write(response)
        return None

def execute_query(parsed_response, current_data):
    """Execute the query and return results."""
    try:
        # Debug logging
        st.write("Debug: Executing query")
        
        query = parsed_response.get("query", "")
        if not query or not isinstance(query, str):
            st.error("Invalid query in AI response")
            return None
        
        st.write(f"Debug: Query to execute: {query}")
        
        # Check if this is a pandas operation or SQL-like query
        if "SELECT" in query.upper() or "FROM" in query.upper():
            # Process as SQL-like query
            st.write("Debug: Processing as SQL-like query")
            result, _ = process_query(query, current_data, st.session_state.db_connection)
        else:
            # Process as pandas operation
            st.write("Debug: Processing as pandas operation")
            
            # Create a safe environment for execution
            local_vars = {'pd': pd, 'np': np}
            
            # Add dataframes to local variables
            for name, df in current_data.items():
                local_vars[name] = df
            
            # Execute the pandas operation
            try:
                # Replace common aggregation patterns
                if "groupby" in query and any(agg in query for agg in ["sum(", "mean(", "count("]):
                    # Convert SQL-like aggregation to pandas
                    query = query.replace("sum(", "sum()[")
                    query = query.replace("mean(", "mean()[")
                    query = query.replace("count(", "count()[")
                    query = query.replace(")", "]")
                
                # Execute the query
                result = eval(query, {"__builtins__": {}}, local_vars)
                
                # Convert to DataFrame if result is a Series
                if isinstance(result, pd.Series):
                    result = result.reset_index()
                
                # Ensure we have a DataFrame
                if not isinstance(result, pd.DataFrame):
                    st.error(f"Query result is not a DataFrame: {type(result)}")
                    return None
                
            except Exception as e:
                st.error(f"Error executing pandas operation: {str(e)}")
                
                # Try to execute as a SQL-like query as fallback
                st.write("Debug: Falling back to SQL-like query")
                try:
                    result, _ = process_query(query, current_data, st.session_state.db_connection)
                except Exception as e2:
                    st.error(f"Fallback also failed: {str(e2)}")
                    return None
        
        # Debug logging
        if result is not None:
            st.write(f"Debug: Query result shape: {result.shape}")
        
        return result
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        return None

def get_general_system_prompt():
    """Get the general system prompt for non-data queries."""
    return """You are an Analytical Chat Bot, an AI assistant specialized in data analysis and visualization.
    Provide complete answers that anticipate user needs without asking follow-up questions.
    Format your responses using markdown for better readability."""

def handle_error(e, user_input):
    """Handle errors in a consistent way."""
        error_message = f"I encountered an error while processing your request: {str(e)}"
        st.session_state.chat_history.append({"role": "assistant", "content": error_message})
        
    # Save to conversation if available
    if st.session_state.conversation_id:
        add_message_to_conversation(
            st.session_state.conversation_id,
            {"role": "assistant", "content": error_message}
        )
        
        # Log the error
        log_action(
            st.session_state.user_id,
            "error",
            {"error": str(e), "query": user_input}
        )
    
    # Display the error in the UI
    st.error(f"Error: {str(e)}")

def create_and_display_visualization(result_df, vis_type, user_query, vis_params=None):
    """Create and display a visualization with proper error handling."""
    try:
        # Debug logging
        st.write(f"Debug: Creating visualization of type '{vis_type}'")
        st.write(f"Debug: Data shape: {result_df.shape}")
        
        # Create the visualization
        visualization = create_visualization(
            result_df,
            vis_type,
            user_query,
            vis_params
        )
        
        # Debug: Check if visualization was created
        if visualization and "fig" in visualization:
            st.write("Debug: Visualization created successfully")
            
            # Display the visualization
            st.plotly_chart(visualization["fig"], use_container_width=True)
            return visualization
        else:
            st.warning("Failed to create visualization. Please try a different query.")
            return None
            
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")
        return None

def get_data_analysis_prompt():
    """Get the system prompt for data analysis queries."""
    return """You are an expert data analyst. Based on the user's query and conversation context,
    generate appropriate pandas operations to analyze the data and create visualizations.
    
    APPROACH:
    1. INTERNALLY analyze the query and context
    2. Generate pandas-compatible operations
    3. Choose appropriate visualization
    4. Return complete configuration
    
    Your response MUST be a valid JSON object with the following structure:
    {
        "query": "The pandas operation to execute (e.g., df.groupby('column').sum())",
        "visualization_type": "bar|line|scatter|pie|histogram|box",
        "explanation": "A detailed explanation of the analysis and insights",
        "visualization_params": {
            "x": "column_name_for_x_axis",
            "y": "column_name_for_y_axis",
            "title": "Clear and descriptive title",
            "color": "column_name_for_color_grouping",  // Optional
            "orientation": "horizontal|vertical",  // Optional
            "aggregation": "sum|mean|count"  // Optional
        }
    }
    
    IMPORTANT:
    1. Return ONLY a valid JSON object
    2. DO NOT include any explanatory text or code snippets outside the JSON
    3. DO NOT use markdown code blocks
    4. Ensure all column names exactly match the available columns
    5. Include all required parameters for the chosen visualization type
    """

# User input
user_input = st.chat_input("Ask a question about your data or type 'help' for suggestions")

# Process user input when provided
if user_input:
    handle_query(user_input)
    
    # Force a rerun to update the chat display
    st.rerun()

# Welcome message for first-time users
if not st.session_state.chat_history:
    welcome_message = """
    # 👋 Welcome to the Analytical Chat Bot!
    
    I'm here to help you analyze and visualize your data. Here's what you can do:
    
    * **Upload data** using the sidebar
    * **Ask questions** about your data
    * **Request visualizations** like charts and plots
    * **Perform analysis** with natural language
    
    Try asking something like:
    * "Show me a summary of my data"
    * "Create a bar chart of sales by region"
    * "What are the trends in this dataset?"
    * "Calculate correlation between price and sales"
    
    Need help? Just type "help" for more suggestions.
    """
    
    st.markdown(welcome_message)