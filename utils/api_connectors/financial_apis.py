"""
Financial Data API Connector

This module provides connectors for financial data APIs.
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime
from utils.api_connectors.base_connector import BaseApiConnector

logger = logging.getLogger(__name__)

class AlphaVantageConnector(BaseApiConnector):
    """Connector for Alpha Vantage financial data API"""
    
    def __init__(self, credentials: Dict):
        """
        Initialize the Alpha Vantage connector
        
        Args:
            credentials (Dict): Dictionary containing 'api_key'
        """
        super().__init__(
            base_url="https://www.alphavantage.co/query",
            credentials=credentials
        )
    
    def _build_headers(self) -> Dict:
        """
        Alpha Vantage uses query parameters for authentication,
        not headers, so we override this method.
        """
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def fetch_data(self, endpoint: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Fetch data from Alpha Vantage API
        
        Args:
            endpoint (str): Type of data to fetch (stocks, forex, crypto)
            params (Dict, optional): Additional parameters
            
        Returns:
            pd.DataFrame: DataFrame containing the financial data
        """
        api_params = params or {}
        
        # Add API key to parameters
        api_params['apikey'] = self.credentials.get('api_key')
        
        if endpoint == 'stocks':
            return self._fetch_stock_data(api_params)
        elif endpoint == 'forex':
            return self._fetch_forex_data(api_params)
        elif endpoint == 'crypto':
            return self._fetch_crypto_data(api_params)
        else:
            raise ValueError(f"Unsupported endpoint: {endpoint}")
    
    def _fetch_stock_data(self, params: Dict) -> pd.DataFrame:
        """Fetch stock market data"""
        # Set default function to TIME_SERIES_DAILY if not specified
        if 'function' not in params:
            params['function'] = 'TIME_SERIES_DAILY'
        
        # Set default symbol to MSFT if not specified
        if 'symbol' not in params:
            params['symbol'] = 'MSFT'
            
        # Make the request
        response = self._make_request('GET', '', params=params)
        data = response.json()
        
        # Parse the response based on the function
        if params['function'] == 'TIME_SERIES_DAILY':
            time_series_key = 'Time Series (Daily)'
            if time_series_key in data:
                # Convert nested dict to DataFrame
                df = pd.DataFrame.from_dict(data[time_series_key], orient='index')
                # Rename columns
                df.columns = [col.split('. ')[1] for col in df.columns]
                # Convert string values to float
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col])
                # Reset index to make date a column
                df.reset_index(inplace=True)
                df.rename(columns={'index': 'date'}, inplace=True)
                # Convert date to datetime
                df['date'] = pd.to_datetime(df['date'])
                return df
            else:
                logger.error(f"Unexpected response format: {data}")
                raise ValueError("Unexpected response format")
        else:
            # Handle other function types as needed
            return pd.DataFrame(data)
    
    def _fetch_forex_data(self, params: Dict) -> pd.DataFrame:
        """Fetch foreign exchange data"""
        # Set default function if not specified
        if 'function' not in params:
            params['function'] = 'FX_DAILY'
        
        # Set default from_currency and to_currency if not specified
        if 'from_currency' not in params:
            params['from_currency'] = 'EUR'
        if 'to_currency' not in params:
            params['to_currency'] = 'USD'
            
        # Make the request
        response = self._make_request('GET', '', params=params)
        data = response.json()
        
        # Check for error messages in the response
        if 'Error Message' in data:
            logger.error(f"Alpha Vantage API error: {data['Error Message']}")
            raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
        
        # Check for rate limit messages (Information field)
        if 'Information' in data:
            logger.error(f"Alpha Vantage API rate limit: {data['Information']}")
            raise ValueError(f"Alpha Vantage API rate limit: {data['Information']}")
        
        # Process response similar to stock data
        # Implementation would be similar to _fetch_stock_data
        # with appropriate keys for the forex data
        
        # Simplified implementation for now
        return pd.DataFrame(data)
    
    def _fetch_crypto_data(self, params: Dict) -> pd.DataFrame:
        """Fetch cryptocurrency data"""
        # Set default function if not specified
        if 'function' not in params:
            params['function'] = 'DIGITAL_CURRENCY_DAILY'
        
        # Set default symbol and market if not specified
        if 'symbol' not in params:
            params['symbol'] = 'BTC'
        if 'market' not in params:
            params['market'] = 'USD'
            
        # Make the request
        response = self._make_request('GET', '', params=params)
        data = response.json()
        
        # Check for error messages in the response
        if 'Error Message' in data:
            logger.error(f"Alpha Vantage API error: {data['Error Message']}")
            raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
        
        # Check for rate limit messages (Information field)
        if 'Information' in data:
            logger.error(f"Alpha Vantage API rate limit: {data['Information']}")
            raise ValueError(f"Alpha Vantage API rate limit: {data['Information']}")
        
        # Process response similar to stock data
        # Implementation would be similar to _fetch_stock_data
        # with appropriate keys for the crypto data
        
        # Simplified implementation for now
        return pd.DataFrame(data)
    
    def validate_credentials(self) -> bool:
        """
        Validate Alpha Vantage API key
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        if 'api_key' not in self.credentials:
            logger.error("API key not provided")
            return False
            
        try:
            # Make a simple request to check if API key is valid
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'MSFT',
                'apikey': self.credentials['api_key']
            }
            response = self._make_request('GET', '', params=params)
            data = response.json()
            
            # Check if response contains an error message about invalid API key
            if 'Error Message' in data and 'apikey' in data['Error Message'].lower():
                logger.error(f"Invalid API key: {data['Error Message']}")
                return False
            
            # If we get a rate limit message, the API key is still valid
            if 'Information' in data and 'API key' in data['Information']:
                logger.warning(f"API key is valid but rate limited: {data['Information']}")
                return True
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating credentials: {str(e)}")
            return False


# Factory function to create appropriate connector
def create_financial_connector(api_name: str, credentials: Dict) -> BaseApiConnector:
    """
    Create a financial data API connector
    
    Args:
        api_name (str): Name of the financial API
        credentials (Dict): API credentials
        
    Returns:
        BaseApiConnector: Connector instance
    """
    if api_name.lower() == 'alphavantage':
        return AlphaVantageConnector(credentials)
    else:
        raise ValueError(f"Unsupported financial API: {api_name}")


# Function to fetch financial data that will be called from api_integrator.py
def fetch_financial_data(endpoint: str, params: Optional[Dict] = None, credentials: Optional[Dict] = None) -> pd.DataFrame:
    """
    Fetch financial data from the default financial API
    
    Args:
        endpoint (str): Type of data to fetch (stocks, forex, crypto)
        params (Dict, optional): Additional parameters
        credentials (Dict, optional): API credentials
        
    Returns:
        pd.DataFrame: DataFrame containing the financial data
    """
    if not credentials or 'api_key' not in credentials:
        raise ValueError("API key is required for financial data")
        
    # Use Alpha Vantage by default
    connector = create_financial_connector('alphavantage', credentials)
    
    # Validate credentials
    if not connector.validate_credentials():
        raise ValueError("Invalid API credentials")
        
    # Fetch and return data
    return connector.fetch_data(endpoint, params) 