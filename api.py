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

# Initialize Flask app
app = Flask(__name__, static_folder='frontend/build')

# Set custom JSON encoder
app.json_encoder = CustomJSONEncoder

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Allow all origins
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "X-Total-Count"],
        "max_age": 600
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
            
        # Import SQL connector
        from utils.sql_connector import SQLServerConnector
        
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
            
        # Import SQL connector
        from utils.sql_connector import SQLServerConnector
        
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

@app.route('/api/external-data/fetch', methods=['POST'])
def get_api_data():
    """Fetch data from an external API based on provided parameters"""
    try:
        data = request.get_json()
        
        # Extract parameters
        api_source_id = data.get('api_source_id')
        endpoint = data.get('endpoint')
        params = data.get('params', {})
        credentials = data.get('credentials', {})
        dataset_name = data.get('dataset_name')
        
        # Validate required fields
        if not api_source_id or not endpoint:
            return jsonify({
                'success': False,
                'error': "API source ID and endpoint are required"
            }), 400
            
        # Fetch data from the API
        df = fetch_api_data(api_source_id, endpoint, params, credentials)
        
        # Generate a preview of the data
        preview = generate_preview(df)
        
        # Save the data to the current_data dictionary if dataset_name is provided
        if dataset_name:
            current_data[dataset_name] = df
            
        return jsonify({
            'success': True,
            'preview': preview,
            'shape': df.shape,
            'columns': list(df.columns)
        })
    
    except ApiIntegrationError as e:
        logger.error(f"API integration error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error fetching API data: {str(e)}")
        traceback.print_exc()
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
    """Test a connection to a SQL Server database"""
    try:
        data = request.get_json()
        
        # Extract connection parameters
        connection_params = data
        
        # Validate required fields
        if not connection_params.get('server') or not connection_params.get('database'):
            return jsonify({
                'success': False,
                'error': "Server and database names are required"
            }), 400
            
        # Log connection attempt (without sensitive info)
        logger.info(f"Testing SQL connection to server: {connection_params.get('server')}, database: {connection_params.get('database')}")
        
        # Import SQL connector
        from utils.sql_connector import SQLServerConnector
        
        # Create connector
        connector = SQLServerConnector(connection_params)
        
        # Get system diagnostics
        system_info = connector._check_system_requirements()
        
        # Test connection
        success, message = connector.test_connection()
        
        # Get available drivers
        available_drivers = connector._get_available_drivers()
        
        # Prepare response with detailed diagnostics
        response = {
            'success': success,
            'message': message,
            'available_drivers': available_drivers,
            'system_info': system_info
        }
        
        # If connection failed, add troubleshooting info
        if not success:
            # Check if SQL Server is installed
            sql_server_installed = system_info.get('sql_server_installed', False)
            
            # Add specific troubleshooting advice
            if not available_drivers:
                response['troubleshooting'] = [
                    "No SQL Server ODBC drivers found on your system.",
                    "Please install the Microsoft ODBC Driver for SQL Server:",
                    "https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server"
                ]
            elif not sql_server_installed and system_info.get('os') == 'Windows':
                response['troubleshooting'] = [
                    "SQL Server does not appear to be installed on this machine.",
                    "If you're trying to connect to a remote SQL Server, make sure the server name is correct.",
                    "If you're trying to connect to a local SQL Server, please install SQL Server or SQL Server Express."
                ]
            
            # Add the error details
            if connector.last_error:
                response['error_details'] = connector.last_error
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error testing SQL Server connection: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f"Error testing SQL Server connection: {str(e)}",
            'traceback': traceback.format_exc()
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

if __name__ == '__main__':
    print(f"Starting IntelliAssistant with configuration:")
    print(f"- Debug mode: {DEBUG}")
    print(f"- Host: {HOST}")
    print(f"- Port: {PORT}")
    print(f"- Default dataset: {DEFAULT_DATASET}")
    app.run(debug=DEBUG, host=HOST, port=PORT)
