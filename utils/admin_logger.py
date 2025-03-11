import json
import os
import time
from datetime import datetime
import threading
import queue

# Logger configuration
LOG_FILE = "acb_usage_logs.jsonl"
LOG_QUEUE = queue.Queue()
LOGGING_ENABLED = True
LOG_LOCK = threading.Lock()

# Initialize the logging thread
def initialize_logger():
    """Initialize the background logging thread."""
    if LOGGING_ENABLED:
        log_thread = threading.Thread(target=log_worker, daemon=True)
        log_thread.start()

# Background worker for processing log queue
def log_worker():
    """Worker thread to process the log queue and write to file."""
    while True:
        try:
            # Get log entry from queue
            log_entry = LOG_QUEUE.get()
            
            # Write to log file
            with LOG_LOCK:
                with open(LOG_FILE, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            
            # Mark task as done
            LOG_QUEUE.task_done()
        except Exception as e:
            print(f"Error in log worker: {str(e)}")
            time.sleep(1)  # Sleep to avoid tight loop on error

def log_action(user_id, action, details=None):
    """
    Log a user action with details.
    
    Args:
        user_id (str): User identifier
        action (str): Action type
        details (dict, optional): Additional details
    """
    if not LOGGING_ENABLED:
        return
    
    # Create log entry
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_id,
        "action": action,
        "details": details or {}
    }
    
    # Add to log queue for background processing
    LOG_QUEUE.put(log_entry)

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
            with LOG_LOCK:
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
        print(f"Error getting user logs: {str(e)}")
    
    return user_logs

def get_resource_usage():
    """
    Get resource usage metrics from logs.
    
    Returns:
        dict: Resource usage metrics
    """
    metrics = {
        "total_queries": 0,
        "total_users": set(),
        "data_sources_used": {},
        "query_types": {},
        "errors": 0
    }
    
    try:
        if os.path.exists(LOG_FILE):
            with LOG_LOCK:
                with open(LOG_FILE, 'r') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            
                            # Count users
                            metrics["total_users"].add(log_entry.get("user_id"))
                            
                            # Count actions
                            action = log_entry.get("action")
                            if action == "query":
                                metrics["total_queries"] += 1
                            elif action == "error":
                                metrics["errors"] += 1
                            
                            # Count data sources
                            details = log_entry.get("details", {})
                            if "data_sources" in details:
                                for source in details["data_sources"]:
                                    if source in metrics["data_sources_used"]:
                                        metrics["data_sources_used"][source] += 1
                                    else:
                                        metrics["data_sources_used"][source] = 1
                        except:
                            continue
    except Exception as e:
        print(f"Error getting resource usage: {str(e)}")
    
    # Convert user set to count
    metrics["total_users"] = len(metrics["total_users"])
    
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
    # Mock cost factors (in a real system, these would be based on actual pricing)
    COST_FACTORS = {
        "query": 0.01,  # $0.01 per query
        "file_upload": 0.05,  # $0.05 per file upload
        "database_connect": 0.1,  # $0.10 per database connection
        "visualization": 0.02  # $0.02 per visualization
    }
    
    # Initialize cost tracking
    costs = {
        "total": 0,
        "breakdown": {action: 0 for action in COST_FACTORS},
        "by_user": {}
    }
    
    try:
        if os.path.exists(LOG_FILE):
            with LOG_LOCK:
                with open(LOG_FILE, 'r') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            
                            # Check filters
                            if user_id and log_entry.get("user_id") != user_id:
                                continue
                            
                            if start_date or end_date:
                                log_date = datetime.strptime(log_entry.get("timestamp", ""), "%Y-%m-%d %H:%M:%S").date()
                                
                                if start_date:
                                    start = datetime.strptime(start_date, "%Y-%m-%d").date()
                                    if log_date < start:
                                        continue
                                
                                if end_date:
                                    end = datetime.strptime(end_date, "%Y-%m-%d").date()
                                    if log_date > end:
                                        continue
                            
                            # Calculate cost
                            action = log_entry.get("action")
                            user = log_entry.get("user_id")
                            
                            if action in COST_FACTORS:
                                action_cost = COST_FACTORS[action]
                                
                                # Add to total
                                costs["total"] += action_cost
                                
                                # Add to breakdown
                                costs["breakdown"][action] += action_cost
                                
                                # Add to user breakdown
                                if user not in costs["by_user"]:
                                    costs["by_user"][user] = 0
                                costs["by_user"][user] += action_cost
                        except:
                            continue
    except Exception as e:
        print(f"Error estimating costs: {str(e)}")
    
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
    
    cutoff_date = datetime.now().date()
    cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
    
    new_logs = []
    removed_count = 0
    
    try:
        with LOG_LOCK:
            with open(LOG_FILE, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        log_date = datetime.strptime(log_entry.get("timestamp", ""), "%Y-%m-%d %H:%M:%S").date()
                        
                        if log_date >= cutoff_date:
                            new_logs.append(log_entry)
                        else:
                            removed_count += 1
                    except:
                        new_logs.append(json.loads(line.strip()))
            
            # Write back the filtered logs
            with open(LOG_FILE, 'w') as f:
                for log_entry in new_logs:
                    f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"Error clearing old logs: {str(e)}")
    
    return removed_count

# Initialize the logger when module is imported
initialize_logger()
