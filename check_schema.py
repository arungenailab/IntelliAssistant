import pyodbc
import pandas as pd

# Set pandas display options to show all columns
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

# Connection parameters
conn_params = {
    'server': 'AVDAILAB15-34\\SQLEXPRESS',
    'database': 'fintest',
    'trusted_connection': 'yes'
}

# Build connection string
conn_str = f"DRIVER={{SQL Server}};SERVER={conn_params['server']};DATABASE={conn_params['database']};Trusted_Connection=yes"

try:
    # Connect to database
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Get table schema
    query = """
    SELECT 
        COLUMN_NAME, 
        DATA_TYPE,
        CHARACTER_MAXIMUM_LENGTH,
        IS_NULLABLE
    FROM 
        INFORMATION_SCHEMA.COLUMNS 
    WHERE 
        TABLE_NAME = 'Transactions'
    ORDER BY 
        ORDINAL_POSITION
    """
    
    df = pd.read_sql_query(query, conn)
    print("\nTransactions table schema:")
    print(df)
    
    # Get sample data
    query = "SELECT TOP 5 * FROM Transactions"
    df = pd.read_sql_query(query, conn)
    print("\nSample data from Transactions:")
    print(df)
    
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    if 'conn' in locals():
        conn.close() 