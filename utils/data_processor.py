import pandas as pd
import numpy as np
import re

def process_query(query, dataframes, db_connection=None):
    """
    Process a SQL-like query against dataframes or database.
    
    Args:
        query (str): The SQL-like query to process
        dataframes (dict): Dictionary of dataframes {name: dataframe}
        db_connection (object, optional): Database connection object
        
    Returns:
        tuple: (result, dataframes_used)
            - result: DataFrame or other query result
            - dataframes_used: List of dataframe names used in the query
    """
    # Check if it's a direct SQL query for the database
    if db_connection and query.lower().startswith("select"):
        try:
            from utils.database_connector import execute_query
            result = execute_query(db_connection, query)
            return result, ["database"]
        except Exception as e:
            raise Exception(f"Database query error: {str(e)}")
    
    # Simple pattern matching to identify dataframes used
    dataframes_used = []
    for df_name in dataframes.keys():
        # Look for the dataframe name as a whole word
        if re.search(r'\b' + re.escape(df_name) + r'\b', query, re.IGNORECASE):
            dataframes_used.append(df_name)
    
    # Special case: joining multiple dataframes
    if len(dataframes_used) > 1 and ("join" in query.lower() or "merge" in query.lower()):
        return process_join_query(query, dataframes, dataframes_used)
    
    # If only one dataframe, process as a single dataframe query
    if len(dataframes_used) == 1:
        df_name = dataframes_used[0]
        df = dataframes[df_name]
        
        # Very basic SQL-like syntax parsing
        parts = query.lower().split()
        
        # Check for select statement
        if "select" in parts:
            select_idx = parts.index("select")
            
            # Find where the column list ends (at FROM)
            from_idx = parts.index("from") if "from" in parts else len(parts)
            
            # Extract columns to select
            select_cols = " ".join(parts[select_idx + 1:from_idx])
            
            # Parse where condition if it exists
            where_condition = None
            if "where" in parts:
                where_idx = parts.index("where")
                
                # Find the end of the where clause
                end_where_idx = len(parts)
                for end_clause in ["order", "group", "limit"]:
                    if end_clause in parts:
                        end_where_idx = min(end_where_idx, parts.index(end_clause))
                
                where_condition = " ".join(parts[where_idx + 1:end_where_idx])
            
            # Parse order by if it exists
            order_by = None
            if "order" in parts and "by" in parts and parts.index("by") == parts.index("order") + 1:
                order_idx = parts.index("order")
                
                # Find the end of the order by clause
                end_order_idx = len(parts)
                if "limit" in parts:
                    end_order_idx = parts.index("limit")
                
                order_by = " ".join(parts[order_idx + 2:end_order_idx])
            
            # Parse group by if it exists
            group_by = None
            if "group" in parts and "by" in parts and parts.index("by") == parts.index("group") + 1:
                group_idx = parts.index("group")
                
                # Find the end of the group by clause
                end_group_idx = len(parts)
                for end_clause in ["order", "limit"]:
                    if end_clause in parts:
                        end_group_idx = min(end_group_idx, parts.index(end_clause))
                
                group_by = " ".join(parts[group_idx + 2:end_group_idx])
            
            # Parse limit if it exists
            limit = None
            if "limit" in parts:
                limit_idx = parts.index("limit")
                if limit_idx + 1 < len(parts):
                    try:
                        limit = int(parts[limit_idx + 1])
                    except ValueError:
                        pass
            
            # Process the query
            return process_single_dataframe_query(
                df, select_cols, where_condition, order_by, group_by, limit
            ), dataframes_used
    
    # If no dataframes were used or the query couldn't be parsed
    return pd.DataFrame(), []

def process_single_dataframe_query(df, select_columns, where_condition=None, 
                                  order_by=None, group_by=None, limit=None):
    """
    Process a query against a single dataframe.
    
    Args:
        df (DataFrame): The pandas dataframe to query
        select_columns (str): Columns to select
        where_condition (str, optional): WHERE condition
        order_by (str, optional): ORDER BY clause
        group_by (str, optional): GROUP BY clause
        limit (int, optional): LIMIT value
        
    Returns:
        DataFrame: Query result
    """
    # Make a copy of the dataframe to avoid modifying the original
    result = df.copy()
    
    # Process WHERE condition
    if where_condition:
        # Very basic condition parsing (dangerous but simple for demonstration)
        # In a real implementation, use a proper parser
        try:
            # Replace column references with df['column']
            for col in df.columns:
                where_condition = where_condition.replace(col, f"result['{col}']")
            
            # Create a boolean mask
            mask = eval(where_condition)
            result = result[mask]
        except Exception as e:
            raise Exception(f"Error processing WHERE condition: {str(e)}")
    
    # Process GROUP BY
    if group_by:
        try:
            # Simple group by with aggregation
            group_cols = [col.strip() for col in group_by.split(",")]
            
            # If SELECT contains aggregation functions, apply them
            if "count(" in select_columns.lower() or "sum(" in select_columns.lower() or "avg(" in select_columns.lower():
                # Extract aggregation functions
                agg_dict = {}
                
                # Extract count() expressions
                count_pattern = r'count\((.*?)\)'
                count_matches = re.findall(count_pattern, select_columns, re.IGNORECASE)
                for match in count_matches:
                    col = match.strip()
                    if col == "*":
                        agg_dict["_count"] = ("__dummy__", "count")
                    else:
                        agg_dict[f"{col}_count"] = (col, "count")
                
                # Extract sum() expressions
                sum_pattern = r'sum\((.*?)\)'
                sum_matches = re.findall(sum_pattern, select_columns, re.IGNORECASE)
                for match in sum_matches:
                    col = match.strip()
                    agg_dict[f"{col}_sum"] = (col, "sum")
                
                # Extract avg() expressions
                avg_pattern = r'avg\((.*?)\)'
                avg_matches = re.findall(avg_pattern, select_columns, re.IGNORECASE)
                for match in avg_matches:
                    col = match.strip()
                    agg_dict[f"{col}_avg"] = (col, "mean")
                
                # Apply aggregations
                if agg_dict:
                    # Add dummy column for count(*) if needed
                    if ("_count", ("__dummy__", "count")) in agg_dict.items():
                        result["__dummy__"] = 1
                    
                    # Create list of aggregations
                    agg_list = {}
                    for output_col, (input_col, agg_func) in agg_dict.items():
                        if input_col not in agg_list:
                            agg_list[input_col] = []
                        agg_list[input_col].append(agg_func)
                    
                    # Group by and aggregate
                    result = result.groupby(group_cols).agg(agg_list)
                    
                    # Reset index to convert groups back to columns
                    result = result.reset_index()
                else:
                    # If no aggregation functions, just group and count
                    result = result.groupby(group_cols).size().reset_index(name="count")
            else:
                # If no aggregation in SELECT, just group and count
                result = result.groupby(group_cols).size().reset_index(name="count")
        except Exception as e:
            raise Exception(f"Error processing GROUP BY: {str(e)}")
    
    # Process SELECT columns
    if select_columns and select_columns.strip() != "*":
        try:
            # Handle special case of COUNT(*)
            if select_columns.lower().strip() == "count(*)":
                return pd.DataFrame({"count": [len(result)]})
            
            # Split the columns by commas, handling function calls
            cols = []
            current_col = ""
            paren_count = 0
            
            for char in select_columns:
                if char == "," and paren_count == 0:
                    cols.append(current_col.strip())
                    current_col = ""
                else:
                    current_col += char
                    if char == "(":
                        paren_count += 1
                    elif char == ")":
                        paren_count -= 1
            
            if current_col:
                cols.append(current_col.strip())
            
            # Process each column or expression
            selected_cols = []
            for col_expr in cols:
                if "(" in col_expr and ")" in col_expr:
                    # Handle function calls like COUNT, SUM, AVG
                    func_match = re.match(r'(\w+)\((.*?)\)', col_expr)
                    if func_match:
                        func_name = func_match.group(1).lower()
                        arg = func_match.group(2).strip()
                        
                        if func_name == "count":
                            if arg == "*":
                                selected_cols.append("count")
                            else:
                                selected_cols.append(f"{arg}_count")
                        elif func_name == "sum":
                            selected_cols.append(f"{arg}_sum")
                        elif func_name == "avg":
                            selected_cols.append(f"{arg}_avg")
                else:
                    # Regular column
                    selected_cols.append(col_expr)
            
            # Select only the requested columns
            available_cols = [col for col in selected_cols if col in result.columns]
            if available_cols:
                result = result[available_cols]
        except Exception as e:
            raise Exception(f"Error processing SELECT columns: {str(e)}")
    
    # Process ORDER BY
    if order_by:
        try:
            # Split the order by clause into columns and directions
            order_parts = order_by.split(",")
            order_cols = []
            ascending = []
            
            for part in order_parts:
                part = part.strip()
                if " desc" in part.lower():
                    col = part.lower().replace(" desc", "").strip()
                    order_cols.append(col)
                    ascending.append(False)
                elif " asc" in part.lower():
                    col = part.lower().replace(" asc", "").strip()
                    order_cols.append(col)
                    ascending.append(True)
                else:
                    order_cols.append(part)
                    ascending.append(True)
            
            # Apply sorting
            result = result.sort_values(by=order_cols, ascending=ascending)
        except Exception as e:
            raise Exception(f"Error processing ORDER BY: {str(e)}")
    
    # Apply LIMIT
    if limit is not None:
        result = result.head(limit)
    
    return result

def process_join_query(query, dataframes, dataframes_used):
    """
    Process a join query between multiple dataframes.
    
    Args:
        query (str): The SQL-like query
        dataframes (dict): Dictionary of dataframes
        dataframes_used (list): List of dataframe names used in the query
        
    Returns:
        DataFrame: Join result
    """
    # Simple heuristic: look for JOIN ... ON clauses
    join_conditions = []
    join_type = "inner"  # Default
    
    # Check for join type
    if "left join" in query.lower():
        join_type = "left"
    elif "right join" in query.lower():
        join_type = "right"
    elif "full join" in query.lower() or "outer join" in query.lower():
        join_type = "outer"
    
    # Extract JOIN ... ON conditions
    join_pattern = r'join\s+(\w+)\s+on\s+(.*?)(?=\s+(?:join|where|group|order|limit|$))'
    join_matches = re.findall(join_pattern, query.lower())
    
    if join_matches:
        # If explicit join conditions are found
        dfs_to_join = [dataframes[dataframes_used[0]]]
        
        for table_name, condition in join_matches:
            if table_name in dataframes:
                right_df = dataframes[table_name]
                
                # Parse the join condition to extract column names
                condition = condition.strip()
                
                # Simple condition parsing (assumes format like 'table1.col1 = table2.col2')
                parts = condition.split('=')
                if len(parts) == 2:
                    left_col = parts[0].strip().split('.')[-1]
                    right_col = parts[1].strip().split('.')[-1]
                    
                    # Perform the join
                    dfs_to_join.append((right_df, left_col, right_col))
        
        # Perform sequential joins
        result = dfs_to_join[0]
        for right_df, left_col, right_col in dfs_to_join[1:]:
            result = result.merge(right_df, left_on=left_col, right_on=right_col, how=join_type)
        
        return result, dataframes_used
    else:
        # If no explicit join conditions, try to join on common columns
        return join_on_common_columns(dataframes, dataframes_used), dataframes_used

def join_on_common_columns(dataframes, dataframes_used):
    """
    Join dataframes on common column names.
    
    Args:
        dataframes (dict): Dictionary of dataframes
        dataframes_used (list): List of dataframe names to join
        
    Returns:
        DataFrame: Join result
    """
    if not dataframes_used:
        return pd.DataFrame()
    
    # Start with the first dataframe
    result = dataframes[dataframes_used[0]]
    
    # Join with each subsequent dataframe
    for df_name in dataframes_used[1:]:
        right_df = dataframes[df_name]
        
        # Find common columns
        common_cols = list(set(result.columns) & set(right_df.columns))
        
        if common_cols:
            # Join on all common columns
            result = result.merge(right_df, on=common_cols, how='inner')
        else:
            # If no common columns, do a cross join (cartesian product)
            # In pandas, this is achieved by adding a dummy column
            result['__key'] = 1
            right_df['__key'] = 1
            result = result.merge(right_df, on='__key', how='inner')
            result = result.drop('__key', axis=1)
    
    return result

def join_datasets(dfs, join_keys=None, join_type='inner'):
    """
    Join multiple datasets based on specified keys or common columns.
    
    Args:
        dfs (list): List of dataframes to join
        join_keys (dict, optional): Dictionary mapping dataframe index to join column
        join_type (str, optional): Type of join ('inner', 'left', 'right', 'outer')
        
    Returns:
        DataFrame: Joined dataframe
    """
    if not dfs or len(dfs) < 2:
        return dfs[0] if dfs else pd.DataFrame()
    
    # Start with the first dataframe
    result = dfs[0]
    
    for i, right_df in enumerate(dfs[1:], 1):
        # Determine join keys
        if join_keys:
            left_key = join_keys.get(i-1)
            right_key = join_keys.get(i)
            
            if left_key and right_key:
                # Join on specified keys
                result = result.merge(right_df, left_on=left_key, right_on=right_key, how=join_type)
            else:
                # Fall back to common columns
                common_cols = list(set(result.columns) & set(right_df.columns))
                if common_cols:
                    result = result.merge(right_df, on=common_cols, how=join_type)
                else:
                    # Cross join if no common columns
                    result['__key'] = 1
                    right_df['__key'] = 1
                    result = result.merge(right_df, on='__key', how=join_type)
                    result = result.drop('__key', axis=1)
        else:
            # Auto-detect common columns
            common_cols = list(set(result.columns) & set(right_df.columns))
            if common_cols:
                result = result.merge(right_df, on=common_cols, how=join_type)
            else:
                # Cross join if no common columns
                result['__key'] = 1
                right_df['__key'] = 1
                result = result.merge(right_df, on='__key', how=join_type)
                result = result.drop('__key', axis=1)
    
    return result

def extract_features(df, text_cols=None, date_cols=None):
    """
    Extract features from dataframe columns for analysis.
    
    Args:
        df (DataFrame): Input dataframe
        text_cols (list, optional): Text columns to process
        date_cols (list, optional): Date columns to process
        
    Returns:
        DataFrame: Dataframe with extracted features
    """
    # Make a copy of the dataframe
    result = df.copy()
    
    # Auto-detect text columns if not specified
    if text_cols is None:
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Auto-detect date columns if not specified
    if date_cols is None:
        date_cols = []
        for col in df.columns:
            try:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    date_cols.append(col)
                elif df[col].dtype == 'object':
                    # Try to convert to datetime
                    pd.to_datetime(df[col], errors='raise')
                    date_cols.append(col)
            except:
                continue
    
    # Process text columns
    for col in text_cols:
        if col in df.columns:
            # Convert to string if not already
            result[col] = result[col].astype(str)
            
            # Extract text features
            result[f'{col}_length'] = result[col].str.len()
            result[f'{col}_word_count'] = result[col].str.split().str.len()
            
            # Extract more features if column has enough data
            if result[col].str.len().mean() > 10:
                result[f'{col}_capitals'] = result[col].str.count(r'[A-Z]')
                result[f'{col}_digits'] = result[col].str.count(r'[0-9]')
                result[f'{col}_special'] = result[col].str.count(r'[^\w\s]')
    
    # Process date columns
    for col in date_cols:
        if col in df.columns:
            # Convert to datetime if not already
            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                try:
                    result[col] = pd.to_datetime(result[col])
                except:
                    continue
            
            # Extract date features
            result[f'{col}_year'] = result[col].dt.year
            result[f'{col}_month'] = result[col].dt.month
            result[f'{col}_day'] = result[col].dt.day
            result[f'{col}_dayofweek'] = result[col].dt.dayofweek
            result[f'{col}_quarter'] = result[col].dt.quarter
            
            # Extract more features for time data
            if (result[col].dt.hour != 0).any():
                result[f'{col}_hour'] = result[col].dt.hour
    
    return result

def aggregate_data(df, group_cols, agg_cols=None, agg_funcs=None):
    """
    Aggregate data by specified columns and functions.
    
    Args:
        df (DataFrame): Input dataframe
        group_cols (list): Columns to group by
        agg_cols (list, optional): Columns to aggregate
        agg_funcs (list, optional): Aggregation functions
        
    Returns:
        DataFrame: Aggregated dataframe
    """
    # Make sure group_cols is a list
    if isinstance(group_cols, str):
        group_cols = [group_cols]
    
    # Auto-detect numeric columns for aggregation if not specified
    if agg_cols is None:
        agg_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Remove group columns from agg_cols
        agg_cols = [col for col in agg_cols if col not in group_cols]
    
    # Default aggregation functions
    if agg_funcs is None:
        agg_funcs = ['count', 'mean', 'sum', 'min', 'max']
    
    # Create aggregation dictionary
    agg_dict = {}
    for col in agg_cols:
        agg_dict[col] = agg_funcs
    
    # Perform aggregation
    if agg_dict:
        result = df.groupby(group_cols).agg(agg_dict)
        
        # Flatten the column names
        result.columns = ['_'.join(col).strip() for col in result.columns.values]
        
        # Reset index to convert groupby columns back to regular columns
        result = result.reset_index()
    else:
        # If no columns to aggregate, just count by group
        result = df.groupby(group_cols).size().reset_index(name='count')
    
    return result