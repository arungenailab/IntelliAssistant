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

# Import utility modules
from utils.gemini_helper import query_gemini, extract_visualization_parameters
from utils.conversation_manager import save_conversation, load_conversation_history, add_message_to_conversation
from utils.file_handler import process_uploaded_file, generate_preview
from utils.visualization import create_visualization, determine_best_visualization
from utils.data_processor import process_query, extract_features
from utils.admin_logger import log_action
from utils.database_connector import connect_to_database, list_tables, get_table_schema

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
                    st.experimental_rerun()
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

# Chat interface
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
                
                # Show feedback buttons if not already given
                message_idx = i
                if message_idx not in st.session_state.feedback:
                    col1, col2, col3 = st.columns([1, 1, 4])
                    with col1:
                        if st.button("👍", key=f"thumbs_up_{message_idx}"):
                            give_feedback(message_idx, "positive")
                    with col2:
                        if st.button("👎", key=f"thumbs_down_{message_idx}"):
                            give_feedback(message_idx, "negative")
                else:
                    st.write(f"Feedback: {st.session_state.feedback[message_idx]}")

# User input
user_input = st.chat_input("Ask a question about your data or type 'help' for suggestions")

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
    
    try:
        # Check if this is a data query
        data_query = False
        processing_result = None
        datasets_to_process = {}
        
        for keyword in ["show", "plot", "visualize", "analyze", "query", "select", "calculate", "compute"]:
            if keyword in user_input.lower():
                data_query = True
                break
        
        if data_query and st.session_state.current_data:
            # Try to process as a data query
            try:
                system_prompt = """
                You are an expert data analyst. Based on the user's query, generate a SQL-like query 
                to extract the relevant information from the available datasets. 
                
                Available datasets:
                """
                for name, df in st.session_state.current_data.items():
                    system_prompt += f"\n- {name}: {list(df.columns)}"
                
                system_prompt += """
                Return your response in this format:
                {
                    "query": "The SQL-like query to execute",
                    "visualization": "The type of visualization to create (bar, line, scatter, pie, etc.)",
                    "explanation": "Brief explanation of the analysis"
                }
                """
                
                # Extract SQL-like query using AI
                response = query_gemini(
                    user_query=user_input,
                    system_prompt=system_prompt
                )
                
                # Parse the response
                try:
                    parsed_response = json.loads(response)
                    
                    # Execute the generated query
                    sql_query = parsed_response.get("query", "")
                    if sql_query:
                        result, dataframes_used = process_query(
                            sql_query, 
                            st.session_state.current_data,
                            st.session_state.db_connection
                        )
                        
                        if not result.empty:
                            # Determine visualization type
                            vis_type = parsed_response.get("visualization", "")
                            if not vis_type:
                                vis_type = determine_best_visualization(result)
                            
                            # Create visualization
                            visualization = create_visualization(
                                result, 
                                vis_type, 
                                user_input
                            )
                            
                            # Prepare response
                            processing_result = {
                                "result": result,
                                "visualization": visualization,
                                "explanation": parsed_response.get("explanation", "")
                            }
                
                except Exception as e:
                    st.error(f"Error parsing AI response: {str(e)}")
            
            except Exception as e:
                st.error(f"Error processing data query: {str(e)}")
        
        # Generate AI response
        system_prompt = """
        You are an Analytical Chat Bot, an AI assistant specialized in data analysis and visualization.
        
        If the user's query is about data analysis, statistics, or visualization, provide a detailed 
        and helpful response. If the query is unclear, ask clarifying questions.
        
        Format your responses using markdown for better readability.
        """
        
        if st.session_state.current_data:
            system_prompt += "\n\nAvailable datasets:"
            for name, df in st.session_state.current_data.items():
                system_prompt += f"\n- {name}: {list(df.columns)}"
        
        if processing_result:
            system_prompt += f"""
            \n\nI've already analyzed the data based on the user's query. Here's the result:
            
            Result shape: {processing_result['result'].shape}
            
            Explanation: {processing_result['explanation']}
            
            Please enhance this explanation with more insights, but keep your response concise and focused on the data.
            """
        
        # Get response from AI
        response = query_gemini(
            user_query=user_input,
            system_prompt=system_prompt
        )
        
        # Create assistant message
        assistant_message = {
            "role": "assistant",
            "content": response
        }
        
        # Add visualization if available
        if processing_result and processing_result["visualization"]:
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
        
        # Add to chat history
        st.session_state.chat_history.append(assistant_message)
        
        # Save to conversation
        add_message_to_conversation(
            st.session_state.conversation_id,
            assistant_message
        )
    
    except Exception as e:
        error_message = f"I encountered an error while processing your request: {str(e)}"
        st.session_state.chat_history.append({"role": "assistant", "content": error_message})
        
        # Save to conversation
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

# Process user input when provided
if user_input:
    handle_query(user_input)
    
    # Force a rerun to update the chat display
    st.experimental_rerun()

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