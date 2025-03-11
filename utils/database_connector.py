import os
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text
import psycopg2
from urllib.parse import quote_plus

def connect_to_database(db_type):
    """
    Connect to a database based on the specified type.
    
    Args:
        db_type (str): The type of database to connect to
        
    Returns:
        object: A database connection object
    """
    if db_type == "PostgreSQL":
        # Get connection parameters from environment variables
        host = os.environ.get("PGHOST", "localhost")
        port = os.environ.get("PGPORT", "5432")
        user = os.environ.get("PGUSER", "postgres")
        password = os.environ.get("PGPASSWORD", "")
        database = os.environ.get("PGDATABASE", "postgres")
        
        # Create connection string
        conn_str = f"postgresql://{user}:{quote_plus(password)}@{host}:{port}/{database}"
        
        try:
            # Create SQLAlchemy engine
            engine = create_engine(conn_str)
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            return engine
        except Exception as e:
            raise Exception(f"Failed to connect to PostgreSQL: {str(e)}")
    
    elif db_type == "MySQL":
        # Implementation for MySQL connection
        raise NotImplementedError("MySQL connection not implemented yet")
    
    elif db_type == "SQLite":
        # Implementation for SQLite connection
        raise NotImplementedError("SQLite connection not implemented yet")
    
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
        if isinstance(conn, sqlalchemy.engine.Engine):
            # SQLAlchemy engine
            if params:
                result = pd.read_sql(text(query), conn, params=params)
            else:
                result = pd.read_sql(text(query), conn)
            return result
        
        elif isinstance(conn, psycopg2.extensions.connection):
            # psycopg2 connection
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Fetch column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch data
            data = cursor.fetchall()
            
            # Create DataFrame
            return pd.DataFrame(data, columns=columns)
        
        else:
            raise TypeError("Unsupported connection type")
    
    except Exception as e:
        raise Exception(f"Query execution failed: {str(e)}")

def list_tables(conn):
    """
    List all tables in the connected database.
    
    Args:
        conn (object): Database connection object
        
    Returns:
        list: List of table names
    """
    try:
        if isinstance(conn, sqlalchemy.engine.Engine):
            # SQLAlchemy engine
            inspector = sqlalchemy.inspect(conn)
            return inspector.get_table_names()
        
        elif isinstance(conn, psycopg2.extensions.connection):
            # psycopg2 connection
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [table[0] for table in cursor.fetchall()]
            return tables
        
        else:
            raise TypeError("Unsupported connection type")
    
    except Exception as e:
        raise Exception(f"Failed to list tables: {str(e)}")

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
        if isinstance(conn, sqlalchemy.engine.Engine):
            # SQLAlchemy engine
            inspector = sqlalchemy.inspect(conn)
            columns = inspector.get_columns(table_name)
            return pd.DataFrame(columns, columns=['name', 'type', 'nullable', 'default'])
        
        elif isinstance(conn, psycopg2.extensions.connection):
            # psycopg2 connection
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
            """)
            schema = cursor.fetchall()
            return pd.DataFrame(schema, columns=['name', 'type', 'nullable', 'default'])
        
        else:
            raise TypeError("Unsupported connection type")
    
    except Exception as e:
        raise Exception(f"Failed to get table schema: {str(e)}")

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
        if isinstance(conn, sqlalchemy.engine.Engine):
            # SQLAlchemy engine
            with conn.begin() as transaction:
                for query in queries:
                    conn.execute(text(query))
            return True
        
        elif isinstance(conn, psycopg2.extensions.connection):
            # psycopg2 connection
            cursor = conn.cursor()
            for query in queries:
                cursor.execute(query)
            conn.commit()
            return True
        
        else:
            raise TypeError("Unsupported connection type")
    
    except Exception as e:
        # Rollback transaction on error
        if isinstance(conn, psycopg2.extensions.connection):
            conn.rollback()
        raise Exception(f"Transaction failed: {str(e)}")
