import os
import json
import uuid
from datetime import datetime

# Directory for storing conversations
CONVERSATIONS_DIR = os.path.join(os.getcwd(), "data", "conversations")

# Create the directory if it doesn't exist
os.makedirs(CONVERSATIONS_DIR, exist_ok=True)

def save_conversation(user_id, conversation_history):
    """
    Save a conversation history for a user.
    
    Args:
        user_id (str): User identifier
        conversation_history (list): List of conversation messages
        
    Returns:
        str: Conversation ID
    """
    # Generate a unique conversation ID
    conversation_id = str(uuid.uuid4())
    
    # Create conversation data structure
    conversation_data = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": conversation_history
    }
    
    # Save to JSON file
    conversation_file = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    
    try:
        with open(conversation_file, 'w') as f:
            json.dump(conversation_data, f, indent=2)
        
        return conversation_id
    except Exception as e:
        print(f"Error saving conversation: {str(e)}")
        return None

def load_conversation(conversation_id):
    """
    Load a conversation by ID.
    
    Args:
        conversation_id (str): Conversation identifier
        
    Returns:
        dict: Conversation data or None if not found
    """
    conversation_file = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    
    try:
        if os.path.exists(conversation_file):
            with open(conversation_file, 'r') as f:
                return json.load(f)
        return None
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
    
    try:
        # Iterate through all conversation files
        for filename in os.listdir(CONVERSATIONS_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(CONVERSATIONS_DIR, filename)
                
                with open(file_path, 'r') as f:
                    conversation_data = json.load(f)
                    
                    # Check if this conversation belongs to the user
                    if conversation_data.get("user_id") == user_id:
                        # Add a summary of the conversation
                        if "messages" in conversation_data and len(conversation_data["messages"]) > 0:
                            first_message = conversation_data["messages"][0]
                            conversation_data["summary"] = first_message.get("content", "")[:100] + "..."
                        else:
                            conversation_data["summary"] = "Empty conversation"
                        
                        user_conversations.append(conversation_data)
        
        # Sort by updated_at timestamp, newest first
        user_conversations.sort(
            key=lambda x: datetime.strptime(x.get("updated_at", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )
        
        return user_conversations
    
    except Exception as e:
        print(f"Error loading user conversations: {str(e)}")
        return []

def delete_conversation(conversation_id):
    """
    Delete a conversation.
    
    Args:
        conversation_id (str): Conversation identifier
        
    Returns:
        bool: True if deleted successfully
    """
    conversation_file = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
    
    try:
        if os.path.exists(conversation_file):
            os.remove(conversation_file)
            return True
        return False
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
    if not conversation_id:
        return []
    
    conversation = load_conversation(conversation_id)
    if not conversation or "messages" not in conversation:
        return []
    
    # Return the most recent messages up to the limit
    messages = conversation["messages"]
    if len(messages) > limit:
        return messages[-limit:]
    return messages

def add_message_to_conversation(conversation_id, message):
    """
    Add a message to an existing conversation.
    
    Args:
        conversation_id (str): Conversation identifier
        message (dict): Message to add
        
    Returns:
        bool: True if message was added successfully
    """
    try:
        conversation = load_conversation(conversation_id)
        if not conversation:
            return False
        
        # Add the new message
        if "messages" not in conversation:
            conversation["messages"] = []
        
        conversation["messages"].append(message)
        
        # Update timestamp
        conversation["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save the updated conversation
        conversation_file = os.path.join(CONVERSATIONS_DIR, f"{conversation_id}.json")
        with open(conversation_file, 'w') as f:
            json.dump(conversation, f, indent=2)
        
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
    try:
        # Load the original conversation
        conversation = load_conversation(conversation_id)
        if not conversation:
            return None
        
        # Create a copy for the recipient
        shared_conversation = conversation.copy()
        
        # Update the metadata
        shared_conversation["conversation_id"] = str(uuid.uuid4())
        shared_conversation["original_id"] = conversation_id
        shared_conversation["user_id"] = recipient_id
        shared_conversation["shared_from"] = conversation["user_id"]
        shared_conversation["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shared_conversation["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shared_conversation["is_shared"] = True
        
        # Save the shared conversation
        shared_id = shared_conversation["conversation_id"]
        shared_file = os.path.join(CONVERSATIONS_DIR, f"{shared_id}.json")
        
        with open(shared_file, 'w') as f:
            json.dump(shared_conversation, f, indent=2)
        
        return shared_id
    
    except Exception as e:
        print(f"Error sharing conversation: {str(e)}")
        return None