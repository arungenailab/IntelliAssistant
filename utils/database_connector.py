import os
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import create_engine, inspect, text
from urllib.parse import urlparse
import json

def connect_to_database(db_type):
    """
    Connect to a database based on the specified type.
    
    Args:
        db_type (str): The type of database to connect to
        
    Returns:
        object: A database connection object
    """
    if db_type == "PostgreSQL":
        # Use DATABASE_URL from environment if available
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Create engine
        engine = create_engine(database_url)
        return engine
    
    elif db_type == "SQLite":
        # Create a SQLite database in the data directory
        os.makedirs("data", exist_ok=True)
        sqlite_path = os.path.join("data", "acb_database.sqlite")
        engine = create_engine(f"sqlite:///{sqlite_path}")
        return engine
    
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def execute_query(conn, query, params=None):
    """
    Execute a SQL query against a database connection.
    
    Args:
        conn (object): Database connection object
        query (str): SQL query to execute
        params (dict, optional): Parameters for the query
        
    Returns:
        DataFrame: Query results as a pandas DataFrame
    """
    try:
        if params:
            # Execute parameterized query
            result = pd.read_sql(query, conn, params=params)
        else:
            # Execute direct query
            result = pd.read_sql(query, conn)
        
        return result
    except Exception as e:
        raise Exception(f"Error executing query: {str(e)}")

def list_tables(conn):
    """
    List all tables in the connected database.
    
    Args:
        conn (object): Database connection object
        
    Returns:
        list: List of table names
    """
    try:
        inspector = inspect(conn)
        return inspector.get_table_names()
    except Exception as e:
        raise Exception(f"Error listing tables: {str(e)}")

def get_table_schema(conn, table_name):
    """
    Get the schema for a specific table.
    
    Args:
        conn (object): Database connection object
        table_name (str): Name of the table
        
    Returns:
        DataFrame: Table schema information
    """
    try:
        inspector = inspect(conn)
        columns = inspector.get_columns(table_name)
        
        # Convert to DataFrame
        schema_df = pd.DataFrame(columns, columns=["name", "type", "nullable", "default", "primary_key"])
        
        # Try to get primary key
        try:
            pk = inspector.get_pk_constraint(table_name)
            for col in schema_df["name"].tolist():
                if col in pk.get("constrained_columns", []):
                    schema_df.loc[schema_df["name"] == col, "primary_key"] = True
        except:
            pass
        
        # Try to get foreign keys
        try:
            fks = inspector.get_foreign_keys(table_name)
            if fks:
                schema_df["foreign_key"] = False
                for fk in fks:
                    for col in schema_df["name"].tolist():
                        if col in fk.get("constrained_columns", []):
                            schema_df.loc[schema_df["name"] == col, "foreign_key"] = True
                            schema_df.loc[schema_df["name"] == col, "references"] = f"{fk.get('referred_table')}.{fk.get('referred_columns')[0]}"
        except:
            pass
        
        return schema_df
    except Exception as e:
        raise Exception(f"Error getting table schema: {str(e)}")

def execute_transaction(conn, queries):
    """
    Execute multiple queries in a transaction.
    
    Args:
        conn (object): Database connection object
        queries (list): List of SQL queries to execute
        
    Returns:
        bool: True if transaction was successful
    """
    try:
        # Check if connection is an engine or connection
        if hasattr(conn, 'connect'):
            # It's an engine, get a connection
            with conn.connect() as connection:
                with connection.begin():
                    for query in queries:
                        connection.execute(text(query))
        else:
            # It's already a connection
            with conn.begin():
                for query in queries:
                    conn.execute(text(query))
        
        return True
    except Exception as e:
        raise Exception(f"Error executing transaction: {str(e)}")

def get_database_info(conn):
    """
    Get information about the database.
    
    Args:
        conn (object): Database connection object
        
    Returns:
        dict: Database information
    """
    try:
        # Determine database type from connection
        if hasattr(conn, 'url'):
            url = conn.url
            db_type = url.get_dialect().name
        elif hasattr(conn, 'engine'):
            url = conn.engine.url
            db_type = url.get_dialect().name
        else:
            # Try to determine from connection string
            db_url = str(conn)
            parsed = urlparse(db_url)
            db_type = parsed.scheme.split('+')[0]
        
        # Get tables and their row counts
        tables = {}
        for table_name in list_tables(conn):
            try:
                # Get row count
                query = f"SELECT COUNT(*) as count FROM {table_name}"
                result = execute_query(conn, query)
                row_count = result['count'].iloc[0]
                
                # Get column count
                schema = get_table_schema(conn, table_name)
                column_count = len(schema)
                
                tables[table_name] = {
                    "rows": int(row_count),
                    "columns": column_count
                }
            except:
                tables[table_name] = {
                    "rows": "Error",
                    "columns": "Error"
                }
        
        # Build info dictionary
        info = {
            "type": db_type,
            "tables": tables,
            "table_count": len(tables)
        }
        
        return info
    except Exception as e:
        return {"error": str(e)}

def table_to_dataframe(conn, table_name, limit=1000):
    """
    Load a database table into a pandas DataFrame.
    
    Args:
        conn (object): Database connection object
        table_name (str): Name of the table
        limit (int, optional): Maximum number of rows to load
        
    Returns:
        DataFrame: Table data as a DataFrame
    """
    try:
        query = f"SELECT * FROM {table_name}"
        if limit > 0:
            query += f" LIMIT {limit}"
        
        return execute_query(conn, query)
    except Exception as e:
        raise Exception(f"Error loading table data: {str(e)}")

def dataframe_to_table(conn, df, table_name, if_exists='replace'):
    """
    Save a DataFrame to a database table.
    
    Args:
        conn (object): Database connection object
        df (DataFrame): DataFrame to save
        table_name (str): Name of the table
        if_exists (str, optional): How to behave if the table exists
            ('fail', 'replace', or 'append')
        
    Returns:
        bool: True if successful
    """
    try:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
        return True
    except Exception as e:
        raise Exception(f"Error saving DataFrame to table: {str(e)}")