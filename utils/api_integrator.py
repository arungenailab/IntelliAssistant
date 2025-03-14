import os
import json
import requests
import pandas as pd
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApiIntegrationError(Exception):
    """Exception raised for API integration errors"""
    pass

class ApiDataCache:
    """Simple cache for API responses to minimize redundant calls"""
    
    def __init__(self, max_age_seconds=300):
        self.cache = {}
        self.max_age_seconds = max_age_seconds
    
    def get(self, cache_key):
        """Get data from cache if it exists and is not expired"""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if datetime.now() - entry['timestamp'] < timedelta(seconds=self.max_age_seconds):
                logger.info(f"Cache hit for {cache_key}")
                return entry['data']
            else:
                logger.info(f"Cache expired for {cache_key}")
                del self.cache[cache_key]
        return None
    
    def set(self, cache_key, data):
        """Store data in cache with current timestamp"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        logger.info(f"Cached data for {cache_key}")
    
    def clear(self):
        """Clear all cached data"""
        self.cache = {}
        logger.info("Cache cleared")

# Initialize global cache
api_cache = ApiDataCache()

def get_available_api_sources():
    """
    Get a list of all available API data sources
    
    Returns:
        List[Dict]: List of available API sources with metadata
    """
    # This would be expanded as more connectors are added
    return [
        {
            'id': 'financial',
            'name': 'Financial Data API',
            'description': 'Stock market data, currency exchange rates, and financial indicators',
            'auth_required': True,
            'auth_type': 'api_key',
            'endpoints': ['stocks', 'forex', 'crypto']
        },
        {
            'id': 'weather',
            'name': 'Weather Data API',
            'description': 'Current weather conditions and forecasts for locations worldwide',
            'auth_required': True,
            'auth_type': 'api_key',
            'endpoints': ['current', 'forecast', 'historical']
        },
        {
            'id': 'public_data',
            'name': 'Public Datasets API',
            'description': 'Open government and public datasets',
            'auth_required': False,
            'endpoints': ['census', 'economic', 'health']
        },
        {
            'id': 'sql_server',
            'name': 'SQL Server Database',
            'description': 'Connect to Microsoft SQL Server databases to fetch and analyze data',
            'auth_required': True,
            'auth_type': 'database',
            'connection_params': [
                {'name': 'server', 'type': 'string', 'required': True, 'description': 'Server name or IP address'},
                {'name': 'database', 'type': 'string', 'required': True, 'description': 'Database name'},
                {'name': 'username', 'type': 'string', 'required': False, 'description': 'Username (for SQL auth)'},
                {'name': 'password', 'type': 'password', 'required': False, 'description': 'Password (for SQL auth)'},
                {'name': 'trusted_connection', 'type': 'boolean', 'required': False, 'description': 'Use Windows Authentication'}
            ],
            'endpoints': ['custom_query', 'table_data']
        }
    ]

def fetch_api_data(api_source_id, endpoint, params=None, credentials=None, use_cache=True):
    """
    Fetch data from an external API
    
    Args:
        api_source_id (str): ID of the API source
        endpoint (str): Specific endpoint to query
        params (Dict, optional): Parameters for the API request
        credentials (Dict, optional): Credentials for authenticated APIs
        use_cache (bool): Whether to use cached data if available
        
    Returns:
        pd.DataFrame: DataFrame containing the API response data
    """
    # Create cache key based on request parameters
    cache_key = f"{api_source_id}_{endpoint}_{json.dumps(params or {})}"
    
    # Check cache first if enabled
    if use_cache:
        cached_data = api_cache.get(cache_key)
        if cached_data is not None:
            return cached_data
    
    # Import specific connector based on API source ID
    try:
        if api_source_id == 'financial':
            from utils.api_connectors.financial_apis import fetch_financial_data
            raw_data = fetch_financial_data(endpoint, params, credentials)
        elif api_source_id == 'weather':
            from utils.api_connectors.weather_apis import fetch_weather_data
            raw_data = fetch_weather_data(endpoint, params, credentials)
        elif api_source_id == 'public_data':
            from utils.api_connectors.public_data_apis import fetch_public_data
            raw_data = fetch_public_data(endpoint, params)
        elif api_source_id == 'sql_server':
            from utils.sql_connector import fetch_sql_data
            
            if endpoint == 'custom_query':
                # For custom queries, params should contain the SQL query
                if not params or 'query' not in params:
                    raise ApiIntegrationError("SQL query is required for custom_query endpoint")
                raw_data = fetch_sql_data(
                    connection_params=credentials,
                    query=params.get('query'),
                    limit=params.get('limit', 1000)
                )
            elif endpoint == 'table_data':
                # For table data, params should contain the table name
                if not params or 'table_name' not in params:
                    raise ApiIntegrationError("Table name is required for table_data endpoint")
                raw_data = fetch_sql_data(
                    connection_params=credentials,
                    table_name=params.get('table_name'),
                    limit=params.get('limit', 1000)
                )
            else:
                raise ApiIntegrationError(f"Unsupported endpoint for SQL Server: {endpoint}")
        else:
            raise ApiIntegrationError(f"Unsupported API source: {api_source_id}")
        
        # Convert to DataFrame
        if isinstance(raw_data, pd.DataFrame):
            df = raw_data
        elif isinstance(raw_data, dict):
            df = pd.json_normalize(raw_data)
        elif isinstance(raw_data, list):
            df = pd.DataFrame(raw_data)
        else:
            raise ApiIntegrationError(f"Unexpected data format from {api_source_id} API")
        
        # Cache the result
        if use_cache:
            api_cache.set(cache_key, df)
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching data from {api_source_id} API: {str(e)}")
        
        # Provide a more user-friendly error message for rate limit errors
        error_message = str(e)
        if "rate limit" in error_message.lower() and api_source_id == 'financial':
            raise ApiIntegrationError(
                "The financial data API rate limit has been reached. "
                "Alpha Vantage free tier allows only 25 requests per day. "
                "Please try again tomorrow or consider upgrading to a premium plan."
            )
        
        raise ApiIntegrationError(f"Error fetching data: {error_message}")

def save_api_credentials(api_source_id, credentials):
    """
    Save API credentials (to be implemented with secure storage)
    
    Args:
        api_source_id (str): ID of the API source
        credentials (Dict): Credentials to save
        
    Returns:
        bool: Success status
    """
    # In a production system, credentials would be securely encrypted
    # For now, we'll just validate them
    
    try:
        # Simple validation based on API source
        if api_source_id == 'financial':
            if 'api_key' not in credentials:
                raise ValueError("API key is required for financial data API")
        elif api_source_id == 'weather':
            if 'api_key' not in credentials:
                raise ValueError("API key is required for weather data API")
        elif api_source_id == 'sql_server':
            if 'server' not in credentials or 'database' not in credentials:
                raise ValueError("Server and database names are required for SQL Server connection")
            
            # For SQL Server, we should validate the connection
            # But we'll just log it for now since test_connection endpoint already validates
            logger.info(f"SQL Server credentials validated: server={credentials.get('server')}, database={credentials.get('database')}")
                
        # In a real implementation, we would securely store credentials here
        logger.info(f"Credentials for {api_source_id} validated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error saving credentials for {api_source_id}: {str(e)}")
        raise ApiIntegrationError(f"Error saving credentials: {str(e)}") 