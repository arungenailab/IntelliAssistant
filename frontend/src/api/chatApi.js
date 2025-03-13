import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
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

/**
 * Send a message to the chat API
 * @param {string} message - The message text
 * @param {string|null} conversationId - Optional conversation ID for continuing a conversation
 * @param {string|null} datasetName - Optional dataset name to analyze
 * @returns {Promise<Object>} - Response with message and visualization data
 */
export const sendMessage = async (message, conversationId = null, datasetName = null) => {
  try {
    // Call the actual backend API
    const response = await api.post('/chat', {
      message,
      conversationId,
      datasetName,
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
    const response = await api.get('/datasets');
    return response.data;
  } catch (error) {
    console.error('Error getting datasets:', error);
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

export default {
  sendMessage,
  getConversationHistory,
  getConversationMessages,
  uploadFile,
  getDatasets,
  getDebugState
};
