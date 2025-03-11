import os
import json
import time
import uuid
import threading
import queue
import datetime
from collections import defaultdict

# Constants
LOG_DIR = "data"
LOG_FILE = "acb_usage_logs.jsonl"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Queue for threaded logging
log_queue = queue.Queue()
stop_logging = threading.Event()
log_thread = None

def initialize_logger():
    """Initialize the background logging thread."""
    global log_thread
    if log_thread is None or not log_thread.is_alive():
        stop_logging.clear()
        log_thread = threading.Thread(target=log_worker, daemon=True)
        log_thread.start()

def log_worker():
    """Worker thread to process the log queue and write to file."""
    while not stop_logging.is_set():
        try:
            # Wait for log entries with a timeout
            log_entry = log_queue.get(timeout=1.0)
            
            # Write to log file
            with open(LOG_PATH, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            
            log_queue.task_done()
        except queue.Empty:
            # Timeout occurred, check if we should stop
            continue
        except Exception as e:
            print(f"Error in log worker: {str(e)}")
            time.sleep(1)  # Avoid tight loop on error

def log_action(user_id, action, details=None):
    """
    Log a user action with details.
    
    Args:
        user_id (str): User identifier
        action (str): Action type
        details (dict, optional): Additional details
    """
    # Create log entry
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "user_id": user_id,
        "action": action,
        "details": details or {}
    }
    
    # Add to queue
    log_queue.put(log_entry)
    
    # Make sure logger is running
    initialize_logger()

def get_user_logs(user_id, limit=100):
    """
    Get logs for a specific user.
    
    Args:
        user_id (str): User identifier
        limit (int, optional): Maximum number of logs to return
        
    Returns:
        list: User logs
    """
    logs = []
    
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get("user_id") == user_id:
                            logs.append(log_entry)
                            if len(logs) >= limit:
                                break
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Error reading logs: {str(e)}")
    
    # Sort by timestamp (newest first)
    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return logs

def get_resource_usage():
    """
    Get resource usage metrics from logs.
    
    Returns:
        dict: Resource usage metrics
    """
    metrics = {
        "total_queries": 0,
        "api_calls": 0,
        "visualizations": 0,
        "total_users": 0,
        "avg_queries_per_user": 0,
        "usage_by_day": defaultdict(int),
        "usage_by_hour": defaultdict(int),
        "popular_query_types": defaultdict(int)
    }
    
    users = set()
    
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Get timestamp and convert to datetime
                        timestamp_str = log_entry.get("timestamp", "")
                        if timestamp_str:
                            dt = datetime.datetime.fromisoformat(timestamp_str)
                            date_str = dt.strftime("%Y-%m-%d")
                            hour = dt.hour
                            
                            # Update usage by day and hour
                            metrics["usage_by_day"][date_str] += 1
                            metrics["usage_by_hour"][hour] += 1
                        
                        # Track unique users
                        user_id = log_entry.get("user_id")
                        if user_id:
                            users.add(user_id)
                        
                        # Count by action type
                        action = log_entry.get("action", "")
                        if action == "query":
                            metrics["total_queries"] += 1
                            
                            # Track query types
                            query_text = log_entry.get("details", {}).get("query", "").lower()
                            for keyword, query_type in [
                                ("show", "display"),
                                ("visualize", "visualization"),
                                ("analyze", "analysis"),
                                ("calculate", "calculation"),
                                ("predict", "prediction"),
                                ("compare", "comparison")
                            ]:
                                if keyword in query_text:
                                    metrics["popular_query_types"][query_type] += 1
                                    break
                        elif action == "api_call":
                            metrics["api_calls"] += 1
                        elif action == "visualization":
                            metrics["visualizations"] += 1
                    
                    except (json.JSONDecodeError, ValueError):
                        continue
    
    except Exception as e:
        print(f"Error analyzing resource usage: {str(e)}")
    
    # Finalize metrics
    metrics["total_users"] = len(users)
    if metrics["total_users"] > 0:
        metrics["avg_queries_per_user"] = metrics["total_queries"] / metrics["total_users"]
    
    # Convert defaultdict to regular dict for serialization
    metrics["usage_by_day"] = dict(metrics["usage_by_day"])
    metrics["usage_by_hour"] = dict(metrics["usage_by_hour"])
    metrics["popular_query_types"] = dict(metrics["popular_query_types"])
    
    return metrics

def estimate_costs(user_id=None, start_date=None, end_date=None):
    """
    Estimate usage costs based on logs.
    
    Args:
        user_id (str, optional): Filter by user ID
        start_date (str, optional): Start date (YYYY-MM-DD)
        end_date (str, optional): End date (YYYY-MM-DD)
        
    Returns:
        dict: Cost estimates
    """
    # Define cost factors
    QUERY_COST = 0.0001  # Cost per query in dollars
    API_CALL_COST = 0.002  # Cost per API call in dollars
    VISUALIZATION_COST = 0.0005  # Cost per visualization in dollars
    
    costs = {
        "total_cost": 0.0,
        "query_cost": 0.0,
        "api_cost": 0.0,
        "visualization_cost": 0.0,
        "breakdown_by_day": defaultdict(float),
        "breakdown_by_user": defaultdict(float) if user_id is None else None
    }
    
    try:
        # Parse date filters if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        
        if end_date:
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            # Set to end of day
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r") as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Filter by user ID if provided
                        if user_id and log_entry.get("user_id") != user_id:
                            continue
                        
                        # Filter by date range if provided
                        if start_dt or end_dt:
                            timestamp_str = log_entry.get("timestamp", "")
                            if timestamp_str:
                                dt = datetime.datetime.fromisoformat(timestamp_str)
                                
                                if start_dt and dt < start_dt:
                                    continue
                                
                                if end_dt and dt > end_dt:
                                    continue
                                
                                date_str = dt.strftime("%Y-%m-%d")
                            else:
                                continue
                        else:
                            # Extract date for breakdown
                            timestamp_str = log_entry.get("timestamp", "")
                            if timestamp_str:
                                dt = datetime.datetime.fromisoformat(timestamp_str)
                                date_str = dt.strftime("%Y-%m-%d")
                            else:
                                date_str = "unknown"
                        
                        # Calculate costs based on action type
                        action = log_entry.get("action", "")
                        entry_user_id = log_entry.get("user_id", "unknown")
                        cost = 0.0
                        
                        if action == "query":
                            cost = QUERY_COST
                            costs["query_cost"] += cost
                        elif action == "api_call":
                            cost = API_CALL_COST
                            costs["api_cost"] += cost
                        elif action == "visualization":
                            cost = VISUALIZATION_COST
                            costs["visualization_cost"] += cost
                        
                        # Add to total and breakdowns
                        costs["total_cost"] += cost
                        costs["breakdown_by_day"][date_str] += cost
                        
                        if costs["breakdown_by_user"] is not None:
                            costs["breakdown_by_user"][entry_user_id] += cost
                    
                    except (json.JSONDecodeError, ValueError):
                        continue
    
    except Exception as e:
        print(f"Error estimating costs: {str(e)}")
    
    # Convert defaultdict to regular dict for serialization
    costs["breakdown_by_day"] = dict(costs["breakdown_by_day"])
    if costs["breakdown_by_user"] is not None:
        costs["breakdown_by_user"] = dict(costs["breakdown_by_user"])
    
    return costs

def clear_old_logs(days=30):
    """
    Clear logs older than a specified number of days.
    
    Args:
        days (int): Number of days to keep
        
    Returns:
        int: Number of logs removed
    """
    if not os.path.exists(LOG_PATH):
        return 0
    
    # Calculate cutoff date
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
    
    # Read all logs
    logs = []
    removed_count = 0
    
    try:
        with open(LOG_PATH, "r") as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    timestamp_str = log_entry.get("timestamp", "")
                    
                    if timestamp_str:
                        dt = datetime.datetime.fromisoformat(timestamp_str)
                        if dt >= cutoff_date:
                            logs.append(log_entry)
                        else:
                            removed_count += 1
                    else:
                        logs.append(log_entry)  # Keep entries without timestamp
                
                except json.JSONDecodeError:
                    continue
        
        # Write back the filtered logs
        with open(LOG_PATH, "w") as f:
            for log_entry in logs:
                f.write(json.dumps(log_entry) + "\n")
    
    except Exception as e:
        print(f"Error clearing old logs: {str(e)}")
    
    return removed_count

# Initialize logger when module is imported
initialize_logger()