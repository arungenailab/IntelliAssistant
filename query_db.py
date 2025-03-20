import pyodbc
import sys
from config import DB_CONFIG

def connect_to_db():
    connection_string = f"DRIVER={{SQL Server}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};Trusted_Connection={DB_CONFIG['trusted_connection']}"
    try:
        conn = pyodbc.connect(connection_string)
        print("Successfully connected to database!")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def get_tables(conn):
    cursor = conn.cursor()
    try:
        # Query to get all tables in the database
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tables = cursor.fetchall()
        return [table[0] for table in tables]
    except Exception as e:
        print(f"Error fetching tables: {e}")
        return []

def count_clients(conn):
    cursor = conn.cursor()
    try:
        print("Executing client count query...")
        cursor.execute("SELECT COUNT(*) FROM Clients")
        result = cursor.fetchone()
        print(f"Raw result: {result}")
        if result:
            count = result[0]
            print(f"Count from query: {count}")
            return count
        return 0
    except Exception as e:
        print(f"Error counting clients: {e}")
        return None

def get_client_schema(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'Clients'
            ORDER BY ORDINAL_POSITION
        """)
        columns = cursor.fetchall()
        return columns
    except Exception as e:
        print(f"Error fetching client schema: {e}")
        return []

if __name__ == "__main__":
    conn = connect_to_db()
    
    # Get all tables
    tables = get_tables(conn)
    print("\nAll tables in database:")
    for table in tables:
        print(f"- {table}")
    
    # Count clients
    print("\nCounting clients...")
    client_count = count_clients(conn)
    if client_count is not None:
        print(f"\nNumber of clients in the database: {client_count}")
    else:
        print("\nFailed to count clients.")
    
    # Get client table schema
    print("\nClient table schema:")
    columns = get_client_schema(conn)
    for col_name, data_type in columns:
        print(f"- {col_name} ({data_type})")
        
    conn.close() 