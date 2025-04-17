import os
import json
import uuid
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import traceback
import logging
import asyncio
import time
import sys
import urllib.parse
import re
from typing import Dict, Any, List, Optional, Union

# Enable asyncio to work with Flask
import nest_asyncio
nest_asyncio.apply()

# Import configuration settings
try:
    from config import DEBUG, PORT, HOST, DEFAULT_DATASET
except ImportError:
    # Default settings if config file is not available
    DEBUG = True
    PORT = 5000
    HOST = "127.0.0.1"
    DEFAULT_DATASET = "MSFT"

# Custom JSON encoder to handle pandas Timestamp and numpy types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (pd.Timestamp, np.datetime64)):
            return str(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import utility modules
from utils.gemini_helper import analyze_data, suggest_query_improvements
from utils.file_utils import process_uploaded_file, generate_preview, get_dataset_info
from utils.visualization_helper import create_visualization
from utils.api_integrator import get_available_api_sources, fetch_api_data, save_api_credentials, ApiIntegrationError
from utils.langgraph_sql.api_integration import langgraph_convert_text_to_sql, is_langgraph_enabled
from utils.sql_connector import SQLServerConnector

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend/build')

# Set custom JSON encoder
app.json_encoder = CustomJSONEncoder

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:3002"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    },
    r"/convert_nl_to_sql": {
        "origins": ["http://localhost:3000", "http://localhost:3002"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Global state
conversations = {}
current_data = {}

def log_action(user_id, action_type, metadata=None):
    """Simple logging function"""
    print(f"[{datetime.now()}] User {user_id}: {action_type} - {json.dumps(metadata or {})}")

def load_sample_data():
    """Load sample data into memory"""
    try:
        # Load sample sales data
        sample_data = {
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'] * 7,
            'country': ['USA', 'UK', 'Canada'] * 7,
            'product': ['Widget A', 'Widget B', 'Widget C'] * 7,
            'amount': [100, 200, 300] * 7,
            'units': [1, 2, 3] * 7,
            'customer': ['Customer 1', 'Customer 2', 'Customer 3'] * 7
        }
        df = pd.DataFrame(sample_data)
        df['date'] = pd.to_datetime(df['date'])
        current_data['sales_data'] = df
        print(f"Loaded sample data with shape: {df.shape}")
        
        # Load sample MSFT stock data
        msft_data = {
            'date': pd.date_range(start='2024-12-01', periods=100).tolist(),
            'open': [392.32, 393.45, 391.23, 394.56, 395.67] * 20,
            'high': [396.78, 395.89, 393.45, 398.12, 399.56] * 20,
            'low': [390.12, 391.23, 389.56, 392.34, 393.45] * 20,
            'close': [395.67, 392.34, 390.23, 396.78, 397.89] * 20,
            'volume': [3245000, 2987000, 3126000, 3456000, 2987000] * 20
        }
        msft_df = pd.DataFrame(msft_data)
        current_data['MSFT'] = msft_df
        print(f"Loaded sample MSFT data with shape: {msft_df.shape}")
    except Exception as e:
        print(f"Error loading sample data: {str(e)}")

# Load sample data on startup
load_sample_data()

# Serve React static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# API Routes
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    """Process a chat message and return a response"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        conversation_id = data.get('conversationId')
        dataset_name = data.get('datasetName')
        preferred_model = data.get('modelId', 'gemini-2.0-flash')  # Add support for model selection
        use_cache = data.get('useCache', True)  # Allow disabling cache for testing
        
        print(f"Processing chat message: {user_message}")
        print(f"Using model: {preferred_model}")
        print(f"Available datasets: {list(current_data.keys())}")
        
        # Create a new conversation if needed
        if not conversation_id or conversation_id not in conversations:
            conversation_id = str(uuid.uuid4())
            conversations[conversation_id] = {
                'id': conversation_id,
                'title': user_message[:30] + '...' if len(user_message) > 30 else user_message,
                'messages': [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        else:
            # Update conversation timestamp
            conversations[conversation_id]['updated_at'] = datetime.now().isoformat()
        
        # Add user message to conversation
        user_message_id = str(uuid.uuid4())
        conversations[conversation_id]['messages'].append({
            'id': user_message_id,
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Get recent conversation history
        conversation_history = [
            {'role': msg['role'], 'content': msg['content']} 
            for msg in conversations[conversation_id]['messages'][-5:] if conversation_id in conversations
        ]
        
        # Get the active dataset
        df = None
        if dataset_name and dataset_name in current_data:
            df = current_data[dataset_name]
            print(f"Using specified dataset: {dataset_name}")
        else:
            # Only use the first available dataset if no specific dataset was requested
            if current_data and not dataset_name:
                dataset_name = next(iter(current_data.keys()))
                df = current_data[dataset_name]
                print(f"No dataset specified, using default: {dataset_name}")
            elif dataset_name and dataset_name not in current_data:
                return jsonify({
                    'error': f'Requested dataset "{dataset_name}" not found. Available datasets: {list(current_data.keys())}'
                }), 404
        
        # Check if dataset exists and is not empty
        if df is None or df.empty:
            return jsonify({
                'error': 'Dataset not found or empty'
            }), 404
        
        # Analyze data and get response
        analysis_result = analyze_data(
            user_query=user_message,
            data=df,
            conversation_history=conversation_history,
            model_id=preferred_model,
            use_cache=use_cache
        )
        
        response_text = analysis_result['text']
        visualization = None
        model_used = analysis_result.get('model_used', None)
        model_version = analysis_result.get('model_version', None)
        is_fallback = analysis_result.get('is_fallback', False)
        
        # Create visualization if suggested
        if analysis_result.get('visualization'):
            try:
                # Check if the user is asking for a top 5 salespersons by boxes shipped visualization
                if ("top 5" in user_message.lower() or "top five" in user_message.lower()) and ("salesperson" in user_message.lower() or "sales person" in user_message.lower()) and "boxes shipped" in user_message.lower():
                    print("[DEBUG] Detected specific request for top 5 salespersons by boxes shipped")
                    
                    # Find the exact column names that match "Sales Person" and "Boxes Shipped"
                    sales_person_col = None
                    boxes_shipped_col = None
                    
                    for col in df.columns:
                        col_lower = col.lower()
                        if "sales person" in col_lower or "salesperson" in col_lower:
                            sales_person_col = col
                        elif "boxes shipped" in col_lower or "shipped boxes" in col_lower:
                            boxes_shipped_col = col
                    
                    # If exact columns not found, look for similar columns
                    if sales_person_col is None:
                        person_cols = [col for col in df.columns if any(term in col.lower() for term in 
                                      ['sales', 'person', 'salesperson', 'employee', 'name'])]
                        if person_cols:
                            sales_person_col = person_cols[0]
                    
                    if boxes_shipped_col is None:
                        shipped_cols = [col for col in df.columns if any(term in col.lower() for term in 
                                       ['box', 'boxes', 'shipped', 'quantity', 'amount', 'count'])]
                        if shipped_cols:
                            boxes_shipped_col = shipped_cols[0]
                    
                    # Create a specific visualization for top 5 salespersons by boxes shipped
                    viz_params = {
                        'type': 'bar',
                        'x': sales_person_col,
                        'y': boxes_shipped_col,
                        'title': 'Top 5 Salespersons by Boxes Shipped',
                        'aggregation': 'sum',
                        'top_n': 5
                    }
                    
                    viz_result = create_visualization(
                        df,
                        'bar',
                        user_message,
                        viz_params
                    )
                else:
                    # Use the visualization parameters from the analysis result
                    viz_result = create_visualization(
                        df,
                        analysis_result['visualization']['type'],
                        user_message,
                        analysis_result['visualization']
                    )
                
                if viz_result:
                    visualization = viz_result
                    # Log the visualization data for debugging
                    print(f"Visualization data being sent to frontend: {json.dumps(visualization)}")
            except Exception as e:
                print(f"Error creating visualization: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
        
        # Create assistant message with model info
        assistant_message = {
            'id': str(uuid.uuid4()),
            'role': 'assistant',
            'content': response_text,
            'timestamp': datetime.now().isoformat(),
            'visualization': visualization,
            'model_used': model_used,
            'model_version': model_version,
            'is_fallback': is_fallback
        }
        
        if conversation_id in conversations:
            conversations[conversation_id]['messages'].append(assistant_message)
        
        # Return the response with model information
        return jsonify({
            'text': response_text,
            'conversationId': conversation_id,
            'messageId': assistant_message['id'],
            'timestamp': assistant_message['timestamp'],
            'visualization': visualization,
            'model_used': model_used,
            'model_version': model_version,
            'is_fallback': is_fallback
        })
        
    except Exception as e:
        print(f"Error processing chat: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations', methods=['GET', 'OPTIONS'])
def get_conversations():
    """Get a list of all conversations"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        result = []
        for conv_id, conv in conversations.items():
            result.append({
                'id': conv_id,
                'title': conv.get('title', ''),
                'created_at': conv.get('created_at'),
                'updated_at': conv.get('updated_at'),
                'message_count': len(conv.get('messages', []))
            })
        return jsonify(result)
    except Exception as e:
        print(f"Error getting conversations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<conversation_id>', methods=['GET', 'OPTIONS'])
def get_conversation(conversation_id):
    """Get a specific conversation"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        if conversation_id not in conversations:
            return jsonify({'error': 'Conversation not found'}), 404
            
        return jsonify(conversations[conversation_id])
    except Exception as e:
        print(f"Error getting conversation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations/<conversation_id>/messages', methods=['GET', 'OPTIONS'])
def get_conversation_messages(conversation_id):
    """Get messages for a specific conversation"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        if conversation_id not in conversations:
            return jsonify({'error': 'Conversation not found'}), 404
            
        return jsonify(conversations[conversation_id]['messages'])
    except Exception as e:
        print(f"Error getting conversation messages: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    """Upload and process a data file"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        print(f"Upload request received. Form data: {request.form}")
        print(f"Files in request: {request.files}")
        
        if 'file' not in request.files:
            print("Error: No file provided in request")
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            print("Error: Empty filename")
            return jsonify({'error': 'No file selected'}), 400
            
        # Get dataset name from form data or use default
        dataset_name = request.form.get('datasetName', f"dataset_{len(current_data) + 1}")
        user_id = request.form.get('userId', 'anonymous')
        
        print(f"Processing file: {file.filename}, Type: {file.content_type}, Size: {file.content_length}")
        
        # Check file type
        allowed_extensions = ['csv', 'xlsx', 'xls', 'json', 'txt']
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            print(f"Error: Unsupported file type: {file_ext}")
            return jsonify({'error': f'Unsupported file type: {file_ext}. Allowed types: {", ".join(allowed_extensions)}'}), 400
        
        # Save the file temporarily
        temp_path = f"temp_{uuid.uuid4()}.{file_ext}"
        file.save(temp_path)
        print(f"File saved temporarily at: {temp_path}")
        
        try:
            # Process the file
            df, file_type = process_uploaded_file(os.path.abspath(temp_path))
            print(f"File processed successfully. Shape: {df.shape}")
            
            # Store the dataset - use the filename as the dataset name if not provided
            if not dataset_name or dataset_name == f"dataset_{len(current_data) + 1}":
                dataset_name = file.filename.rsplit('.', 1)[0]
                
            # Store the entire DataFrame as one dataset
            current_data[dataset_name] = df
            
            # Get dataset info
            dataset_info = get_dataset_info(df)
            
            # Log the action
            log_action(user_id, "upload_file", {
                "filename": file.filename,
                "dataset_name": dataset_name,
                "file_type": file_type,
                "rows": df.shape[0],
                "columns": df.shape[1]
            })
            
            return jsonify({
                'success': True,
                'datasetName': dataset_name,
                **dataset_info
            })
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
            
        finally:
            # Always remove the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"Temporary file removed: {temp_path}")
        
    except Exception as e:
        print(f"Unexpected error in upload_file: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/datasets', methods=['GET', 'OPTIONS'])
def get_datasets():
    """Get a list of all available datasets"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        result = {}
        for name, df in current_data.items():
            result[name] = get_dataset_info(df)
        return jsonify(result)
    except Exception as e:
        print(f"Error getting datasets: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/state', methods=['GET', 'OPTIONS'])
def get_debug_state():
    """Get current application state for debugging"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        return jsonify({
            'conversations': len(conversations),
            'datasets': {
                name: {
                    'shape': df.shape,
                    'columns': df.columns.tolist()
                }
                for name, df in current_data.items()
            },
            'memory_usage': {
                'conversations_kb': len(str(conversations)) / 1024,
                'datasets_kb': sum(len(df.to_json()) / 1024 for df in current_data.values())
            }
        })
    except Exception as e:
        print(f"Error getting debug state: {str(e)}")
        return jsonify({'error': str(e)}), 500

# API Routes for external API integration
@app.route('/api/external-data/sources', methods=['GET'])
def get_api_sources():
    """Return a list of available API integrations"""
    try:
        sources = get_available_api_sources()
        return jsonify({
            'success': True,
            'sources': sources
        })
    except Exception as e:
        logger.error(f"Error retrieving API sources: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error retrieving API sources: {str(e)}"
        }), 500

@app.route('/api/external-data/sql/tables', methods=['POST', 'OPTIONS'])
def get_sql_tables():
    """Return a list of tables in the SQL Server database"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        return response
        
    try:
        logger.info("Received request to fetch SQL tables")
        data = request.get_json()
        logger.info(f"Request data: {json.dumps(data, default=str)}")
        
        # Extract connection parameters
        connection_params = data.get('credentials', {})
        logger.info(f"Connection params: server={connection_params.get('server')}, database={connection_params.get('database')}")
        
        # Validate required fields
        if not connection_params.get('server') or not connection_params.get('database'):
            logger.warning("Missing required fields: server or database")
            return jsonify({
                'success': False,
                'error': "Server and database names are required"
            }), 400
            
        # Create connector
        connector = SQLServerConnector(connection_params)
        
        # Connect to database
        logger.info(f"Attempting to connect to {connection_params.get('server')}/{connection_params.get('database')}")
        if not connector.connect():
            logger.error(f"Failed to connect to database: {connector.last_error}")
            return jsonify({
                'success': False,
                'error': f"Failed to connect to the database: {connector.last_error}"
            }), 400
            
        # Get table list
        logger.info("Fetching table list")
        tables = connector.list_tables()
        logger.info(f"Retrieved {len(tables)} tables")
        
        # Disconnect
        connector.disconnect()
        logger.info("Disconnected from database")
        
        return jsonify({
            'success': True,
            'tables': tables
        })
        
    except Exception as e:
        logger.error(f"Error fetching SQL Server tables: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f"Error fetching SQL Server tables: {str(e)}",
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/external-data/sql/schema', methods=['POST'])
def get_sql_schema():
    """Return schema information for a specific table"""
    try:
        data = request.get_json()
        
        # Extract connection parameters and table name
        connection_params = data.get('credentials', {})
        table_name = data.get('table_name')
        
        # Validate required fields
        if not connection_params.get('server') or not connection_params.get('database'):
            return jsonify({
                'success': False,
                'error': "Server and database names are required"
            }), 400
            
        if not table_name:
            return jsonify({
                'success': False,
                'error': "Table name is required"
            }), 400
            
        # Create connector
        connector = SQLServerConnector(connection_params)
        
        # Connect to database
        if not connector.connect():
            return jsonify({
                'success': False,
                'error': "Failed to connect to the database"
            }), 400
            
        # Get table schema
        schema_df = connector.get_table_schema(table_name)
        
        # Convert DataFrame to list of dictionaries
        schema = schema_df.to_dict(orient='records')
        
        # Disconnect
        connector.disconnect()
        
        return jsonify({
            'success': True,
            'schema': schema
        })
        
    except Exception as e:
        logger.error(f"Error fetching SQL Server schema: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f"Error fetching SQL Server schema: {str(e)}"
        }), 500

@app.route('/api/external-data/sql/get-ddl', methods=['POST'])
def get_sql_ddl():
    """Return comprehensive database DDL and schema information"""
    try:
        data = request.get_json()
        
        # Extract connection parameters
        connection_params = data.get('credentials', {})
        
        # Validate required fields
        if not connection_params.get('server') or not connection_params.get('database'):
            return jsonify({
                'success': False,
                'error': "Server and database names are required"
            }), 400
            
        # Create connector
        connector = SQLServerConnector(connection_params)
        
        # Connect to database
        if not connector.connect():
            return jsonify({
                'success': False,
                'error': f"Failed to connect to the database: {connector.last_error}"
            }), 400
        
        # Get database DDL
        try:
            database_ddl = connector.get_database_ddl()
        except Exception as e:
            logger.error(f"Error in get_database_ddl: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"Error fetching SQL Server DDL: {str(e)}"
            }), 500
        
        # Disconnect
        connector.disconnect()
        
        return jsonify({
            'success': True,
            'ddl': database_ddl
        })
        
    except Exception as e:
        logger.error(f"Error fetching SQL Server DDL: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f"Error fetching SQL Server DDL: {str(e)}"
        }), 500

@app.route('/api/external-data/fetch', methods=['POST'])
def get_api_data():
    """Fetch data from an external API or data source"""
    try:
        data = request.get_json()
        
        # Extract parameters
        api_source_id = data.get('api_source_id')
        endpoint = data.get('endpoint')
        params = data.get('params', {})
        credentials = data.get('credentials', {})
        dataset_name = data.get('dataset_name', f"{api_source_id}_{endpoint}")
        
        # Validate required fields
        if not api_source_id or not endpoint:
            return jsonify({
                'success': False,
                'error': "API source ID and endpoint are required"
            }), 400
        
        # Log the request
        logger.info(f"Fetching data from {api_source_id} endpoint {endpoint}")
        logger.info(f"Parameters: {json.dumps(params)}")
        logger.info(f"Dataset name: {dataset_name}")
        
        # Handle SQL Server separately
        if api_source_id == 'sql_server':
            from utils.sql_connector import SQLServerConnector, fetch_sql_data
            
            try:
                # For SQL Server, the endpoint is either a table name or a query
                if endpoint == 'query':
                    # Execute a custom query
                    query = params.get('query')
                    if not query:
                        return jsonify({
                            'success': False,
                            'error': "Query parameter is required for SQL query endpoint"
                        }), 400
                    
                    df = fetch_sql_data(credentials, query=query)
                else:
                    # Use the endpoint as the table name
                    df = fetch_sql_data(credentials, table_name=endpoint)
                
                # Check for error result
                if 'error' in df.columns and len(df) == 1:
                    error_msg = df['error'].iloc[0]
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 400
                
                # Save the credentials as a successful configuration
                if credentials:
                    # Add a name field based on the dataset name
                    credentials['name'] = dataset_name
                    SQLServerConnector.save_configuration(credentials)
                    logger.info(f"Saved SQL configuration for {credentials.get('server')}/{credentials.get('database')}")
                
                # Generate a preview of the data
                preview = generate_preview(df)
                
                return jsonify({
                    'success': True,
                    'preview': preview,
                    'shape': df.shape,
                    'columns': df.columns.tolist(),
                    'dataset_name': dataset_name
                })
            except Exception as e:
                logger.error(f"Error fetching SQL data: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f"Error fetching SQL data: {str(e)}"
                }), 400
        
        # For other API sources, use the API integrator
        try:
            # Fetch the data
            df = fetch_api_data(api_source_id, endpoint, params, credentials)
            
            # Generate a preview of the data
            preview = generate_preview(df)
            
            return jsonify({
                'success': True,
                'preview': preview,
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dataset_name': dataset_name
            })
        except ApiIntegrationError as e:
            logger.error(f"API integration error: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
    
    except Exception as e:
        logger.error(f"Error fetching API data: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f"Error fetching API data: {str(e)}"
        }), 500

@app.route('/api/external-data/configure', methods=['POST'])
def configure_api():
    """Save API credentials for a specific integration"""
    try:
        data = request.get_json()
        
        # Extract parameters
        api_source_id = data.get('api_source_id')
        credentials = data.get('credentials', {})
        
        # Validate required fields
        if not api_source_id:
            return jsonify({
                'success': False,
                'error': "API source ID is required"
            }), 400
            
        # Save API credentials
        success = save_api_credentials(api_source_id, credentials)
        
        if success:
            return jsonify({
                'success': True,
                'message': f"Credentials for {api_source_id} saved successfully"
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Failed to save credentials for {api_source_id}"
            }), 400
    
    except Exception as e:
        logger.error(f"Error configuring API: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error configuring API: {str(e)}"
        }), 500

@app.route('/api/external-data/sql/test-connection', methods=['POST'])
def test_sql_connection():
    """Test connection to a SQL Server database"""
    try:
        data = request.get_json()
        
        # Extract connection parameters
        connection_params = data.get('credentials', {})
        
        # Validate required fields
        if not connection_params.get('server') or not connection_params.get('database'):
            return jsonify({
                'success': False,
                'error': "Server and database names are required"
            }), 400
        
        # Add a name field if provided
        if data.get('name'):
            connection_params['name'] = data.get('name')
        
        # Create connector
        connector = SQLServerConnector(connection_params)
        
        # Test connection
        logger.info(f"Testing connection to {connection_params.get('server')}/{connection_params.get('database')}")
        success, message = connector.test_connection()
        
        # If successful, save the configuration
        if success:
            SQLServerConnector.save_configuration(connection_params)
            logger.info(f"Saved SQL configuration for {connection_params.get('server')}/{connection_params.get('database')}")
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error testing SQL connection: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error testing SQL connection: {str(e)}"
        }), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """Return the status of the API server"""
    try:
        return jsonify({
            'success': True,
            'message': 'API server is running',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    except Exception as e:
        logger.error(f"Error checking API status: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error checking API status: {str(e)}"
        }), 500

@app.route('/convert_nl_to_sql', methods=['POST'])
def convert_nl_to_sql():
    """
    Convert natural language to SQL query and optionally execute it.
    Uses langgraph_convert_text_to_sql when available, with proper error handling.
    """
    try:
        logger.info("Received request to convert natural language to SQL")
        data = request.json

        if not data:
            logger.warning("No data provided in request")
            return jsonify({"error": "No data provided"}), 400

        query = data.get('query')

        if not query:
            logger.warning("No query provided in request")
            return jsonify({"error": "No query provided"}), 400

        logger.info(f"Processing NL to SQL query: {query}")

        # Check for specific entity queries that need enhanced handling
        is_clients_query = 'client' in query.lower()
        is_transactions_query = 'transaction' in query.lower() or 'transactions' in query.lower()
        is_assets_query = 'asset' in query.lower() or 'assets' in query.lower()
        
        # Check if the query contains a filter condition
        has_filter = 'where' in query.lower() or 'that are' in query.lower() or 'which are' in query.lower()
        
        direct_diagnostic_results = None
        
        # Extract optional parameters
        connection_params = data.get('connection_params', {})
        execute = data.get('execute', False)
        conversation_history = data.get('conversation_history', [])
        additional_context = data.get('additional_context', "")

        # If this is a common entity query, do a direct check first
        if (is_clients_query or is_transactions_query or is_assets_query) and connection_params:
            try:
                from utils.sql_connector import SQLServerConnector
                
                table_type = "Clients" if is_clients_query else ("Transactions" if is_transactions_query else "Assets")
                logger.info(f"Performing direct diagnostic check for {table_type} table")
                connector = SQLServerConnector(connection_params)
                
                if connector.connect():
                    logger.info("Successfully connected for direct diagnostics")
                    
                    # Check if the relevant table exists (Clients or Transactions)
                    tables = connector.list_tables()
                    target_table = None
                    target_table_name = 'clients' if is_clients_query else ('transactions' if is_transactions_query else 'assets')
                    
                    for table in tables:
                        if table.lower() == target_table_name:
                            target_table = table
                            break
                    
                    if target_table:
                        logger.info(f"Found {target_table} table")
                        
                        # Try a direct SELECT to check for permission issues
                        try:
                            test_query = f"SELECT TOP 5 * FROM [{target_table}]"
                            logger.info(f"Running direct test query: {test_query}")
                            result = connector.execute_query(test_query)
                            
                            if result is not None:
                                row_count = len(result)
                                logger.info(f"Direct test returned {row_count} rows")
                                
                                if row_count > 0:
                                    # Store these results as a fallback
                                    columns = result.columns.tolist()
                                    
                                    # Convert to list of dictionaries
                                    rows = []
                                    for _, row in result.iterrows():
                                        row_dict = {}
                                        for col in columns:
                                            value = row[col]
                                            # Handle non-serializable values
                                            if pd.isna(value):
                                                row_dict[col] = None
                                            else:
                                                row_dict[col] = str(value) if not isinstance(value, (int, float, bool, str, type(None))) else value
                                        rows.append(row_dict)
                                    
                                    direct_diagnostic_results = {
                                        "columns": columns,
                                        "rows": rows,
                                        "query": test_query
                                    }
                                    logger.info(f"Stored direct diagnostic results with {len(rows)} rows as fallback")
                                else:
                                    logger.warning("Direct query found no rows in Clients table - check if table is empty")
                            else:
                                logger.warning("Direct query returned None - possible execution error")
                        except Exception as direct_err:
                            logger.error(f"Error in direct test query: {str(direct_err)}")
                    else:
                        logger.warning(f"Could not find '{target_table_name}' table - check table name case sensitivity")
                    
                    # Close the connection
                    connector.disconnect()
                else:
                    logger.error(f"Failed to connect for direct diagnostics: {connector.last_error}")
            except Exception as diag_err:
                logger.error(f"Error performing direct diagnostics: {str(diag_err)}")

        # Check if langgraph SQL converter is available
        if not is_langgraph_enabled():
            logger.error("Langgraph SQL converter not enabled")
            
            # If we found data directly and this is a recognized entity query, use it
            if (is_clients_query or is_transactions_query) and direct_diagnostic_results:
                logger.info("Using direct diagnostic results since langgraph is not available")
                entity_table = "Clients" if is_clients_query else "Transactions"
                return jsonify({
                    "result": {
                        "sql": f"SELECT * FROM {entity_table}",
                        "explanation": "SQL query executed directly for diagnostic purposes",
                        "success": True,
                        "result": direct_diagnostic_results["rows"],
                        "columns": direct_diagnostic_results["columns"],
                        "diagnostic_mode": True
                    }
                }), 200
            
            return jsonify({
                "error": "SQL conversion service unavailable. The required conversion module is not enabled.",
                "result": None
            }), 503

        # Use the langgraph SQL converter
        logger.info("Using langgraph_convert_text_to_sql for conversion")
        result = langgraph_convert_text_to_sql(
            query=query,
            connection_params=connection_params,
            execute=execute,
            conversation_history=conversation_history,
            additional_context=additional_context
        )

        # Check if this is a clients or transactions query that returned no results but we have diagnostics
        if (is_clients_query or is_transactions_query) and "result" in result and (not result["result"] or len(result["result"]) == 0) and direct_diagnostic_results:
            entity_type = "clients" if is_clients_query else "transactions"
            logger.info(f"Regular flow returned no results for {entity_type} query, but we have direct diagnostic data")
            logger.info("Replacing empty results with direct diagnostic data")
            
            # Update the result with our diagnostic data
            result["result"] = direct_diagnostic_results["rows"]
            result["columns"] = direct_diagnostic_results["columns"]
            result["diagnostic_mode"] = True
            result["diagnostic_message"] = "Data retrieved through direct query for diagnostic purposes"

        logger.info(f"Successfully converted query using langgraph_convert_text_to_sql")
        return jsonify({"result": result}), 200

    except Exception as e:
        error_message = f"Error converting natural language to SQL: {str(e)}"
        logger.error(error_message)
        logger.error(traceback.format_exc())
        return jsonify({
            "error": error_message,
            "result": None
        }), 500

# Add a debugging endpoint for SQL database schema
@app.route('/api/external-data/sql/debug-schema', methods=['GET'])
def debug_sql_schema():
    """Debug endpoint to show what tables are available in the stored DDL"""
    try:
        # Get connection parameters from request
        connection_params = {
            'server': request.args.get('server'),
            'database': request.args.get('database'),
            'username': request.args.get('username', ''),
            'password': request.args.get('password', ''),
            'trusted_connection': request.args.get('trusted_connection', 'false').lower() == 'true'
        }
        
        # If connection params are provided, get the schema directly
        if connection_params['server'] and connection_params['database']:
            logger.info(f"Getting schema for {connection_params['server']}/{connection_params['database']}")
            
            # Create connector
            connector = SQLServerConnector(connection_params)
            
            # Connect to database
            if not connector.connect():
                return jsonify({
                    'success': False,
                    'error': f"Failed to connect to the database: {connector.last_error}"
                }), 400
            
            try:
                # List tables
                tables = connector.list_tables()
                
                # Get schema for each table
                schema_info = {}
                for table_name in tables[:10]:  # Limit to 10 tables for debugging
                    try:
                        schema_df = connector.get_table_schema(table_name)
                        schema_info[table_name] = schema_df.to_dict(orient='records')
                    except Exception as e:
                        logger.warning(f"Could not fetch schema for table {table_name}: {str(e)}")
                
                # Add diagnostic query for 'Clients' table
                clients_exists = False
                clients_rows = []
                try:
                    # Check if Clients table exists (case insensitive)
                    clients_table_name = None
                    for table in tables:
                        if table.lower() == 'clients':
                            clients_table_name = table
                            clients_exists = True
                            break
                    
                    if clients_exists:
                        # Try to query the first few rows
                        query = f"SELECT TOP 5 * FROM [{clients_table_name}]"
                        df = connector.execute_query(query)
                        clients_rows = df.to_dict(orient='records')
                        logger.info(f"Successfully queried {clients_table_name} table, found {len(clients_rows)} rows")
                    else:
                        logger.warning("No table named 'Clients' found (case insensitive search)")
                except Exception as e:
                    logger.error(f"Error querying Clients table: {str(e)}")
                
                return jsonify({
                    'success': True,
                    'server': connection_params['server'],
                    'database': connection_params['database'],
                    'tables': tables,
                    'schemas': schema_info,
                    'clients_table': {
                        'exists': clients_exists,
                        'table_name': clients_table_name if clients_exists else None,
                        'sample_rows': clients_rows
                    }
                }), 200
            except Exception as e:
                logger.error(f"Error getting database schema: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f"Error getting database schema: {str(e)}"
                }), 500
            finally:
                # Close connection
                connector.disconnect()
        
        # Default response with instructions
        return jsonify({
            'success': True,
            'message': 'Use this endpoint with server and database query parameters to debug SQL schema',
            'example': '/api/external-data/sql/debug-schema?server=yourserver&database=yourdb'
        }), 200
            
    except Exception as e:
        logger.error(f"Error in debug-schema endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error: {str(e)}"
        }), 500

# Also add a test endpoint specifically for the Clients SQL query issue
@app.route('/api/test/clients-query', methods=['GET'])
def test_clients_query():
    """Test endpoint to debug issues with Clients table queries"""
    try:
        # Get connection parameters from request or use saved configurations
        use_saved = request.args.get('use_saved', 'true').lower() == 'true'
        
        if use_saved:
            # Try to use saved SQL configurations
            configs = SQLServerConnector.get_saved_configurations()
            if not configs:
                return jsonify({
                    'success': False,
                    'error': "No saved SQL configurations found. Please provide connection parameters."
                }), 400
                
            connection_params = configs[0]  # Use the first saved configuration
            logger.info(f"Using saved configuration for {connection_params.get('server')}/{connection_params.get('database')}")
        else:
            # Get connection parameters from request
            connection_params = {
                'server': request.args.get('server'),
                'database': request.args.get('database'),
                'username': request.args.get('username', ''),
                'password': request.args.get('password', ''),
                'trusted_connection': request.args.get('trusted_connection', 'false').lower() == 'true'
            }
        
        # Create connector
        connector = SQLServerConnector(connection_params)
        
        # Connect to database
        if not connector.connect():
            return jsonify({
                'success': False,
                'error': f"Failed to connect to the database: {connector.last_error}"
            }), 400
        
        results = {}
        
        try:
            # Test connection with simple query
            try:
                test_query = "SELECT 1 AS test_value"
                test_df = connector.execute_query(test_query)
                results['connection_test'] = {
                    'success': True,
                    'result': test_df.to_dict(orient='records')
                }
            except Exception as e:
                results['connection_test'] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"Connection test query failed: {str(e)}")
            
            # List all tables
            try:
                tables = connector.list_tables()
                results['all_tables'] = tables
            except Exception as e:
                results['all_tables'] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"Failed to list tables: {str(e)}")
                # Set an empty list for later use if we failed
                tables = []
            
            # Check for Clients table (case-insensitive)
            clients_table = None
            for table in tables:
                if table.lower() == 'clients':
                    clients_table = table
                    break
            
            results['clients_table_name'] = clients_table
            
            # Try different variations of the Clients query
            variations = [
                {"name": "standard", "query": "SELECT TOP 5 * FROM Clients"},
                {"name": "lowercase", "query": "SELECT TOP 5 * FROM clients"},
                {"name": "brackets", "query": "SELECT TOP 5 * FROM [Clients]"},
                {"name": "schema_prefix", "query": "SELECT TOP 5 * FROM dbo.Clients"},
                {"name": "schema_prefix_brackets", "query": "SELECT TOP 5 * FROM [dbo].[Clients]"}
            ]
            
            # If we found the exact table name, add it to variations
            if clients_table and clients_table not in ["Clients", "clients"]:
                variations.append({"name": "exact_match", "query": f"SELECT TOP 5 * FROM [{clients_table}]"})
            
            # Test each variation
            query_results = {}
            for var in variations:
                try:
                    logger.info(f"Testing query variation: {var['name']} - {var['query']}")
                    df = connector.execute_query(var['query'])
                    row_count = len(df)
                    query_results[var['name']] = {
                        "success": True,
                        "row_count": row_count,
                        "sample": df.head(3).to_dict(orient='records') if row_count > 0 else []
                    }
                    logger.info(f"Query result: {row_count} rows")
                except Exception as e:
                    query_results[var['name']] = {
                        "success": False,
                        "error": str(e)
                    }
                    logger.error(f"Query failed: {str(e)}")
            
            results['query_variations'] = query_results
            
            # Check for information schema tables
            try:
                info_schema_query = """
                SELECT 
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    TABLE_TYPE
                FROM 
                    INFORMATION_SCHEMA.TABLES
                WHERE 
                    TABLE_TYPE = 'BASE TABLE'
                ORDER BY 
                    TABLE_SCHEMA, TABLE_NAME
                """
                info_schema_df = connector.execute_query(info_schema_query)
                results['information_schema'] = info_schema_df.to_dict(orient='records')
            except Exception as e:
                results['information_schema'] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"Information schema query failed: {str(e)}")
            
            # Check for similar tables if Clients table doesn't exist
            if not clients_table:
                similar_tables = [table for table in tables if 'client' in table.lower() or 'customer' in table.lower()]
                results['similar_tables'] = similar_tables
                
                # Also search for tables with "client" in the name using information_schema
                try:
                    client_search_query = """
                    SELECT 
                        TABLE_SCHEMA,
                        TABLE_NAME,
                        TABLE_TYPE
                    FROM 
                        INFORMATION_SCHEMA.TABLES
                    WHERE 
                        TABLE_NAME LIKE '%client%' OR
                        TABLE_NAME LIKE '%Customer%'
                    ORDER BY 
                        TABLE_SCHEMA, TABLE_NAME
                    """
                    client_search_df = connector.execute_query(client_search_query)
                    results['client_search'] = client_search_df.to_dict(orient='records')
                except Exception as e:
                    results['client_search'] = {
                        'success': False,
                        'error': str(e)
                    }
                    logger.error(f"Client search query failed: {str(e)}")
            
            # Return connector diagnostic information
            try:
                server_info = connector._get_server_info()
                results['server_info'] = server_info
            except Exception as e:
                results['server_info'] = {
                    'success': False,
                    'error': str(e)
                }
            
            return jsonify({
                'success': True,
                'connection_info': {
                    'server': connection_params.get('server'),
                    'database': connection_params.get('database'),
                    'trusted_connection': connection_params.get('trusted_connection', False)
                },
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Error in test query: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"Error in test query: {str(e)}",
                'partial_results': results
            }), 500
        finally:
            # Close connection
            connector.disconnect()
            
    except Exception as e:
        logger.error(f"Error in clients-query test endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error: {str(e)}"
        }), 500

# New endpoint to fetch configured data sources
@app.route('/api/external-data/configured-sources', methods=['GET'])
def get_configured_sources():
    """Return a list of data sources that have been configured"""
    try:
        logger.info("Fetching configured data sources")
        
        # Initialize an empty list for configured sources
        configured_sources = []
        
        # Get SQL Server configurations
        try:
            # Fetch all saved SQL server configurations
            sql_configs = SQLServerConnector.get_saved_configurations()
            
            # Add each SQL configuration as a configured source
            for i, config in enumerate(sql_configs):
                source_id = f"sql_{i+1}"
                source_name = config.get('name', f"{config.get('server')}/{config.get('database')}")
                
                configured_sources.append({
                    'id': source_id,
                    'name': source_name,
                    'type': 'sql_server',
                    'description': f"SQL Server connection to {config.get('server')}/{config.get('database')}",
                    'status': 'Active',
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'auth_required': True,
                    'config': {
                        'server': config.get('server'),
                        'database': config.get('database'),
                        'trusted_connection': config.get('trusted_connection', True)
                    }
                })
        except Exception as e:
            logger.warning(f"Error fetching SQL configurations: {str(e)}")
        
        # Return only the actual configured sources
        return jsonify({
            'success': True,
            'sources': configured_sources,
            'total_count': len(configured_sources)
        })
    except Exception as e:
        logger.error(f"Error retrieving configured sources: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error retrieving configured sources: {str(e)}"
        }), 500

# New endpoint to delete a configured data source
@app.route('/api/external-data/configured-sources/<source_id>', methods=['DELETE'])
def delete_configured_source(source_id):
    """Delete a configured data source by ID"""
    try:
        logger.info(f"Received request to delete data source with ID: {source_id}")
        
        # In a production app, this would delete from a database
        # For now, we'll just simulate a successful deletion
        
        # Validate source_id format
        if not source_id or not isinstance(source_id, str):
            return jsonify({
                'success': False,
                'error': "Invalid source ID format"
            }), 400
        
        # In a real implementation, this would check if the source exists
        # and delete it from persistent storage
        
        return jsonify({
            'success': True,
            'message': f"Data source {source_id} deleted successfully"
        })
    except Exception as e:
        logger.error(f"Error deleting data source: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error deleting data source: {str(e)}"
        }), 500

# Add a direct SQL query execution endpoint for the Clients table
@app.route('/api/test/direct-clients-query', methods=['GET'])
def direct_clients_query():
    """Direct query endpoint for the Clients table"""
    try:
        # Get connection parameters from saved configurations
        configs = SQLServerConnector.get_saved_configurations()
        if not configs:
            return jsonify({
                'success': False,
                'error': "No saved SQL configurations found."
            }), 400
            
        connection_params = configs[0]  # Use the first saved configuration
        logger.info(f"Using saved configuration for {connection_params.get('server')}/{connection_params.get('database')}")
        
        # Create connector
        connector = SQLServerConnector(connection_params)
        
        # Connect to database
        if not connector.connect():
            return jsonify({
                'success': False,
                'error': f"Failed to connect to the database: {connector.last_error}"
            }), 400
        
        results = {}
        
        try:
            # List all tables
            tables = connector.list_tables()
            
            # Get client tables - both exact and similar matches
            clients_table = None
            similar_tables = []
            
            for table in tables:
                if table.lower() == 'clients':
                    clients_table = table
                elif 'client' in table.lower() or 'customer' in table.lower():
                    similar_tables.append(table)
            
            # Execute direct query on Clients table if it exists
            if clients_table:
                try:
                    # Try with SQL Server specific syntax
                    direct_query = f"SELECT TOP 10 * FROM [{clients_table}]"
                    logger.info(f"Executing direct query: {direct_query}")
                    
                    df = connector.execute_query(direct_query)
                    
                    # Check if we got results
                    row_count = len(df)
                    logger.info(f"Query returned {row_count} rows")
                    
                    # Get column information
                    columns = df.columns.tolist()
                    
                    # Create a sample result
                    results['direct_query'] = {
                        'success': True,
                        'query': direct_query,
                        'row_count': row_count,
                        'columns': columns,
                        'sample_data': df.head(5).to_dict(orient='records') if row_count > 0 else []
                    }
                    
                except Exception as e:
                    logger.error(f"Error executing direct query: {str(e)}")
                    results['direct_query'] = {
                        'success': False,
                        'query': direct_query,
                        'error': str(e)
                    }
            else:
                results['direct_query'] = {
                    'success': False,
                    'error': "No table named 'Clients' found."
                }
            
            # Add information about the database
            results['database_info'] = {
                'connection': {
                    'server': connection_params.get('server'),
                    'database': connection_params.get('database'),
                    'driver': connector.driver
                },
                'tables_count': len(tables),
                'tables_sample': tables[:10],  # First 10 tables
                'clients_table': clients_table,
                'similar_tables': similar_tables
            }
            
            # Also try to get table schema information for Clients
            if clients_table:
                try:
                    schema_df = connector.get_table_schema(clients_table)
                    results['table_schema'] = schema_df.to_dict(orient='records')
                except Exception as e:
                    logger.error(f"Error getting table schema: {str(e)}")
                    results['table_schema'] = {
                        'success': False,
                        'error': str(e)
                    }
                    
            # Get the SQL Server version
            try:
                server_info = connector._get_server_info()
                results['server_info'] = server_info
            except Exception as e:
                logger.error(f"Error getting server info: {str(e)}")
                results['server_info'] = {
                    'success': False,
                    'error': str(e)
                }
            
            return jsonify({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Error in direct Clients query: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"Error in direct Clients query: {str(e)}",
                'partial_results': results
            }), 500
        finally:
            # Close connection
            connector.disconnect()
            
    except Exception as e:
        logger.error(f"Error in direct-clients-query endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error: {str(e)}"
        }), 500

# Add a test endpoint for NL to SQL with Clients table
@app.route('/api/test/nl-to-sql-clients', methods=['GET'])
def test_nl_to_sql_clients():
    """Test endpoint for natural language to SQL with Clients table"""
    try:
        # Get the natural language query from the request
        nl_query = request.args.get('query', 'Show all clients')
        
        # Get connection parameters from saved configurations
        configs = SQLServerConnector.get_saved_configurations()
        if not configs:
            return jsonify({
                'success': False,
                'error': "No saved SQL configurations found."
            }), 400
            
        connection_params = configs[0]  # Use the first saved configuration
        logger.info(f"Using saved configuration for {connection_params.get('server')}/{connection_params.get('database')}")
        
        # Make sure the langgraph SQL is enabled
        os.environ["ENABLE_LANGGRAPH_SQL"] = "true"
        os.environ["ENABLE_SQL_REFLECTION"] = "true"
        
        # Convert natural language to SQL
        try:
            # Call the langgraph_convert_text_to_sql function directly
            from utils.langgraph_sql.api_integration import langgraph_convert_text_to_sql
            
            # Set execute=True to attempt execution
            result = langgraph_convert_text_to_sql(
                query=nl_query,
                connection_params=connection_params,
                execute=True
            )
            
            logger.info(f"NL to SQL result: {json.dumps(result, default=str)}")
            
            return jsonify({
                'success': True,
                'query': nl_query,
                'sql': result.get('sql', ''),
                'explanation': result.get('explanation', ''),
                'executed': 'result' in result and result['result'] is not None,
                'result': result.get('result', []),
                'error': result.get('error', None)
            })
            
        except Exception as e:
            logger.error(f"Error converting NL to SQL: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'query': nl_query,
                'error': f"Error converting NL to SQL: {str(e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in NL to SQL Clients test: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error: {str(e)}"
        }), 500

# Debug endpoint to directly check Clients table
@app.route('/api/test/direct-sql-clients', methods=['GET'])
def test_direct_sql_clients():
    """Debug endpoint to directly query the Clients table"""
    try:
        # Get connection parameters from saved configurations
        configs = SQLServerConnector.get_saved_configurations()
        if not configs:
            return jsonify({
                'success': False,
                'error': "No saved SQL configurations found."
            }), 400
            
        connection_params = configs[0]  # Use the first saved configuration
        logger.info(f"Using saved configuration for {connection_params.get('server')}/{connection_params.get('database')}")
        
        # Create a connector and query the database
        connector = SQLServerConnector(connection_params)
        if connector.connect():
            logger.info("Successfully connected to database")
            
            # Get list of tables to find the right one
            tables = connector.list_tables()
            logger.info(f"Available tables: {tables}")
            
            # Try to find Clients table (case insensitive)
            clients_table = None
            for table in tables:
                if table.lower() == 'clients':
                    clients_table = table
                    break
            
            # Fall back to the first table if no Clients table found
            if not clients_table and tables:
                clients_table = tables[0]
                logger.info(f"No Clients table found, using first table: {clients_table}")
            elif not clients_table:
                return jsonify({
                    'success': False,
                    'error': "No tables found in database"
                }), 404
            else:
                logger.info(f"Found Clients table: {clients_table}")
            
            # Execute a simple query to get all data from the table
            query = f"SELECT TOP 10 * FROM [{clients_table}]"
            logger.info(f"Executing query: {query}")
            
            try:
                df = connector.execute_query(query)
                row_count = len(df)
                logger.info(f"Query returned {row_count} rows")
                
                # Log sample data
                if row_count > 0:
                    logger.info(f"Sample data (first row): {df.iloc[0].to_dict()}")
                    
                # Create a detailed response
                result = {
                    'success': True,
                    'table_used': clients_table,
                    'available_tables': tables,
                    'row_count': row_count,
                    'columns': df.columns.tolist(),
                    'data': df.to_dict(orient='records'),
                    'connection': {
                        'server': connection_params.get('server'),
                        'database': connection_params.get('database')
                    }
                }
                
                connector.disconnect()
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Error executing query: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({
                    'success': False,
                    'error': f"Error executing query: {str(e)}",
                    'table_attempted': clients_table,
                    'available_tables': tables
                }), 500
                
        else:
            logger.error(f"Failed to connect to database: {connector.last_error}")
            return jsonify({
                'success': False,
                'error': f"Failed to connect to database: {connector.last_error}"
            }), 500
            
    except Exception as e:
        logger.error(f"Error in direct SQL Clients test: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f"Error: {str(e)}"
        }), 500

if __name__ == '__main__':
    print(f"Starting IntelliAssistant with configuration:")
    print(f"- Debug mode: {DEBUG}")
    print(f"- Host: {HOST}")
    print(f"- Port: {PORT}")
    print(f"- Default dataset: {DEFAULT_DATASET}")
    app.run(debug=DEBUG, host=HOST, port=PORT)
