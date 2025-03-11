import os
import json
import uuid
import datetime
from typing import List, Dict, Optional, Any

# Constants
CONVERSATION_DIR = "data/conversations"

# Create conversation directory if it doesn't exist
os.makedirs(CONVERSATION_DIR, exist_ok=True)

def save_conversation(user_id: str, conversation_history: List[Dict[str, Any]]) -> str:
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
        "id": conversation_id,
        "user_id": user_id,
        "created_at": datetime.datetime.now().isoformat(),
        "updated_at": datetime.datetime.now().isoformat(),
        "messages": conversation_history
    }
    
    # Save to file
    file_path = os.path.join(CONVERSATION_DIR, f"{conversation_id}.json")
    with open(file_path, "w") as f:
        json.dump(conversation_data, f)
    
    return conversation_id

def load_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a conversation by ID.
    
    Args:
        conversation_id (str): Conversation identifier
        
    Returns:
        dict: Conversation data or None if not found
    """
    file_path = os.path.join(CONVERSATION_DIR, f"{conversation_id}.json")
    
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading conversation {conversation_id}: {str(e)}")
        return None

def load_user_conversations(user_id: str) -> List[Dict[str, Any]]:
    """
    Load all conversations for a user.
    
    Args:
        user_id (str): User identifier
        
    Returns:
        list: List of conversation data
    """
    conversations = []
    
    # Check if directory exists
    if not os.path.exists(CONVERSATION_DIR):
        return conversations
    
    # List all conversation files
    for filename in os.listdir(CONVERSATION_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(CONVERSATION_DIR, filename)
            try:
                with open(file_path, "r") as f:
                    conversation_data = json.load(f)
                    if conversation_data.get("user_id") == user_id:
                        conversations.append(conversation_data)
            except Exception as e:
                print(f"Error loading conversation {filename}: {str(e)}")
    
    # Sort by updated_at (newest first)
    conversations.sort(
        key=lambda x: x.get("updated_at", x.get("created_at", "")), 
        reverse=True
    )
    
    return conversations

def delete_conversation(conversation_id: str) -> bool:
    """
    Delete a conversation.
    
    Args:
        conversation_id (str): Conversation identifier
        
    Returns:
        bool: True if deleted successfully
    """
    file_path = os.path.join(CONVERSATION_DIR, f"{conversation_id}.json")
    
    if not os.path.exists(file_path):
        return False
    
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        print(f"Error deleting conversation {conversation_id}: {str(e)}")
        return False

def load_conversation_history(conversation_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
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
    
    conversation_data = load_conversation(conversation_id)
    if not conversation_data or "messages" not in conversation_data:
        return []
    
    # Get the messages, limited to the specified number
    messages = conversation_data["messages"]
    if limit > 0:
        messages = messages[-limit:]
    
    return messages

def add_message_to_conversation(conversation_id: str, message: Dict[str, Any]) -> bool:
    """
    Add a message to an existing conversation.
    
    Args:
        conversation_id (str): Conversation identifier
        message (dict): Message to add
        
    Returns:
        bool: True if message was added successfully
    """
    # Load existing conversation
    conversation_data = load_conversation(conversation_id)
    if not conversation_data:
        return False
    
    # Add message to history
    if "messages" not in conversation_data:
        conversation_data["messages"] = []
    
    conversation_data["messages"].append(message)
    
    # Update timestamp
    conversation_data["updated_at"] = datetime.datetime.now().isoformat()
    
    # Save back to file
    file_path = os.path.join(CONVERSATION_DIR, f"{conversation_id}.json")
    try:
        with open(file_path, "w") as f:
            json.dump(conversation_data, f)
        return True
    except Exception as e:
        print(f"Error updating conversation {conversation_id}: {str(e)}")
        return False

def share_conversation(conversation_id: str, recipient_id: str) -> Optional[str]:
    """
    Share a conversation with another user.
    
    Args:
        conversation_id (str): Conversation identifier
        recipient_id (str): Recipient user identifier
        
    Returns:
        str: Shared conversation ID or None if failed
    """
    # Load the original conversation
    conversation_data = load_conversation(conversation_id)
    if not conversation_data:
        return None
    
    # Create a copy for the recipient
    shared_conversation = conversation_data.copy()
    
    # Generate a new ID for the shared conversation
    new_conversation_id = str(uuid.uuid4())
    
    # Update metadata
    shared_conversation["id"] = new_conversation_id
    shared_conversation["user_id"] = recipient_id
    shared_conversation["shared_from"] = {
        "user_id": conversation_data.get("user_id"),
        "conversation_id": conversation_id,
        "shared_at": datetime.datetime.now().isoformat()
    }
    shared_conversation["created_at"] = datetime.datetime.now().isoformat()
    shared_conversation["updated_at"] = datetime.datetime.now().isoformat()
    
    # Save to file
    file_path = os.path.join(CONVERSATION_DIR, f"{new_conversation_id}.json")
    try:
        with open(file_path, "w") as f:
            json.dump(shared_conversation, f)
        return new_conversation_id
    except Exception as e:
        print(f"Error sharing conversation: {str(e)}")
        return None