import os
import json
import time
import threading
from datetime import datetime, timedelta
from queue import Queue
import uuid

# Setup paths
LOG_FILE = "acb_usage_logs.jsonl"
log_queue = Queue()
stop_event = threading.Event()
log_thread = None

def initialize_logger():
    """Initialize the background logging thread."""
    global log_thread
    if log_thread is None or not log_thread.is_alive():
        log_thread = threading.Thread(target=log_worker, daemon=True)
        log_thread.start()

def log_worker():
    """Worker thread to process the log queue and write to file."""
    while not stop_event.is_set():
        # Wait for log entries or check stop_event every second
        if log_queue.empty():
            time.sleep(1)
            continue
        
        # Process all available log entries
        log_entries = []
        while not log_queue.empty():
            try:
                log_entries.append(log_queue.get_nowait())
                log_queue.task_done()
            except:
                break
        
        # Write log entries to file
        if log_entries:
            try:
                with open(LOG_FILE, 'a') as f:
                    for entry in log_entries:
                        f.write(json.dumps(entry) + "\n")
            except Exception as e:
                print(f"Error writing to log file: {str(e)}")
    
    print("Log worker thread stopped")

def log_action(user_id, action, details=None):
    """
    Log a user action with details.
    
    Args:
        user_id (str): User identifier
        action (str): Action type
        details (dict, optional): Additional details
    """
    # Create log entry
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "action": action,
        "details": details or {}
    }
    
    # Add to queue
    log_queue.put(log_entry)
    
    # Ensure logger is initialized
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
    user_logs = []
    
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        if log_entry.get("user_id") == user_id:
                            user_logs.append(log_entry)
                            if len(user_logs) >= limit:
                                break
                    except:
                        continue
    except Exception as e:
        print(f"Error reading log file: {str(e)}")
    
    # Sort by timestamp in descending order (newest first)
    user_logs.sort(
        key=lambda x: datetime.strptime(x.get("timestamp", "1970-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S"),
        reverse=True
    )
    
    return user_logs

def get_resource_usage():
    """
    Get resource usage metrics from logs.
    
    Returns:
        dict: Resource usage metrics
    """
    usage = {
        "total_queries": 0,
        "total_users": set(),
        "queries_by_date": {},
        "users_by_date": {},
        "popular_actions": {}
    }
    
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        timestamp = log_entry.get("timestamp", "")
                        action = log_entry.get("action", "")
                        user_id = log_entry.get("user_id", "")
                        
                        if not timestamp or not action:
                            continue
                        
                        # Get just the date part
                        date = timestamp.split()[0]
                        
                        # Count total queries
                        if action == "query":
                            usage["total_queries"] += 1
                            
                            # Count queries by date
                            if date not in usage["queries_by_date"]:
                                usage["queries_by_date"][date] = 0
                            usage["queries_by_date"][date] += 1
                        
                        # Count unique users
                        if user_id:
                            usage["total_users"].add(user_id)
                            
                            # Count users by date
                            if date not in usage["users_by_date"]:
                                usage["users_by_date"][date] = set()
                            usage["users_by_date"][date].add(user_id)
                        
                        # Count actions
                        if action:
                            if action not in usage["popular_actions"]:
                                usage["popular_actions"][action] = 0
                            usage["popular_actions"][action] += 1
                    
                    except:
                        continue
    except Exception as e:
        print(f"Error analyzing logs: {str(e)}")
    
    # Convert sets to counts
    usage["total_users"] = len(usage["total_users"])
    for date in usage["users_by_date"]:
        usage["users_by_date"][date] = len(usage["users_by_date"][date])
    
    return usage

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
    # Define cost factors (illustrative)
    COST_PER_QUERY = 0.02  # $0.02 per query
    COST_PER_VISUALIZATION = 0.05  # $0.05 per visualization
    STORAGE_COST_PER_DAY = 0.001  # $0.001 per day for storage
    
    costs = {
        "query_cost": 0,
        "visualization_cost": 0,
        "storage_cost": 0,
        "total_cost": 0,
        "query_count": 0,
        "visualization_count": 0,
        "storage_days": 0
    }
    
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        
                        # Apply filters
                        if user_id and log_entry.get("user_id") != user_id:
                            continue
                        
                        timestamp = log_entry.get("timestamp", "")
                        if not timestamp:
                            continue
                        
                        # Parse timestamp
                        log_date = timestamp.split()[0]  # Get just the date part
                        
                        # Apply date filters
                        if start_date and log_date < start_date:
                            continue
                        if end_date and log_date > end_date:
                            continue
                        
                        # Count and cost queries
                        if log_entry.get("action") == "query":
                            costs["query_count"] += 1
                            costs["query_cost"] += COST_PER_QUERY
                        
                        # Count and cost visualizations
                        if log_entry.get("action") == "visualization":
                            costs["visualization_count"] += 1
                            costs["visualization_cost"] += COST_PER_VISUALIZATION
                    
                    except:
                        continue
    except Exception as e:
        print(f"Error estimating costs: {str(e)}")
    
    # Calculate storage costs
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            days = (end - start).days + 1
            costs["storage_days"] = days
            costs["storage_cost"] = days * STORAGE_COST_PER_DAY
        except:
            costs["storage_days"] = 30  # Default to 30 days
            costs["storage_cost"] = 30 * STORAGE_COST_PER_DAY
    else:
        costs["storage_days"] = 30  # Default to 30 days
        costs["storage_cost"] = 30 * STORAGE_COST_PER_DAY
    
    # Calculate total cost
    costs["total_cost"] = costs["query_cost"] + costs["visualization_cost"] + costs["storage_cost"]
    
    return costs

def clear_old_logs(days=30):
    """
    Clear logs older than a specified number of days.
    
    Args:
        days (int): Number of days to keep
        
    Returns:
        int: Number of logs removed
    """
    if not os.path.exists(LOG_FILE):
        return 0
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
    
    # Read all logs
    all_logs = []
    removed_count = 0
    
    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    timestamp = log_entry.get("timestamp", "1970-01-01 00:00:00")
                    
                    # Keep logs newer than cutoff date
                    if timestamp >= cutoff_str:
                        all_logs.append(log_entry)
                    else:
                        removed_count += 1
                except:
                    # Keep lines we couldn't parse (shouldn't happen)
                    all_logs.append(json.loads(line.strip()))
    except Exception as e:
        print(f"Error reading logs for cleanup: {str(e)}")
        return 0
    
    # Write back the logs to keep
    try:
        with open(LOG_FILE, 'w') as f:
            for log_entry in all_logs:
                f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Error writing logs after cleanup: {str(e)}")
        return 0
    
    return removed_count

# Initialize the logger when the module is imported
initialize_logger()