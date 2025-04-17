"""
Script to directly test the SQL query on the Clients table.
This helps diagnose why 'Show list of clients' returns no results.
"""
import requests
import json
import pyodbc
from config import DB_CONFIG

def test_direct_database_query():
    """Test direct SQL query to the database."""
    try:
        connection_string = f"DRIVER={{SQL Server}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};Trusted_Connection={DB_CONFIG['trusted_connection']}"
        conn = pyodbc.connect(connection_string)
        print("Successfully connected to database!")
        
        cursor = conn.cursor()
        
        # Get the table structure
        cursor.execute("SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Clients' ORDER BY ORDINAL_POSITION")
        columns = cursor.fetchall()
        print("\nClients table structure:")
        for col in columns:
            print(f"Column: {col.COLUMN_NAME}, Type: {col.DATA_TYPE}, Nullable: {col.IS_NULLABLE}")
        
        # Query all data in Clients table
        cursor.execute("SELECT * FROM Clients")
        
        # Get column names
        column_names = [column[0] for column in cursor.description]
        print(f"\nColumn names: {column_names}")
        
        # Fetch and print results
        rows = cursor.fetchall()
        print(f"\nFound {len(rows)} clients in database:")
        
        for row in rows:
            row_as_dict = {column_names[i]: value for i, value in enumerate(row)}
            print(row_as_dict)
            
        conn.close()
        return True
    except Exception as e:
        print(f"Error executing direct database query: {str(e)}")
        return False

def test_api_query():
    """Test the API endpoint for SQL conversion."""
    try:
        api_url = "http://localhost:5000/api/convert_nl_to_sql"
        
        # Prepare the payload
        payload = {
            "query": "Show list of clients",
            "connection_params": DB_CONFIG,
            "execute": True
        }
        
        # Send the request
        print("\nSending request to API endpoint...")
        response = requests.post(api_url, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            print("\nAPI Response:")
            print(f"SQL Query: {result.get('sql', 'No SQL generated')}")
            print(f"Explanation: {result.get('explanation', 'No explanation provided')}")
            
            # Check if there are results
            if result.get('result'):
                print(f"\nFound {len(result['result'])} results from API")
                for row in result['result'][:3]:  # Show first 3 results
                    print(row)
            else:
                print("\nNo results returned from the API")
                
            # Check for any errors
            if result.get('error'):
                print(f"\nError reported: {result['error']}")
                
            return True
        else:
            print(f"\nAPI request failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error testing API query: {str(e)}")
        return False

if __name__ == "__main__":
    print("======== Testing SQL queries for Clients table ========")
    
    print("\n1. Testing direct database query...")
    test_direct_database_query()
    
    print("\n2. Testing API endpoint...")
    test_api_query()
    
    print("\n======== Test completed ========")