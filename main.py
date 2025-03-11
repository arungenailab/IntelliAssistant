import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import base64
from datetime import datetime
import plotly.express as px
import matplotlib.pyplot as plt
import uuid
from io import BytesIO

# Import local utility modules
from utils.database_connector import connect_to_database, execute_query, list_tables
from utils.file_handler import process_uploaded_file, generate_preview, dataframe_to_csv
from utils.data_processor import process_query
from utils.gemini_helper import query_gemini, generate_sql_query, suggest_query_improvements
from utils.visualization import create_visualization, determine_best_visualization
from utils.conversation_manager import save_conversation, load_conversation_history, add_message_to_conversation
from utils.admin_logger import log_action

# Check for GEMINI_API_KEY
if not os.environ.get("GEMINI_API_KEY"):
    st.warning("⚠️ GEMINI_API_KEY is not set. Some functionality will be limited. Please add your Gemini API key in the settings.")

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "dataframes" not in st.session_state:
    st.session_state.dataframes = {}

if "db_connection" not in st.session_state:
    st.session_state.db_connection = None

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "sql_query" not in st.session_state:
    st.session_state.sql_query = None

# Title and description
st.title("Analytical Chat Bot")
st.subheader("Ask questions about your data in natural language")

# Sidebar for data sources and settings
with st.sidebar:
    st.header("Data Sources")
    
    # Option to upload files
    st.subheader("Upload Data Files")
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "json"])
    
    if uploaded_file is not None:
        try:
            df, file_type = process_uploaded_file(uploaded_file)
            
            # Generate dataset name
            dataset_name = f"{uploaded_file.name.split('.')[0]}_{len(st.session_state.dataframes) + 1}"
            st.success(f"✅ Uploaded {uploaded_file.name} ({file_type})")
            
            # Add to session state
            st.session_state.dataframes[dataset_name] = df
            
            # Log the action
            log_action(
                st.session_state.user_id,
                "file_upload",
                {"filename": uploaded_file.name, "type": file_type, "rows": len(df), "columns": len(df.columns)}
            )
        except Exception as e:
            st.error(f"Error uploading file: {str(e)}")
    
    # Database connection
    st.subheader("Connect to Database")
    db_type = st.selectbox("Database Type", ["PostgreSQL", "MySQL", "SQLite"], index=0)
    
    if st.button("Connect to Database"):
        try:
            conn = connect_to_database(db_type)
            st.session_state.db_connection = conn
            st.success(f"✅ Connected to {db_type} database")
            
            # Show available tables
            tables = list_tables(conn)
            if tables:
                st.write(f"Available tables: {', '.join(tables)}")
            
            # Log the action
            log_action(
                st.session_state.user_id,
                "database_connect",
                {"type": db_type, "tables_count": len(tables) if tables else 0}
            )
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")
    
    # Show loaded dataframes
    if st.session_state.dataframes:
        st.subheader("Loaded Datasets")
        for name, df in st.session_state.dataframes.items():
            with st.expander(f"{name} ({len(df)} rows, {len(df.columns)} columns)"):
                st.dataframe(df.head(3))
                
                # Add download button
                csv_data = dataframe_to_csv(df)
                download_link = f'<a href="data:file/csv;base64,{csv_data}" download="{name}.csv">Download CSV</a>'
                st.markdown(download_link, unsafe_allow_html=True)
    
    # Settings section
    st.header("Settings")
    
    # Add API key input
    gemini_key = st.text_input("Gemini API Key", type="password", 
                             value=os.environ.get("GEMINI_API_KEY", ""))
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        if "show_api_success" not in st.session_state:
            st.success("✅ API key set successfully")
            st.session_state.show_api_success = True
    
    # Clear conversation
    if st.button("Clear Conversation"):
        st.session_state.chat_history = []
        st.session_state.conversation_id = None
        st.success("Conversation cleared")

# Function to give feedback on responses
def give_feedback(message_idx, feedback_type):
    if 0 <= message_idx < len(st.session_state.chat_history):
        if "feedback" not in st.session_state.chat_history[message_idx]:
            st.session_state.chat_history[message_idx]["feedback"] = feedback_type
            
            # Log the feedback
            log_action(
                st.session_state.user_id,
                "feedback",
                {
                    "message_idx": message_idx,
                    "feedback": feedback_type,
                    "query": st.session_state.chat_history[message_idx].get("content", "")
                }
            )
            
            # If conversation is saved, update it
            if st.session_state.conversation_id:
                add_message_to_conversation(
                    st.session_state.conversation_id,
                    st.session_state.chat_history[message_idx]
                )
            
            st.experimental_rerun()

# Function to handle user queries
def handle_query(user_input):
    if not user_input.strip():
        return
    
    # Add user message to chat history
    user_message = {"role": "user", "content": user_input, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    st.session_state.chat_history.append(user_message)
    
    # Log the query
    log_action(
        st.session_state.user_id,
        "query",
        {"query": user_input}
    )
    
    # Process the query
    try:
        # Determine available data sources
        available_sources = list(st.session_state.dataframes.keys())
        
        # If connected to database, add tables as sources
        if st.session_state.db_connection:
            tables = list_tables(st.session_state.db_connection)
            available_sources.extend(tables)
        
        # Generate a data context for the AI
        data_context = {}
        for name, df in st.session_state.dataframes.items():
            data_context[name] = {
                "columns": df.columns.tolist(),
                "rows": len(df),
                "dtypes": {col: str(df[col].dtype) for col in df.columns}
            }
        
        # Generate SQL-like query using Gemini
        is_visualization_request = any(keyword in user_input.lower() for keyword in [
            "plot", "chart", "graph", "visualize", "visualization", "show me", "display"
        ])
        
        if is_visualization_request:
            # If it's a visualization request, we need to first get the data
            # then determine the visualization type
            sql_query = generate_sql_query(
                user_input,
                available_sources,
                data_context
            )
            
            # Store the generated SQL query
            st.session_state.sql_query = sql_query
            
            # Execute the query to get data
            result_df, sources_used = process_query(
                sql_query,
                st.session_state.dataframes,
                st.session_state.db_connection
            )
            
            # Determine the best visualization type
            vis_type = determine_best_visualization(result_df)
            
            # Create the visualization
            viz_result = create_visualization(
                result_df,
                vis_type,
                user_input
            )
            
            # Store the result
            st.session_state.current_result = {
                "type": "visualization",
                "data": result_df,
                "visualization": viz_result,
                "sources_used": sources_used
            }
            
            # Create a response message
            if viz_result:
                # Use Gemini to generate an analysis
                analysis_prompt = f"""
                Analyze this data visualization and provide insights:
                
                Query: {user_input}
                Visualization Type: {viz_result['type']}
                Data:
                {result_df.head(10).to_markdown() if len(result_df) > 10 else result_df.to_markdown()}
                
                Provide 3-5 key insights from this visualization in bullet points.
                """
                
                analysis = query_gemini(analysis_prompt)
                
                response_content = f"""
                📊 **Visualization Created**
                
                *Query interpreted as:* `{sql_query}`
                
                **Analysis:**
                {analysis}
                """
            else:
                response_content = f"""
                I couldn't create a visualization for your query.
                
                *Query interpreted as:* `{sql_query}`
                
                Please try a different query or check if you have relevant data loaded.
                """
            
        else:
            # For non-visualization queries, handle as regular data query
            sql_query = generate_sql_query(
                user_input,
                available_sources,
                data_context
            )
            
            # Store the generated SQL query
            st.session_state.sql_query = sql_query
            
            # Execute the query
            result_df, sources_used = process_query(
                sql_query,
                st.session_state.dataframes,
                st.session_state.db_connection
            )
            
            # Store the result
            st.session_state.current_result = {
                "type": "data",
                "data": result_df,
                "sources_used": sources_used
            }
            
            # Create a response message based on the result
            if result_df is not None and not result_df.empty:
                # Use Gemini to analyze the results
                analysis_prompt = f"""
                Analyze this data and provide insights:
                
                Query: {user_input}
                Data:
                {result_df.head(10).to_markdown() if len(result_df) > 10 else result_df.to_markdown()}
                
                Provide a concise summary of the results and 2-3 key insights.
                """
                
                analysis = query_gemini(analysis_prompt)
                
                response_content = f"""
                📋 **Query Results** (Showing {min(5, len(result_df))} of {len(result_df)} rows)
                
                *Query interpreted as:* `{sql_query}`
                
                **Analysis:**
                {analysis}
                """
            else:
                response_content = f"""
                I couldn't find any results for your query.
                
                *Query interpreted as:* `{sql_query}`
                
                Please try a different query or check if you have relevant data loaded.
                """
        
        # Add bot response to chat history
        bot_message = {
            "role": "assistant",
            "content": response_content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": {
                "sql_query": sql_query,
                "sources_used": sources_used
            }
        }
        st.session_state.chat_history.append(bot_message)
        
        # Save conversation if not already saved
        if not st.session_state.conversation_id:
            st.session_state.conversation_id = save_conversation(
                st.session_state.user_id,
                st.session_state.chat_history
            )
        else:
            # Update existing conversation
            add_message_to_conversation(
                st.session_state.conversation_id,
                bot_message
            )
        
    except Exception as e:
        # Log the error
        log_action(
            st.session_state.user_id,
            "error",
            {"query": user_input, "error": str(e)}
        )
        
        # Add error message to chat history
        error_message = {
            "role": "assistant",
            "content": f"""
            I encountered an error processing your query:
            ```
            {str(e)}
            ```
            
            Please try rephrasing your question or check if you have the necessary data loaded.
            """,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": True
        }
        st.session_state.chat_history.append(error_message)

# Main chat interface
st.header("Chat")

# Display chat messages
for i, message in enumerate(st.session_state.chat_history):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Display feedback buttons for assistant messages
        if message["role"] == "assistant" and message.get("error", False) is False:
            col1, col2 = st.columns([1, 10])
            with col1:
                # Thumbs up button
                if st.button("👍", key=f"thumbs_up_{i}", help="This was helpful"):
                    give_feedback(i, "positive")
                
                # Thumbs down button
                if st.button("👎", key=f"thumbs_down_{i}", help="This wasn't helpful"):
                    give_feedback(i, "negative")
            
            # Display feedback if already given
            if "feedback" in message:
                feedback_text = "You found this helpful" if message["feedback"] == "positive" else "You found this unhelpful"
                st.caption(f"*{feedback_text}*")

# Display current result if applicable
if st.session_state.current_result:
    result = st.session_state.current_result
    
    if result["type"] == "visualization" and result.get("visualization"):
        with st.expander("Show Visualization", expanded=True):
            viz = result["visualization"]
            st.plotly_chart(viz["fig"], use_container_width=True)
            
            # Show the data used
            if result["data"] is not None and not result["data"].empty:
                with st.expander("View Data"):
                    st.dataframe(result["data"])
    
    elif result["type"] == "data" and result["data"] is not None and not result["data"].empty:
        with st.expander("Show Results Table", expanded=True):
            st.dataframe(result["data"])
            
            # Add download option
            csv_data = dataframe_to_csv(result["data"])
            st.download_button(
                label="Download Results",
                data=f"data:file/csv;base64,{csv_data}",
                file_name="query_results.csv",
                mime="text/csv",
            )

# Chat input
user_input = st.chat_input("Ask a question about your data...")

if user_input:
    handle_query(user_input)

# Footer
st.markdown("---")
st.markdown("### Example Queries")
st.markdown("""
- "Show me the top 5 records in dataset_name"
- "Calculate the average of column_name grouped by category_column"
- "Create a bar chart of sales by region"
- "What's the correlation between price and quantity?"
- "Identify outliers in the numeric columns"
""")

# Add a version number
st.sidebar.markdown("---")
st.sidebar.caption("Analytical Chat Bot v1.0.0")
st.sidebar.caption(f"User ID: {st.session_state.user_id}")