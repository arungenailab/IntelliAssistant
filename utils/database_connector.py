import os
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text

def connect_to_database(db_type):
    """
    Connect to a database based on the specified type.
    
    Args:
        db_type (str): The type of database to connect to
        
    Returns:
        object: A database connection object
    """
    if db_type == "PostgreSQL":
        # Use environment variable for PostgreSQL connection
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            # If DATABASE_URL is not set, try to construct it from individual env vars
            host = os.environ.get("PGHOST", "localhost")
            port = os.environ.get("PGPORT", "5432")
            user = os.environ.get("PGUSER", "postgres")
            password = os.environ.get("PGPASSWORD", "")
            database = os.environ.get("PGDATABASE", "postgres")
            
            db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        engine = sa.create_engine(db_url)
        conn = engine.connect()
        return conn
    
    elif db_type == "MySQL":
        # Check for MySQL connection details in environment variables
        host = os.environ.get("MYSQL_HOST", "localhost")
        port = os.environ.get("MYSQL_PORT", "3306")
        user = os.environ.get("MYSQL_USER", "root")
        password = os.environ.get("MYSQL_PASSWORD", "")
        database = os.environ.get("MYSQL_DATABASE", "mysql")
        
        db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        
        engine = sa.create_engine(db_url)
        conn = engine.connect()
        return conn
    
    elif db_type == "SQLite":
        # Use in-memory SQLite database for simplicity
        engine = sa.create_engine("sqlite:///:memory:")
        conn = engine.connect()
        return conn
    
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
            # Execute query with parameters
            result = conn.execute(text(query), params)
        else:
            # Execute query without parameters
            result = conn.execute(text(query))
        
        # Convert results to a pandas DataFrame
        if result.returns_rows:
            df = pd.DataFrame(result.fetchall())
            if len(df) > 0:
                df.columns = result.keys()
            return df
        return pd.DataFrame()
    
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
        # Check if we're using SQLAlchemy Engine or Connection
        if hasattr(conn, 'engine'):
            engine = conn.engine
        elif hasattr(conn, 'connection'):
            engine = conn.connection
        else:
            engine = conn
        
        # Get database dialect
        dialect = engine.dialect.name
        
        # Execute dialect-specific query to get table names
        if dialect == 'postgresql':
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        elif dialect == 'mysql':
            query = "SHOW TABLES"
        elif dialect == 'sqlite':
            query = "SELECT name FROM sqlite_master WHERE type='table'"
        else:
            query = "SELECT table_name FROM information_schema.tables"
        
        result = execute_query(conn, query)
        
        # Extract table names from the result
        if len(result) > 0:
            table_names = result.iloc[:, 0].tolist()
            return table_names
        return []
    
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
        # Check if we're using SQLAlchemy Engine or Connection
        if hasattr(conn, 'engine'):
            engine = conn.engine
        elif hasattr(conn, 'connection'):
            engine = conn.connection
        else:
            engine = conn
        
        # Get database dialect
        dialect = engine.dialect.name
        
        # Execute dialect-specific query to get column information
        if dialect == 'postgresql':
            query = f"""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            """
        elif dialect == 'mysql':
            query = f"""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            """
        elif dialect == 'sqlite':
            query = f"PRAGMA table_info('{table_name}')"
        else:
            query = f"""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            """
        
        result = execute_query(conn, query)
        return result
    
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
        # Start a transaction
        transaction = conn.begin()
        
        try:
            # Execute each query in the transaction
            for query in queries:
                conn.execute(text(query))
            
            # Commit the transaction
            transaction.commit()
            return True
        
        except Exception as e:
            # Rollback the transaction if an error occurs
            transaction.rollback()
            raise Exception(f"Transaction error: {str(e)}")
    
    except Exception as e:
        raise Exception(f"Error executing transaction: {str(e)}")