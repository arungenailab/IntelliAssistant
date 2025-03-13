import os
import json
import uuid
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import traceback

# Import utility modules
from utils.gemini_helper import analyze_data, suggest_query_improvements
from utils.file_utils import process_uploaded_file, generate_preview, get_dataset_info
from utils.visualization_helper import create_visualization

# Initialize Flask app
app = Flask(__name__, static_folder='frontend/build')

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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
        user_id = data.get('userId', 'anonymous')
        dataset_name = data.get('datasetName')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
            
        print(f"\nProcessing chat message: {user_message}")
        print(f"Available datasets: {list(current_data.keys())}")
        
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            conversations[conversation_id] = {
                'id': conversation_id,
                'title': user_message[:50] + ('...' if len(user_message) > 50 else ''),
                'messages': [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        
        # Add user message to conversation
        user_message_obj = {
            'id': str(uuid.uuid4()),
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        }
        
        if conversation_id in conversations:
            conversations[conversation_id]['messages'].append(user_message_obj)
            conversations[conversation_id]['updated_at'] = datetime.now().isoformat()
        
        # Get conversation history
        conversation_history = [
            {'role': msg['role'], 'content': msg['content']} 
            for msg in conversations[conversation_id]['messages'][-5:] if conversation_id in conversations
        ]
        
        # Get the active dataset
        df = None
        if dataset_name and dataset_name in current_data:
            df = current_data[dataset_name]
        else:
            # Use the first available dataset
            if current_data:
                dataset_name = next(iter(current_data.keys()))
                df = current_data[dataset_name]
        
        if df is None or df.empty:
            return jsonify({'error': 'No dataset available'}), 400
        
        # Analyze data and get response
        analysis_result = analyze_data(
            user_query=user_message,
            data=df,
            conversation_history=conversation_history
        )
        
        response_text = analysis_result['text']
        visualization = None
        
        # Create visualization if suggested
        if analysis_result['visualization']:
            try:
                viz_result = create_visualization(
                    df,
                    analysis_result['visualization']['type'],
                    user_message,
                    analysis_result['visualization']
                )
                
                if viz_result:
                    visualization = {
                        'type': viz_result['type'],
                        'title': viz_result['title'],
                        'data': viz_result['data']
                    }
            except Exception as e:
                print(f"Error creating visualization: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
        
        # Create assistant message
        assistant_message = {
            'id': str(uuid.uuid4()),
            'role': 'assistant',
            'content': response_text,
            'timestamp': datetime.now().isoformat(),
            'visualization': visualization
        }
        
        if conversation_id in conversations:
            conversations[conversation_id]['messages'].append(assistant_message)
        
        return jsonify({
            'text': response_text,
            'conversationId': conversation_id,
            'messageId': assistant_message['id'],
            'timestamp': assistant_message['timestamp'],
            'visualization': visualization
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
            
            # Store the dataset
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
