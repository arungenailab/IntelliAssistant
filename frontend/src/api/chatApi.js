import axios from 'axios';

// Get API base URL from environment or use a default
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

// Create an axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000, // 30 second timeout
  withCredentials: true // Enable CORS credentials
});

// Add request interceptor for error handling
api.interceptors.request.use(
  (config) => {
    // Add any request preprocessing here
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // Server responded with error
      console.error('Server error:', error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('Network error:', error.request);
    } else {
      // Other errors
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Export the base URL for use in other components
export const getApiBaseUrl = () => {
  // Make sure the URL doesn't have a trailing slash
  const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
  console.log('API Base URL:', baseUrl);
  return baseUrl;
};

/**
 * Send a message to the chat API
 * @param {string} message - The message text
 * @param {string|null} conversationId - Optional conversation ID for continuing a conversation
 * @param {string|null} datasetName - Optional dataset name to analyze
 * @param {string|null} modelId - Optional model ID to use for processing
 * @param {boolean} useCache - Whether to use cached responses
 * @returns {Promise<Object>} - Response with message and visualization data
 */
export const sendMessage = async (
  message, 
  conversationId = null, 
  datasetName = null, 
  modelId = 'gemini-2.0-flash',
  useCache = true
) => {
  try {
    // Call the actual backend API
    const response = await api.post('/chat', {
      message,
      conversationId,
      datasetName,
      modelId,
      useCache,
      userId: localStorage.getItem('userId') || 'anonymous',
      includeVisualization: true,  // Explicitly request visualization data
      requestFormat: 'json'  // Request JSON format for easier parsing
    });
    
    // Process the response
    const data = response.data;
    
    // Validate visualization data if present
    if (data.visualization) {
      try {
        // If visualization is a string, try to parse it as JSON
        if (typeof data.visualization === 'string') {
          data.visualization = JSON.parse(data.visualization);
        }
        
        // Ensure visualization has required properties
        if (!data.visualization.type && !data.visualization.data && !data.visualization.fig) {
          console.warn('Visualization data is missing required properties');
          
          // Try to extract visualization type from the response text
          if (data.text && data.text.includes('visualization')) {
            const visTypes = ['bar', 'line', 'scatter', 'pie', 'histogram', 'box'];
            for (const type of visTypes) {
              if (data.text.toLowerCase().includes(type + ' chart') || 
                  data.text.toLowerCase().includes(type + ' graph') ||
                  data.text.toLowerCase().includes(type + ' plot')) {
                data.visualization.type = type;
                break;
              }
            }
          }
        }
      } catch (error) {
        console.error('Error processing visualization data:', error);
        data.visualization = null;
      }
    }
    
    return data;
  } catch (error) {
    console.error('Error sending message:', error);
    
    // Return a structured error response
    return {
      text: 'Sorry, I encountered an error processing your request. Please try again.',
      error: error.message,
      visualization: null
    };
  }
};

/**
 * Get conversation history
 * @returns {Promise<Array>} - List of conversations
 */
export const getConversationHistory = async () => {
  try {
    const response = await api.get('/conversations');
    return response.data;
  } catch (error) {
    console.error('Error getting conversation history:', error);
    throw error;
  }
};

/**
 * Get messages for a specific conversation
 * @param {string} conversationId - The conversation ID
 * @returns {Promise<Array>} - List of messages in the conversation
 */
export const getConversationMessages = async (conversationId) => {
  try {
    const response = await api.get(`/conversations/${conversationId}/messages`);
    return response.data;
  } catch (error) {
    console.error('Error getting conversation messages:', error);
    throw error;
  }
};

/**
 * Upload a data file
 * @param {FormData} formData - The FormData object containing the file and metadata
 * @returns {Promise<Object>} - Response with dataset information
 */
export const uploadFile = async (formData) => {
  try {
    console.log('Sending upload request to server');
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 60000 // Increase timeout for large files
    });
    
    console.log('Upload successful:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error in uploadFile function:', error);
    
    // Log detailed error information
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('Error response data:', error.response.data);
      console.error('Error response status:', error.response.status);
      console.error('Error response headers:', error.response.headers);
    } else if (error.request) {
      // The request was made but no response was received
      console.error('Error request:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('Error message:', error.message);
    }
    
    throw error;
  }
};

/**
 * Get available datasets
 * @returns {Promise<Object>} - Available datasets with metadata
 */
export const getDatasets = async () => {
  try {
    console.log('getDatasets: Sending request to /api/datasets');
    const startTime = performance.now();
    
    // Attempt to use fetch API as an alternative to axios
    try {
      console.log('Trying alternative fetch method...');
      const fetchResponse = await fetch('http://localhost:5000/api/datasets', {
        method: 'GET',
        credentials: 'include', // Important for CORS with cookies
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (fetchResponse.ok) {
        const fetchData = await fetchResponse.json();
        console.log('Fetch API successful:', fetchData);
        const endTime = performance.now();
        console.log(`getDatasets: Fetch request completed in ${endTime - startTime}ms`);
        return fetchData;
      } else {
        console.error('Fetch API failed with status:', fetchResponse.status);
      }
    } catch (fetchError) {
      console.error('Fetch API error:', fetchError);
    }
    
    // Fallback to axios
    console.log('Falling back to axios request');
    const response = await api.get('/datasets');
    const endTime = performance.now();
    console.log(`getDatasets: Axios request completed in ${endTime - startTime}ms`);
    console.log('getDatasets: Response received:', response.data);
    
    // Validate the response data
    if (!response.data || typeof response.data !== 'object') {
      console.error('getDatasets: Invalid response data format:', response.data);
      throw new Error('Invalid response data format');
    }
    
    // Check if the response is empty
    if (Object.keys(response.data).length === 0) {
      console.warn('getDatasets: No datasets found in response');
    }
    
    return response.data;
  } catch (error) {
    console.error('Error getting datasets:', error);
    
    // Log more detailed error information
    if (error.response) {
      console.error('Error response status:', error.response.status);
      console.error('Error response headers:', error.response.headers);
      console.error('Error response data:', error.response.data);
    } else if (error.request) {
      console.error('No response received (request details):', error.request);
    }
    
    // Rethrow to be handled by the component
    throw error;
  }
};

/**
 * Get application debug state
 * @returns {Promise<Object>} - Current application state
 */
export const getDebugState = async () => {
  try {
    const response = await api.get('/debug/state');
    return response.data;
  } catch (error) {
    console.error('Error getting debug state:', error);
    throw error;
  }
};

/**
 * Check the API server status
 * @returns {Promise<Object>} - API server status
 */
export const checkApiStatus = async () => {
  try {
    console.log('Checking API server status...');
    console.log('API Base URL:', API_BASE_URL);
    const startTime = performance.now();
    
    // Use a direct fetch with a short timeout to quickly detect connection issues
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    const response = await fetch(`${API_BASE_URL.replace('/api', '')}/api/status`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`Server responded with status: ${response.status}`);
    }
    
    const data = await response.json();
    const endTime = performance.now();
    console.log(`API status check completed in ${endTime - startTime}ms`);
    console.log('API status response:', data);
    
    return {
      ...data,
      responseTime: endTime - startTime
    };
  } catch (error) {
    console.error('Error checking API status:', error);
    
    // Provide more specific error messages based on the error type
    if (error.name === 'AbortError') {
      throw new Error('Connection timeout - server may be down or unreachable');
    } else if (error.message.includes('Failed to fetch')) {
      throw new Error('Failed to fetch - check if the API server is running and accessible');
    } else {
      throw error;
    }
  }
};

/**
 * Debug function to log API connection details
 * This is useful for troubleshooting connection issues
 */
export const debugApiConnection = () => {
  console.group('API Connection Debug Info');
  console.log('API Base URL:', API_BASE_URL);
  console.log('Environment Variables:', process.env);
  console.log('Current Origin:', window.location.origin);
  console.log('Current URL:', window.location.href);
  
  // Check if the API server is accessible with a simple fetch
  fetch(`${API_BASE_URL.replace('/api', '')}/api/status`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
  })
    .then(response => {
      console.log('API Status Response:', response);
      return response.json();
    })
    .then(data => {
      console.log('API Status Data:', data);
    })
    .catch(error => {
      console.error('API Status Error:', error);
    })
    .finally(() => {
      console.groupEnd();
    });
  
  return {
    apiBaseUrl: API_BASE_URL,
    origin: window.location.origin,
    url: window.location.href,
    env: process.env
  };
};

export default {
  sendMessage,
  getConversationHistory,
  getConversationMessages,
  uploadFile,
  getDatasets,
  getDebugState,
  checkApiStatus,
  debugApiConnection
};
