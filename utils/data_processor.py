import pandas as pd
import numpy as np
import re
from utils.database_connector import execute_query

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
    # Process query differently based on the source type
    try:
        # Check if query is for a specific dataframe or database
        dataframes_used = []
        
        # Check for dataframe references in the query
        for df_name in dataframes:
            if df_name.lower() in query.lower():
                dataframes_used.append(df_name)
        
        # If querying database
        if db_connection and (not dataframes_used or "SELECT" in query.upper()):
            # Execute direct SQL query against the database
            result = execute_query(db_connection, query)
            return result, ["database"]
        
        # If we have dataframes to query
        elif dataframes_used:
            # Handle single dataframe query
            if len(dataframes_used) == 1:
                df_name = dataframes_used[0]
                df = dataframes[df_name]
                
                # Parse the query to extract components
                # This is a simplified parser
                select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE)
                where_match = re.search(r'WHERE\s+(.*?)(?:\s+ORDER BY|\s+GROUP BY|\s+LIMIT|$)', query, re.IGNORECASE)
                order_by_match = re.search(r'ORDER BY\s+(.*?)(?:\s+LIMIT|$)', query, re.IGNORECASE)
                group_by_match = re.search(r'GROUP BY\s+(.*?)(?:\s+ORDER BY|\s+LIMIT|$)', query, re.IGNORECASE)
                limit_match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
                
                select_columns = "*"
                if select_match:
                    select_columns = select_match.group(1).strip()
                
                where_condition = None
                if where_match:
                    where_condition = where_match.group(1).strip()
                
                order_by = None
                if order_by_match:
                    order_by = order_by_match.group(1).strip()
                
                group_by = None
                if group_by_match:
                    group_by = group_by_match.group(1).strip()
                
                limit = None
                if limit_match:
                    limit = int(limit_match.group(1))
                
                result = process_single_dataframe_query(
                    df,
                    select_columns,
                    where_condition,
                    order_by,
                    group_by,
                    limit
                )
                
                return result, dataframes_used
            
            # Handle join query
            else:
                result = process_join_query(query, dataframes, dataframes_used)
                return result, dataframes_used
        
        # No recognized source in query
        else:
            # Try to execute on all dataframes if there are any
            if dataframes:
                # For simple queries, default to the first dataframe
                df = list(dataframes.values())[0]
                df_name = list(dataframes.keys())[0]
                
                # Extract query components
                select_match = re.search(r'SELECT\s+(.*?)(?:\s+WHERE|\s+ORDER BY|\s+GROUP BY|\s+LIMIT|$)', query, re.IGNORECASE)
                where_match = re.search(r'WHERE\s+(.*?)(?:\s+ORDER BY|\s+GROUP BY|\s+LIMIT|$)', query, re.IGNORECASE)
                
                select_columns = "*"
                if select_match:
                    select_columns = select_match.group(1).strip()
                
                where_condition = None
                if where_match:
                    where_condition = where_match.group(1).strip()
                
                result = process_single_dataframe_query(
                    df,
                    select_columns,
                    where_condition
                )
                
                return result, [df_name]
            
            # No dataframes available
            else:
                return None, []
    
    except Exception as e:
        raise Exception(f"Error processing query: {str(e)}")

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
    result = df.copy()
    
    # Process SELECT
    if select_columns and select_columns != "*":
        # Handle aggregate functions
        if any(func in select_columns.lower() for func in ['count(', 'sum(', 'avg(', 'min(', 'max(']):
            # This is a simplified approach - in a full implementation
            # we would parse the aggregate functions more thoroughly
            if group_by:
                # We're grouping and aggregating
                group_cols = [col.strip() for col in group_by.split(',')]
                
                # Extract aggregations
                agg_funcs = {}
                for agg in re.finditer(r'(count|sum|avg|min|max)\(([^)]+)\)', select_columns, re.IGNORECASE):
                    func, col = agg.groups()
                    col = col.strip()
                    if col not in agg_funcs:
                        agg_funcs[col] = []
                    agg_funcs[col].append(func.lower())
                
                # Convert avg to mean for pandas
                for col, funcs in agg_funcs.items():
                    if 'avg' in funcs:
                        funcs.remove('avg')
                        funcs.append('mean')
                
                # Perform groupby and aggregation
                result = result.groupby(group_cols).agg(agg_funcs).reset_index()
            else:
                # Aggregation without grouping
                columns = []
                for col in select_columns.split(','):
                    col = col.strip()
                    if 'count(' in col.lower():
                        match = re.search(r'count\(([^)]+)\)', col, re.IGNORECASE)
                        if match:
                            count_col = match.group(1).strip()
                            result = pd.DataFrame({f'count({count_col})': [result[count_col].count()]})
                            columns.append(f'count({count_col})')
                    elif 'sum(' in col.lower():
                        match = re.search(r'sum\(([^)]+)\)', col, re.IGNORECASE)
                        if match:
                            sum_col = match.group(1).strip()
                            if not columns:
                                result = pd.DataFrame({f'sum({sum_col})': [result[sum_col].sum()]})
                            else:
                                result[f'sum({sum_col})'] = result[sum_col].sum()
                            columns.append(f'sum({sum_col})')
                    elif 'avg(' in col.lower() or 'mean(' in col.lower():
                        match = re.search(r'(avg|mean)\(([^)]+)\)', col, re.IGNORECASE)
                        if match:
                            avg_col = match.group(2).strip()
                            if not columns:
                                result = pd.DataFrame({f'avg({avg_col})': [result[avg_col].mean()]})
                            else:
                                result[f'avg({avg_col})'] = result[avg_col].mean()
                            columns.append(f'avg({avg_col})')
                    elif 'min(' in col.lower():
                        match = re.search(r'min\(([^)]+)\)', col, re.IGNORECASE)
                        if match:
                            min_col = match.group(1).strip()
                            if not columns:
                                result = pd.DataFrame({f'min({min_col})': [result[min_col].min()]})
                            else:
                                result[f'min({min_col})'] = result[min_col].min()
                            columns.append(f'min({min_col})')
                    elif 'max(' in col.lower():
                        match = re.search(r'max\(([^)]+)\)', col, re.IGNORECASE)
                        if match:
                            max_col = match.group(1).strip()
                            if not columns:
                                result = pd.DataFrame({f'max({max_col})': [result[max_col].max()]})
                            else:
                                result[f'max({max_col})'] = result[max_col].max()
                            columns.append(f'max({max_col})')
                
                if columns:
                    result = result[columns]
        else:
            # Simple column selection
            cols = [col.strip() for col in select_columns.split(',')]
            valid_cols = [col for col in cols if col in df.columns]
            if valid_cols:
                result = result[valid_cols]
    
    # Process WHERE
    if where_condition:
        # This is a simplified evaluation of WHERE conditions
        # Convert SQL operators to Python/pandas equivalents
        condition = where_condition.replace('=', '==').replace('<>', '!=')
        
        # Handle string literals
        condition = re.sub(r"'([^']*)'", r"'\1'", condition)
        
        # Evaluate the condition
        try:
            mask = result.eval(condition)
            result = result[mask]
        except:
            # If eval fails, fallback to filtering with query()
            try:
                result = result.query(condition)
            except:
                # If both methods fail, return the original dataframe
                pass
    
    # Process GROUP BY
    if group_by and not any(func in select_columns.lower() for func in ['count(', 'sum(', 'avg(', 'min(', 'max(']):
        group_cols = [col.strip() for col in group_by.split(',')]
        result = result.groupby(group_cols).size().reset_index(name='count')
    
    # Process ORDER BY
    if order_by:
        order_cols = []
        ascending = []
        for col in order_by.split(','):
            col = col.strip()
            if ' DESC' in col.upper():
                order_cols.append(col.replace(' DESC', '').replace(' desc', '').strip())
                ascending.append(False)
            elif ' ASC' in col.upper():
                order_cols.append(col.replace(' ASC', '').replace(' asc', '').strip())
                ascending.append(True)
            else:
                order_cols.append(col.strip())
                ascending.append(True)
        
        result = result.sort_values(by=order_cols, ascending=ascending)
    
    # Process LIMIT
    if limit:
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
    # Extract join condition if present
    join_match = re.search(r'JOIN\s+(\w+)\s+ON\s+(.*?)(?:\s+WHERE|\s+ORDER BY|\s+GROUP BY|\s+LIMIT|$)', query, re.IGNORECASE)
    
    if join_match:
        # Process explicit join
        second_df_name = join_match.group(1).strip()
        join_condition = join_match.group(2).strip()
        
        # Find the first dataframe
        first_df_name = next((name for name in dataframes_used if name != second_df_name), dataframes_used[0])
        
        # Get the dataframes
        first_df = dataframes[first_df_name]
        second_df = dataframes[second_df_name]
        
        # Extract join keys
        join_keys_match = re.search(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', join_condition, re.IGNORECASE)
        
        if join_keys_match:
            first_table, first_key, second_table, second_key = join_keys_match.groups()
            
            # Perform the join
            if first_table.lower() == first_df_name.lower():
                result = pd.merge(first_df, second_df, left_on=first_key, right_on=second_key)
            else:
                result = pd.merge(first_df, second_df, left_on=second_key, right_on=first_key)
            
            # Apply additional filters from the original query
            result = process_single_dataframe_query(
                result,
                "*",  # We'll select everything for now
                None  # No WHERE condition for simplicity
            )
            
            return result
    
    # If no explicit join or if the join processing failed,
    # try to join the dataframes on common column names
    return join_on_common_columns(dataframes, dataframes_used)

def join_on_common_columns(dataframes, dataframes_used):
    """
    Join dataframes on common column names.
    
    Args:
        dataframes (dict): Dictionary of dataframes
        dataframes_used (list): List of dataframe names to join
        
    Returns:
        DataFrame: Join result
    """
    if not dataframes_used or len(dataframes_used) < 2:
        return None
    
    # Get the dataframes to join
    dfs_to_join = [dataframes[name] for name in dataframes_used if name in dataframes]
    
    if len(dfs_to_join) < 2:
        return dfs_to_join[0] if dfs_to_join else None
    
    # Find common columns
    common_cols = set.intersection(*(set(df.columns) for df in dfs_to_join))
    
    if not common_cols:
        # No common columns, can't join automatically
        return dfs_to_join[0]  # Return first dataframe
    
    # Use the first common column as join key
    join_col = list(common_cols)[0]
    
    # Perform the join
    result = dfs_to_join[0]
    for df in dfs_to_join[1:]:
        result = pd.merge(result, df, on=join_col)
    
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
        return dfs[0] if dfs else None
    
    # If join keys are not specified, try to find common columns
    if not join_keys:
        common_cols = set.intersection(*(set(df.columns) for df in dfs))
        if not common_cols:
            return dfs[0]  # Return first dataframe if no common columns
        
        join_keys = {i: list(common_cols)[0] for i in range(len(dfs))}
    
    # Perform the join
    result = dfs[0]
    for i, df in enumerate(dfs[1:], start=1):
        left_key = join_keys.get(0, join_keys.get(i-1))
        right_key = join_keys.get(i)
        
        if left_key and right_key:
            result = pd.merge(result, df, left_on=left_key, right_on=right_key, how=join_type)
        else:
            # If keys are not specified, join on all common columns
            common_cols = set(result.columns).intersection(set(df.columns))
            if common_cols:
                result = pd.merge(result, df, on=list(common_cols), how=join_type)
    
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
    result = df.copy()
    
    # Process text columns
    if text_cols:
        for col in text_cols:
            if col in df.columns and df[col].dtype == 'object':
                # Add character count
                result[f'{col}_char_count'] = df[col].astype(str).str.len()
                
                # Add word count
                result[f'{col}_word_count'] = df[col].astype(str).str.split().str.len()
    
    # Process date columns
    if date_cols:
        for col in date_cols:
            if col in df.columns:
                try:
                    # Convert to datetime if not already
                    if not pd.api.types.is_datetime64_any_dtype(df[col]):
                        result[col] = pd.to_datetime(df[col], errors='coerce')
                    
                    # Extract date features
                    result[f'{col}_year'] = result[col].dt.year
                    result[f'{col}_month'] = result[col].dt.month
                    result[f'{col}_day'] = result[col].dt.day
                    result[f'{col}_dayofweek'] = result[col].dt.dayofweek
                except:
                    pass
    
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
    if not agg_cols:
        # If no aggregation columns specified, use numeric columns
        agg_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not agg_funcs:
        # Default aggregation functions
        agg_funcs = ['count', 'mean', 'sum', 'min', 'max']
    
    # Create aggregation dictionary
    agg_dict = {col: agg_funcs for col in agg_cols if col not in group_cols}
    
    # Perform aggregation
    result = df.groupby(group_cols).agg(agg_dict).reset_index()
    
    return result