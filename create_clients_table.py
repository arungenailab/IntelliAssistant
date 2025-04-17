"""
Script to create and populate the Clients table in the database.
This will resolve the issue with "Show list of clients" returning no results.
"""
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

def check_table_exists(conn, table_name):
    cursor = conn.cursor()
    try:
        # Query INFORMATION_SCHEMA to check if table exists
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = '{table_name}'
        """)
        result = cursor.fetchone()
        return result[0] > 0
    except Exception as e:
        print(f"Error checking if table exists: {e}")
        return False

def create_clients_table(conn):
    cursor = conn.cursor()
    try:
        # Create Clients table if it doesn't exist
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Clients')
        BEGIN
            CREATE TABLE Clients (
                client_id INT PRIMARY KEY IDENTITY(1,1),
                first_name NVARCHAR(50) NOT NULL,
                last_name NVARCHAR(50) NOT NULL,
                email NVARCHAR(100),
                phone NVARCHAR(20),
                created_date DATETIME DEFAULT GETDATE()
            )
            
            PRINT 'Clients table created successfully.'
        END
        ELSE
        BEGIN
            PRINT 'Clients table already exists.'
        END
        """)
        conn.commit()
        print("Clients table created or already exists")
        return True
    except Exception as e:
        print(f"Error creating Clients table: {e}")
        return False

def populate_sample_data(conn):
    cursor = conn.cursor()
    try:
        # Check if table already has data
        cursor.execute("SELECT COUNT(*) FROM Clients")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Clients table already has {count} records. Skipping sample data insertion.")
            return True
        
        # Sample client data matching the actual table structure
        sample_clients = [
            ('James', 'Wilson', 'james.wilson@example.com', '555-0103'),
            ('Maria', 'Garcia', 'maria.garcia@example.com', '555-0104'),
            ('David', 'Brown', 'david.brown@example.com', '555-0105'),
            ('Linda', 'Miller', 'linda.miller@example.com', '555-0106'),
            ('Robert', 'Davis', 'robert.davis@example.com', '555-0107'),
            ('Susan', 'Anderson', 'susan.anderson@example.com', '555-0108'),
            ('Michael', 'Lee', 'michael.lee@example.com', '555-0109'),
            ('Sarah', 'Taylor', 'sarah.taylor@example.com', '555-0110')
        ]
        
        # Insert sample data with correct column names
        cursor.executemany("""
        INSERT INTO Clients (first_name, last_name, email, phone)
        VALUES (?, ?, ?, ?)
        """, sample_clients)
        
        conn.commit()
        print(f"Successfully inserted {len(sample_clients)} sample clients")
        return True
    except Exception as e:
        print(f"Error populating sample data: {e}")
        conn.rollback()
        return False

def main():
    print("Starting Client table creation and population...")
    
    # Connect to the database
    conn = connect_to_db()
    if not conn:
        print("Unable to connect to the database. Please check your connection settings.")
        return
    
    try:
        # Create the Clients table if it doesn't exist
        if create_clients_table(conn):
            # Populate with sample data
            populate_sample_data(conn)
            
            # Verify data was inserted
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Clients")
            count = cursor.fetchone()[0]
            print(f"Clients table now has {count} records")
            
            # Show some sample data
            print("\nSample client data:")
            # Get the actual column names from the table
            cursor.execute("SELECT TOP 0 * FROM Clients")
            columns = [column[0] for column in cursor.description]
            print(f"\nActual columns in Clients table: {', '.join(columns)}")
            
            # Select data using the actual column names
            cursor.execute("SELECT TOP 3 * FROM Clients")
            rows = cursor.fetchall()
            for row in rows:
                row_data = [str(value) for value in row]
                print(f"Row data: {', '.join(row_data)}")
    finally:
        # Close the connection
        conn.close()
        print("Database connection closed")
    
    print("\nNow you can try 'Show list of clients' again, and it should return results!")

if __name__ == "__main__":
    main()