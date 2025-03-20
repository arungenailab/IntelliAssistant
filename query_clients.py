import pyodbc
from config import DB_CONFIG

def connect_to_db():
    connection_string = f"DRIVER={{SQL Server}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};Trusted_Connection={DB_CONFIG['trusted_connection']}"
    try:
        conn = pyodbc.connect(connection_string)
        print("Successfully connected to database!")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_client_count(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM Clients")
        result = cursor.fetchone()
        return result[0]
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
        return cursor.fetchall()
    except Exception as e:
        print(f"Error getting client schema: {e}")
        return []

def get_all_client_data(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM Clients")
        columns = [column[0] for column in cursor.description]
        results = cursor.fetchall()
        return columns, results
    except Exception as e:
        print(f"Error getting client data: {e}")
        return [], []

if __name__ == "__main__":
    conn = connect_to_db()
    if not conn:
        exit(1)
    
    # Count clients
    client_count = get_client_count(conn)
    print(f"\nTotal number of clients in the database: {client_count}")
    
    # Get client schema
    print("\nClient table schema:")
    schema = get_client_schema(conn)
    for column_name, data_type in schema:
        print(f"- {column_name} ({data_type})")
    
    # Get all client data
    print("\nAll client data:")
    columns, results = get_all_client_data(conn)
    if columns and results:
        print(", ".join(columns))
        print("-" * 80)
        for row in results:
            print(", ".join(str(value) for value in row))
    
    conn.close() 