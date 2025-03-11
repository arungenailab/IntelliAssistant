import pandas as pd
import numpy as np
import re
import json
from sqlalchemy import text
from typing import Tuple, Dict, List, Any, Optional, Union

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
    # Check if query is empty
    if not query or not isinstance(query, str):
        return pd.DataFrame(), []
    
    # Identify which dataframes are used in the query
    dataframes_used = []
    for name in dataframes.keys():
        # Look for dataframe name in query (as a word, not part of another word)
        if re.search(r'\b' + re.escape(name) + r'\b', query):
            dataframes_used.append(name)
    
    # If no dataframes are referenced but we have a database connection,
    # execute against the database
    if not dataframes_used and db_connection is not None:
        try:
            # Execute the query against the database
            result = pd.read_sql(query, db_connection)
            return result, []
        except Exception as e:
            raise Exception(f"Error executing database query: {str(e)}")
    
    # If we have identified dataframes to use, process the query
    if dataframes_used:
        # Simple case: if only one dataframe is used, try to process as a single dataframe query
        if len(dataframes_used) == 1:
            df_name = dataframes_used[0]
            df = dataframes[df_name]
            
            # Try to parse the query
            try:
                # Extract parts of the query
                select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE)
                where_match = re.search(r'WHERE\s+(.*?)(?:\s+ORDER\s+BY|\s+GROUP\s+BY|\s+LIMIT|\s*$)', query, re.IGNORECASE)
                order_match = re.search(r'ORDER\s+BY\s+(.*?)(?:\s+LIMIT|\s*$)', query, re.IGNORECASE)
                group_match = re.search(r'GROUP\s+BY\s+(.*?)(?:\s+ORDER\s+BY|\s+LIMIT|\s*$)', query, re.IGNORECASE)
                limit_match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
                
                # Extract the parts
                select_columns = select_match.group(1) if select_match else "*"
                where_condition = where_match.group(1) if where_match else None
                order_by = order_match.group(1) if order_match else None
                group_by = group_match.group(1) if group_match else None
                limit = int(limit_match.group(1)) if limit_match else None
                
                # Process the single dataframe query
                result = process_single_dataframe_query(
                    df, select_columns, where_condition, order_by, group_by, limit
                )
                
                return result, dataframes_used
            
            except Exception as e:
                raise Exception(f"Error processing query on single dataframe: {str(e)}")
        
        # Multiple dataframes: try to handle as a join query
        else:
            try:
                result = process_join_query(query, dataframes, dataframes_used)
                return result, dataframes_used
            except Exception as e:
                raise Exception(f"Error processing join query: {str(e)}")
    
    # If we reach here, we couldn't process the query
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
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Process WHERE clause if present
    if where_condition:
        # Replace SQL-like operators with Python operators
        condition = where_condition.replace('=', '==').replace('<>', '!=')
        
        # Handle SQL LIKE operator
        like_matches = re.finditer(r'(\w+)\s+LIKE\s+[\'"]([^\'"]*)[\'"]', condition, re.IGNORECASE)
        for match in like_matches:
            col_name = match.group(1)
            pattern = match.group(2).replace('%', '.*')
            condition = condition.replace(
                match.group(0),
                f"{col_name}.str.contains('{pattern}', case=False, regex=True)"
            )
        
        # Handle SQL IN operator
        in_matches = re.finditer(r'(\w+)\s+IN\s+\((.*?)\)', condition, re.IGNORECASE)
        for match in in_matches:
            col_name = match.group(1)
            values = match.group(2)
            condition = condition.replace(
                match.group(0),
                f"{col_name}.isin([{values}])"
            )
        
        # Handle SQL BETWEEN operator
        between_matches = re.finditer(r'(\w+)\s+BETWEEN\s+(\S+)\s+AND\s+(\S+)', condition, re.IGNORECASE)
        for match in between_matches:
            col_name = match.group(1)
            lower = match.group(2)
            upper = match.group(3)
            condition = condition.replace(
                match.group(0),
                f"({col_name} >= {lower}) & ({col_name} <= {upper})"
            )
        
        # Apply the condition
        try:
            result_df = result_df.query(condition)
        except Exception as e:
            # If query fails, try a different approach with eval
            try:
                mask = pd.eval(condition, engine='python', local_dict={col: result_df[col] for col in result_df.columns})
                result_df = result_df[mask]
            except:
                raise Exception(f"Error processing WHERE condition: {where_condition}")
    
    # Process GROUP BY clause if present
    if group_by:
        # Split by comma and strip whitespace
        group_cols = [col.strip() for col in group_by.split(',')]
        
        # Check if we have aggregation functions in the SELECT
        if select_columns != "*" and any(agg_func in select_columns.lower() for agg_func in 
                                         ['sum(', 'avg(', 'count(', 'min(', 'max(']):
            # This is a complex aggregation query
            # Parse SELECT to find aggregation functions
            agg_columns = {}
            select_parts = [part.strip() for part in select_columns.split(',')]
            
            for part in select_parts:
                if 'sum(' in part.lower():
                    col = re.search(r'sum\((.*?)\)', part, re.IGNORECASE).group(1)
                    agg_columns[col] = 'sum'
                elif 'avg(' in part.lower():
                    col = re.search(r'avg\((.*?)\)', part, re.IGNORECASE).group(1)
                    agg_columns[col] = 'mean'
                elif 'count(' in part.lower():
                    col = re.search(r'count\((.*?)\)', part, re.IGNORECASE).group(1)
                    agg_columns[col] = 'count'
                elif 'min(' in part.lower():
                    col = re.search(r'min\((.*?)\)', part, re.IGNORECASE).group(1)
                    agg_columns[col] = 'min'
                elif 'max(' in part.lower():
                    col = re.search(r'max\((.*?)\)', part, re.IGNORECASE).group(1)
                    agg_columns[col] = 'max'
            
            # Group by the specified columns and aggregate
            if agg_columns:
                agg_dict = {col: func for col, func in agg_columns.items()}
                result_df = result_df.groupby(group_cols).agg(agg_dict).reset_index()
            else:
                # Simple group by with no aggregation
                result_df = result_df.groupby(group_cols).first().reset_index()
        else:
            # Simple group by with no aggregation
            result_df = result_df.groupby(group_cols).first().reset_index()
    
    # Process SELECT clause if not "*"
    if select_columns != "*":
        # Split by comma and strip whitespace
        columns = [col.strip() for col in select_columns.split(',')]
        
        # Check for aggregation functions
        final_columns = []
        for col in columns:
            # Handle aggregation functions if not already handled by GROUP BY
            if not group_by:
                if 'sum(' in col.lower():
                    agg_col = re.search(r'sum\((.*?)\)', col, re.IGNORECASE).group(1)
                    result_df[col] = result_df[agg_col].sum()
                    final_columns.append(col)
                elif 'avg(' in col.lower():
                    agg_col = re.search(r'avg\((.*?)\)', col, re.IGNORECASE).group(1)
                    result_df[col] = result_df[agg_col].mean()
                    final_columns.append(col)
                elif 'count(' in col.lower():
                    agg_col = re.search(r'count\((.*?)\)', col, re.IGNORECASE).group(1)
                    result_df[col] = result_df[agg_col].count()
                    final_columns.append(col)
                elif 'min(' in col.lower():
                    agg_col = re.search(r'min\((.*?)\)', col, re.IGNORECASE).group(1)
                    result_df[col] = result_df[agg_col].min()
                    final_columns.append(col)
                elif 'max(' in col.lower():
                    agg_col = re.search(r'max\((.*?)\)', col, re.IGNORECASE).group(1)
                    result_df[col] = result_df[agg_col].max()
                    final_columns.append(col)
                else:
                    final_columns.append(col)
            else:
                # If group_by was already processed, we just need the column names
                final_columns.append(col)
        
        # Select only the requested columns
        try:
            result_df = result_df[final_columns]
        except KeyError as e:
            # Handle missing columns
            missing_cols = []
            for col in final_columns:
                if col not in result_df.columns:
                    missing_cols.append(col)
            
            if missing_cols:
                raise KeyError(f"Columns not found: {', '.join(missing_cols)}")
            else:
                raise e
    
    # Process ORDER BY clause if present
    if order_by:
        # Split by comma and strip whitespace
        order_cols = []
        ascending = []
        
        # Parse each part
        for part in order_by.split(','):
            part = part.strip()
            if ' DESC' in part.upper():
                col = part.split(' DESC')[0].strip()
                order_cols.append(col)
                ascending.append(False)
            elif ' ASC' in part.upper():
                col = part.split(' ASC')[0].strip()
                order_cols.append(col)
                ascending.append(True)
            else:
                order_cols.append(part)
                ascending.append(True)
        
        # Apply sorting
        result_df = result_df.sort_values(by=order_cols, ascending=ascending)
    
    # Apply LIMIT if specified
    if limit is not None:
        result_df = result_df.head(limit)
    
    return result_df

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
    # Look for JOIN keyword
    join_match = re.search(r'FROM\s+(\w+)\s+(?:INNER |LEFT |RIGHT |FULL |CROSS )?JOIN', query, re.IGNORECASE)
    
    if join_match:
        # This is an explicit join query
        # This requires more complex parsing, for now we'll use a simpler approach
        # Extract the join condition(s)
        join_conditions = re.finditer(r'JOIN\s+(\w+)\s+ON\s+(.*?)(?:\s+(?:INNER |LEFT |RIGHT |FULL |CROSS )?JOIN|\s+WHERE|\s+GROUP|\s+ORDER|\s+LIMIT|\s*$)', query, re.IGNORECASE)
        
        # Start with the first table
        primary_table = join_match.group(1)
        result_df = dataframes[primary_table].copy()
        
        # Apply each join
        for match in join_conditions:
            secondary_table = match.group(1)
            condition = match.group(2)
            
            # Parse the condition (assuming format like "table1.col1 = table2.col2")
            condition_match = re.search(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', condition)
            
            if condition_match:
                left_table = condition_match.group(1)
                left_col = condition_match.group(2)
                right_table = condition_match.group(3)
                right_col = condition_match.group(4)
                
                # Determine join type
                join_type_match = re.search(r'(INNER|LEFT|RIGHT|FULL|CROSS)\s+JOIN\s+' + re.escape(secondary_table), query, re.IGNORECASE)
                join_type = join_type_match.group(1).lower() if join_type_match else 'inner'
                
                # Perform the join
                if join_type == 'left':
                    result_df = pd.merge(result_df, dataframes[secondary_table], 
                                         left_on=left_col, right_on=right_col, 
                                         how='left', suffixes=('', f'_{secondary_table}'))
                elif join_type == 'right':
                    result_df = pd.merge(result_df, dataframes[secondary_table], 
                                         left_on=left_col, right_on=right_col, 
                                         how='right', suffixes=('', f'_{secondary_table}'))
                elif join_type == 'full':
                    result_df = pd.merge(result_df, dataframes[secondary_table], 
                                         left_on=left_col, right_on=right_col, 
                                         how='outer', suffixes=('', f'_{secondary_table}'))
                elif join_type == 'cross':
                    # Cross join is a cartesian product
                    result_df = pd.merge(result_df, dataframes[secondary_table], 
                                         how='cross', suffixes=('', f'_{secondary_table}'))
                else:  # inner join by default
                    result_df = pd.merge(result_df, dataframes[secondary_table], 
                                         left_on=left_col, right_on=right_col, 
                                         how='inner', suffixes=('', f'_{secondary_table}'))
        
        # Now that we have joined the tables, we need to apply any WHERE, GROUP BY, etc.
        # Extract relevant parts from the query
        where_match = re.search(r'WHERE\s+(.*?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+LIMIT|\s*$)', query, re.IGNORECASE)
        group_match = re.search(r'GROUP\s+BY\s+(.*?)(?:\s+ORDER\s+BY|\s+LIMIT|\s*$)', query, re.IGNORECASE)
        order_match = re.search(r'ORDER\s+BY\s+(.*?)(?:\s+LIMIT|\s*$)', query, re.IGNORECASE)
        limit_match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query, re.IGNORECASE)
        
        # Apply WHERE if present
        if where_match:
            where_condition = where_match.group(1)
            # We need to modify column references like "table.column" to just "column"
            # This is a simplification; a proper implementation would handle column name conflicts
            for table_name in dataframes_used:
                where_condition = where_condition.replace(f"{table_name}.", "")
            
            result_df = process_single_dataframe_query(
                result_df, "*", where_condition, None, None, None
            )
        
        # Apply GROUP BY if present
        if group_match:
            group_by = group_match.group(1)
            # Modify column references
            for table_name in dataframes_used:
                group_by = group_by.replace(f"{table_name}.", "")
            
            select_columns = select_match.group(1) if select_match else "*"
            # Modify column references in SELECT
            for table_name in dataframes_used:
                select_columns = select_columns.replace(f"{table_name}.", "")
            
            result_df = process_single_dataframe_query(
                result_df, select_columns, None, None, group_by, None
            )
        elif select_match:
            # Apply SELECT if no GROUP BY
            select_columns = select_match.group(1)
            # Modify column references
            for table_name in dataframes_used:
                select_columns = select_columns.replace(f"{table_name}.", "")
            
            # Get the list of columns to select
            cols_to_select = [col.strip() for col in select_columns.split(',')]
            
            # Handle special case "SELECT *"
            if select_columns.strip() != "*":
                try:
                    result_df = result_df[cols_to_select]
                except KeyError as e:
                    # Some columns might be missing or have been renamed during the join
                    missing_cols = []
                    for col in cols_to_select:
                        if col not in result_df.columns:
                            missing_cols.append(col)
                    
                    if missing_cols:
                        raise KeyError(f"Columns not found: {', '.join(missing_cols)}")
                    else:
                        raise e
        
        # Apply ORDER BY if present
        if order_match:
            order_by = order_match.group(1)
            # Modify column references
            for table_name in dataframes_used:
                order_by = order_by.replace(f"{table_name}.", "")
            
            result_df = process_single_dataframe_query(
                result_df, "*", None, order_by, None, None
            )
        
        # Apply LIMIT if present
        if limit_match:
            limit = int(limit_match.group(1))
            result_df = result_df.head(limit)
        
        return result_df
    
    else:
        # No explicit JOIN, try to join on common columns
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
    if not dataframes_used:
        return pd.DataFrame()
    
    # Start with the first dataframe
    result = dataframes[dataframes_used[0]].copy()
    
    # Join with each subsequent dataframe
    for df_name in dataframes_used[1:]:
        df = dataframes[df_name]
        
        # Find common columns
        common_cols = list(set(result.columns).intersection(set(df.columns)))
        
        if common_cols:
            # Join on common columns
            result = pd.merge(result, df, on=common_cols, how='inner')
        else:
            # No common columns, do a cross join (cartesian product)
            result['_key'] = 1
            df['_key'] = 1
            result = pd.merge(result, df, on='_key', how='outer')
            result.drop('_key', axis=1, inplace=True)
    
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
    if not dfs:
        return pd.DataFrame()
    
    # Start with the first dataframe
    result = dfs[0].copy()
    
    # Join with each subsequent dataframe
    for i, df in enumerate(dfs[1:], 1):
        if join_keys is not None:
            # Join on specified keys
            left_key = join_keys.get(i-1)
            right_key = join_keys.get(i)
            
            if left_key is not None and right_key is not None:
                result = pd.merge(result, df, left_on=left_key, right_on=right_key, 
                                 how=join_type, suffixes=('', f'_{i}'))
            else:
                # No keys specified, try to find common columns
                common_cols = list(set(result.columns).intersection(set(df.columns)))
                
                if common_cols:
                    # Join on common columns
                    result = pd.merge(result, df, on=common_cols, how=join_type)
                else:
                    # No common columns, do a cross join
                    result['_key'] = 1
                    df['_key'] = 1
                    result = pd.merge(result, df, on='_key', how='outer')
                    result.drop('_key', axis=1, inplace=True)
        else:
            # No keys specified, try to find common columns
            common_cols = list(set(result.columns).intersection(set(df.columns)))
            
            if common_cols:
                # Join on common columns
                result = pd.merge(result, df, on=common_cols, how=join_type)
            else:
                # No common columns, do a cross join
                result['_key'] = 1
                df['_key'] = 1
                result = pd.merge(result, df, on='_key', how='outer')
                result.drop('_key', axis=1, inplace=True)
    
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
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Process text columns
    if text_cols is None:
        # Try to identify text columns automatically
        text_cols = [col for col in df.select_dtypes(include=['object']).columns 
                     if df[col].str.len().mean() > 5]  # Average length > 5 characters
    
    for col in text_cols:
        if col in df.columns:
            # Character count
            result_df[f"{col}_char_count"] = df[col].str.len()
            
            # Word count
            result_df[f"{col}_word_count"] = df[col].str.split().str.len()
            
            # Uppercase count
            result_df[f"{col}_upper_count"] = df[col].str.count(r'[A-Z]')
            
            # Lowercase count
            result_df[f"{col}_lower_count"] = df[col].str.count(r'[a-z]')
            
            # Number count
            result_df[f"{col}_digit_count"] = df[col].str.count(r'[0-9]')
            
            # Special character count
            result_df[f"{col}_special_count"] = df[col].str.count(r'[^\w\s]')
    
    # Process date columns
    if date_cols is None:
        # Try to identify date columns automatically
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
    
    for col in date_cols:
        if col in df.columns:
            # Extract year
            result_df[f"{col}_year"] = df[col].dt.year
            
            # Extract month
            result_df[f"{col}_month"] = df[col].dt.month
            
            # Extract day
            result_df[f"{col}_day"] = df[col].dt.day
            
            # Extract day of week
            result_df[f"{col}_day_of_week"] = df[col].dt.dayofweek
            
            # Extract quarter
            result_df[f"{col}_quarter"] = df[col].dt.quarter
            
            # Is weekend
            result_df[f"{col}_is_weekend"] = df[col].dt.dayofweek.isin([5, 6]).astype(int)
    
    return result_df

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
    if agg_cols is None:
        # Use all numeric columns
        agg_cols = df.select_dtypes(include=['number']).columns.tolist()
        # Remove group columns from aggregation columns
        agg_cols = [col for col in agg_cols if col not in group_cols]
    
    if not agg_cols:
        # No columns to aggregate
        return df.groupby(group_cols).size().reset_index(name='count')
    
    if agg_funcs is None:
        # Default aggregation functions
        agg_funcs = ['sum', 'mean', 'min', 'max', 'count']
    
    # Create aggregation dictionary
    agg_dict = {col: agg_funcs for col in agg_cols}
    
    # Perform aggregation
    result = df.groupby(group_cols).agg(agg_dict)
    
    # Flatten multi-level column index
    result.columns = ['_'.join(col).strip() for col in result.columns.values]
    
    # Reset index to get group columns back as regular columns
    result = result.reset_index()
    
    return result