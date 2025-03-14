"""
Weather Data API Connector

This module provides connectors for weather data APIs.
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime
from utils.api_connectors.base_connector import BaseApiConnector

logger = logging.getLogger(__name__)

class OpenWeatherMapConnector(BaseApiConnector):
    """Connector for OpenWeatherMap API"""
    
    def __init__(self, credentials: Dict):
        """
        Initialize the OpenWeatherMap connector
        
        Args:
            credentials (Dict): Dictionary containing 'api_key'
        """
        super().__init__(
            base_url="https://api.openweathermap.org/data/2.5",
            credentials=credentials
        )
    
    def _build_headers(self) -> Dict:
        """
        OpenWeatherMap uses query parameters for authentication,
        not headers, so we override this method.
        """
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def fetch_data(self, endpoint: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """
        Fetch data from OpenWeatherMap API
        
        Args:
            endpoint (str): Type of data to fetch (current, forecast, historical)
            params (Dict, optional): Additional parameters
            
        Returns:
            pd.DataFrame: DataFrame containing the weather data
        """
        api_params = params or {}
        
        # Add API key to parameters
        api_params['appid'] = self.credentials.get('api_key')
        
        if endpoint == 'current':
            return self._fetch_current_weather(api_params)
        elif endpoint == 'forecast':
            return self._fetch_forecast(api_params)
        elif endpoint == 'historical':
            return self._fetch_historical(api_params)
        else:
            raise ValueError(f"Unsupported endpoint: {endpoint}")
    
    def _fetch_current_weather(self, params: Dict) -> pd.DataFrame:
        """Fetch current weather data"""
        # Ensure city parameter is included
        if 'q' not in params and 'lat' not in params and 'lon' not in params:
            # Default to London if no location is provided
            params['q'] = 'London'
            
        # Make the API request
        response = self._make_request('GET', '/weather', params=params)
        data = response.json()
        
        # Create a DataFrame from the response
        df = pd.DataFrame([{
            'city': data.get('name', 'Unknown'),
            'country': data.get('sys', {}).get('country', 'Unknown'),
            'temperature': data.get('main', {}).get('temp'),
            'feels_like': data.get('main', {}).get('feels_like'),
            'humidity': data.get('main', {}).get('humidity'),
            'pressure': data.get('main', {}).get('pressure'),
            'wind_speed': data.get('wind', {}).get('speed'),
            'wind_direction': data.get('wind', {}).get('deg'),
            'clouds': data.get('clouds', {}).get('all'),
            'weather_main': data.get('weather', [{}])[0].get('main'),
            'weather_description': data.get('weather', [{}])[0].get('description'),
            'timestamp': datetime.fromtimestamp(data.get('dt', 0))
        }])
        
        return df
    
    def _fetch_forecast(self, params: Dict) -> pd.DataFrame:
        """Fetch weather forecast data"""
        # Ensure city parameter is included
        if 'q' not in params and 'lat' not in params and 'lon' not in params:
            # Default to London if no location is provided
            params['q'] = 'London'
            
        # Make the API request
        response = self._make_request('GET', '/forecast', params=params)
        data = response.json()
        
        # Extract forecast list
        forecast_list = data.get('list', [])
        city_name = data.get('city', {}).get('name', 'Unknown')
        country = data.get('city', {}).get('country', 'Unknown')
        
        # Create records for DataFrame
        records = []
        for item in forecast_list:
            records.append({
                'city': city_name,
                'country': country,
                'temperature': item.get('main', {}).get('temp'),
                'feels_like': item.get('main', {}).get('feels_like'),
                'humidity': item.get('main', {}).get('humidity'),
                'pressure': item.get('main', {}).get('pressure'),
                'wind_speed': item.get('wind', {}).get('speed'),
                'wind_direction': item.get('wind', {}).get('deg'),
                'clouds': item.get('clouds', {}).get('all'),
                'weather_main': item.get('weather', [{}])[0].get('main'),
                'weather_description': item.get('weather', [{}])[0].get('description'),
                'timestamp': datetime.fromtimestamp(item.get('dt', 0))
            })
        
        # Create DataFrame
        df = pd.DataFrame(records)
        return df
    
    def _fetch_historical(self, params: Dict) -> pd.DataFrame:
        """Fetch historical weather data"""
        # This is a simplified implementation
        # In a real application, you would need to handle the historical data API differently
        
        # Return a sample DataFrame for demonstration
        return pd.DataFrame([{
            'city': 'Sample City',
            'country': 'Sample Country',
            'temperature': 20.5,
            'humidity': 65,
            'timestamp': datetime.now()
        }])

def fetch_weather_data(endpoint: str, params: Optional[Dict] = None, credentials: Optional[Dict] = None) -> pd.DataFrame:
    """
    Fetch weather data from the appropriate API
    
    Args:
        endpoint (str): The endpoint to query
        params (Dict, optional): Parameters for the API request
        credentials (Dict, optional): API credentials
        
    Returns:
        pd.DataFrame: DataFrame containing the weather data
    """
    if not credentials or 'api_key' not in credentials:
        raise ValueError("API key is required for weather data")
    
    # Use OpenWeatherMap connector
    connector = OpenWeatherMapConnector(credentials)
    return connector.fetch_data(endpoint, params) 