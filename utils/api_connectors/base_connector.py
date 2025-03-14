"""
Base API Connector

This module provides the base class for all API connectors.
"""

import requests
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

class BaseApiConnector(ABC):
    """
    Abstract base class for API connectors.
    
    All API connectors should extend this class and implement
    the required methods to ensure consistent behavior.
    """
    
    def __init__(self, base_url: str, credentials: Optional[Dict] = None):
        """
        Initialize the API connector
        
        Args:
            base_url (str): The base URL for the API
            credentials (Dict, optional): Authentication credentials
        """
        self.base_url = base_url
        self.credentials = credentials or {}
        self.headers = self._build_headers()
    
    def _build_headers(self) -> Dict:
        """
        Build HTTP headers for API requests
        
        Returns:
            Dict: Headers for API requests
        """
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Add any authentication headers
        if 'api_key' in self.credentials:
            headers['Authorization'] = f"Bearer {self.credentials['api_key']}"
        
        return headers
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> requests.Response:
        """
        Make an HTTP request to the API
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            params (Dict, optional): Query parameters
            data (Dict, optional): Request body data
            
        Returns:
            requests.Response: Response from the API
        """
        url = f"{self.base_url}/{endpoint}"
        logger.info(f"Making {method} request to {url}")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data
            )
            
            response.raise_for_status()  # Raise exception for error status codes
            return response
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {str(e)}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error occurred: {str(e)}")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timed out: {str(e)}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception occurred: {str(e)}")
            raise
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a GET request to the API
        
        Args:
            endpoint (str): API endpoint
            params (Dict, optional): Query parameters
            
        Returns:
            Dict: Parsed JSON response
        """
        response = self._make_request('GET', endpoint, params=params)
        return response.json()
    
    def post(self, endpoint: str, data: Dict, params: Optional[Dict] = None) -> Dict:
        """
        Make a POST request to the API
        
        Args:
            endpoint (str): API endpoint
            data (Dict): Request body data
            params (Dict, optional): Query parameters
            
        Returns:
            Dict: Parsed JSON response
        """
        response = self._make_request('POST', endpoint, params=params, data=data)
        return response.json()
    
    @abstractmethod
    def fetch_data(self, endpoint: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Fetch data from the API and convert to a DataFrame
        
        Args:
            endpoint (str): Specific API endpoint
            params (Dict, optional): Parameters for the API request
            
        Returns:
            pd.DataFrame: DataFrame containing the API response data
        """
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate API credentials
        
        Returns:
            bool: True if credentials are valid, False otherwise
        """
        pass 