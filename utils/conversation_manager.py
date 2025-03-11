import json
import os
import time
from datetime import datetime

# In a production system, this would use a database
# For simplicity, we'll use a dictionary and save to disk
CONVERSATION_STORE = {}
CONVERSATION_FILE = "conversations.json"

def save_conversation(user_id, conversation_history):
    """
    Save a conversation history for a user.
    
    Args:
        user_id (str): User identifier
        conversation_history (list): List of conversation messages
        
    Returns:
        str: Conversation ID
    """
    # Generate a conversation ID
    conversation_id = f"conv_{int(time.time())}_{user_id[-5:]}"
    
    # Prepare conversation data
    conversation_data = {
        "id": conversation_id,
        "user_id": user_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "history": conversation_history
    }
    
    # Add to in-memory store
    CONVERSATION_STORE[conversation_id] = conversation_data
    
    # Save to disk
    try:
        # Load existing conversations if file exists
        existing_conversations = {}
        if os.path.exists(CONVERSATION_FILE):
            with open(CONVERSATION_FILE, 'r') as f:
                existing_conversations = json.load(f)
        
        # Update with new conversation
        existing_conversations[conversation_id] = conversation_data
        
        # Write back to file
        with open(CONVERSATION_FILE, 'w') as f:
            json.dump(existing_conversations, f, indent=2)
    except Exception as e:
        print(f"Error saving conversation: {str(e)}")
    
    return conversation_id

def load_conversation(conversation_id):
    """
    Load a conversation by ID.
    
    Args:
        conversation_id (str): Conversation identifier
        
    Returns:
        dict: Conversation data or None if not found
    """
    # Check in-memory store first
    if conversation_id in CONVERSATION_STORE:
        return CONVERSATION_STORE[conversation_id]
    
    # If not in memory, try to load from disk
    try:
        if os.path.exists(CONVERSATION_FILE):
            with open(CONVERSATION_FILE, 'r') as f:
                conversations = json.load(f)
                if conversation_id in conversations:
                    # Add to in-memory store for faster access
                    CONVERSATION_STORE[conversation_id] = conversations[conversation_id]
                    return conversations[conversation_id]
    except Exception as e:
        print(f"Error loading conversation: {str(e)}")
    
    return None

def load_user_conversations(user_id):
    """
    Load all conversations for a user.
    
    Args:
        user_id (str): User identifier
        
    Returns:
        list: List of conversation data
    """
    user_conversations = []
    
    # Check in-memory store
    for conv_id, conv_data in CONVERSATION_STORE.items():
        if conv_data["user_id"] == user_id:
            user_conversations.append(conv_data)
    
    # Also check disk storage for additional conversations
    try:
        if os.path.exists(CONVERSATION_FILE):
            with open(CONVERSATION_FILE, 'r') as f:
                conversations = json.load(f)
                for conv_id, conv_data in conversations.items():
                    if conv_data["user_id"] == user_id and conv_id not in CONVERSATION_STORE:
                        user_conversations.append(conv_data)
                        # Add to in-memory store
                        CONVERSATION_STORE[conv_id] = conv_data
    except Exception as e:
        print(f"Error loading user conversations: {str(e)}")
    
    # Sort by timestamp (newest first)
    user_conversations.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return user_conversations

def delete_conversation(conversation_id):
    """
    Delete a conversation.
    
    Args:
        conversation_id (str): Conversation identifier
        
    Returns:
        bool: True if deleted successfully
    """
    # Remove from in-memory store
    if conversation_id in CONVERSATION_STORE:
        del CONVERSATION_STORE[conversation_id]
    
    # Remove from disk storage
    try:
        if os.path.exists(CONVERSATION_FILE):
            with open(CONVERSATION_FILE, 'r') as f:
                conversations = json.load(f)
            
            if conversation_id in conversations:
                del conversations[conversation_id]
                
                with open(CONVERSATION_FILE, 'w') as f:
                    json.dump(conversations, f, indent=2)
                
                return True
    except Exception as e:
        print(f"Error deleting conversation: {str(e)}")
    
    return False

def load_conversation_history(conversation_id=None, limit=20):
    """
    Load conversation history for display.
    
    Args:
        conversation_id (str, optional): Conversation ID to load
        limit (int, optional): Maximum number of messages to return
        
    Returns:
        list: Conversation history
    """
    if conversation_id:
        conversation = load_conversation(conversation_id)
        if conversation:
            # Return the most recent messages up to the limit
            history = conversation["history"]
            return history[-limit:] if limit < len(history) else history
    
    # Return empty list if conversation not found
    return []

def add_message_to_conversation(conversation_id, message):
    """
    Add a message to an existing conversation.
    
    Args:
        conversation_id (str): Conversation identifier
        message (dict): Message to add
        
    Returns:
        bool: True if message was added successfully
    """
    conversation = load_conversation(conversation_id)
    if not conversation:
        return False
    
    # Add the message
    conversation["history"].append(message)
    
    # Update in-memory store
    CONVERSATION_STORE[conversation_id] = conversation
    
    # Update disk storage
    try:
        if os.path.exists(CONVERSATION_FILE):
            with open(CONVERSATION_FILE, 'r') as f:
                conversations = json.load(f)
            
            conversations[conversation_id] = conversation
            
            with open(CONVERSATION_FILE, 'w') as f:
                json.dump(conversations, f, indent=2)
        else:
            # If file doesn't exist, create it with this conversation
            with open(CONVERSATION_FILE, 'w') as f:
                json.dump({conversation_id: conversation}, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error adding message to conversation: {str(e)}")
    
    return False

def share_conversation(conversation_id, recipient_id):
    """
    Share a conversation with another user.
    
    Args:
        conversation_id (str): Conversation identifier
        recipient_id (str): Recipient user identifier
        
    Returns:
        str: Shared conversation ID or None if failed
    """
    # Load the source conversation
    conversation = load_conversation(conversation_id)
    if not conversation:
        return None
    
    # Create a copy for the recipient
    shared_conversation_id = f"shared_{int(time.time())}_{recipient_id[-5:]}"
    
    shared_conversation = {
        "id": shared_conversation_id,
        "user_id": recipient_id,
        "shared_from": {
            "user_id": conversation["user_id"],
            "conversation_id": conversation_id,
            "timestamp": conversation["timestamp"]
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "history": conversation["history"]
    }
    
    # Add to in-memory store
    CONVERSATION_STORE[shared_conversation_id] = shared_conversation
    
    # Save to disk
    try:
        # Load existing conversations
        existing_conversations = {}
        if os.path.exists(CONVERSATION_FILE):
            with open(CONVERSATION_FILE, 'r') as f:
                existing_conversations = json.load(f)
        
        # Add the shared conversation
        existing_conversations[shared_conversation_id] = shared_conversation
        
        # Write back to file
        with open(CONVERSATION_FILE, 'w') as f:
            json.dump(existing_conversations, f, indent=2)
        
        return shared_conversation_id
    except Exception as e:
        print(f"Error sharing conversation: {str(e)}")
    
    return None
