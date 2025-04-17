import axios from 'axios';

// Get API base URL from environment or use a default
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';
const API_ROOT_URL = API_BASE_URL.replace('/api', '');

// Create an axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 30000, // 30 second timeout
  withCredentials: true // Enable CORS credentials
});

// Add request interceptor for error handling
api.interceptors.request.use(
  (config) => {
    // Log the request URL for debugging
    console.log(`Making ${config.method?.toUpperCase()} request to: ${config.baseURL}${config.url}`);
    
    // Special handling for SQL conversion endpoint
    if (config.url === '/convert_nl_to_sql') {
      console.log('Detected SQL conversion request, ensuring correct endpoint');
      
      // Try several endpoint variations since the server might be expecting a specific format
      // Option 1: Use the root URL with convert_nl_to_sql (original behavior)
      config.baseURL = API_ROOT_URL;
      
      // Try these endpoints in order until one works (will be tracked in browser console)
      // We'll use the one that works first
      if (localStorage.getItem('successful_sql_endpoint')) {
        // Use the endpoint that worked previously
        const successful_endpoint = localStorage.getItem('successful_sql_endpoint');
        console.log(`Using previously successful endpoint: ${successful_endpoint}`);
        config.url = successful_endpoint;
      } else {
        console.log('Testing various endpoint formats to find one that works');
        // First try with /api prefix
        config.url = '/api/convert_nl_to_sql';
      }
      
      console.log(`Adjusted endpoint: ${config.baseURL}${config.url}`);
    }
    
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
    // For SQL conversion responses, add extra debugging
    if (response.config.url.includes('convert_nl_to_sql')) {
      console.log('SQL conversion response received:', response.status);
      // Check for empty result sets
      if (response.data && response.data.result) {
        const result = response.data.result || {};
        if (result.result && Array.isArray(result.result)) {
          console.log(`SQL result contains ${result.result.length} rows`);
          if (result.result.length > 0) {
            console.log('First row sample:', result.result[0]);
          } else {
            console.warn('SQL query returned zero rows - this may indicate a data access issue or empty table');
          }
        } else if (response.data.result && Array.isArray(response.data.result)) {
          console.log(`SQL result contains ${response.data.result.length} rows`);
          if (response.data.result.length > 0) {
            console.log('First row sample:', response.data.result[0]);
          } else {
            console.warn('SQL query returned zero rows - this may indicate a data access issue or empty table');
          }
        } else {
          console.warn('SQL result structure does not contain expected rows array');
          console.log('Full response data structure:', JSON.stringify(response.data, null, 2));
        }
      }
    }
    return response;
  },
  (error) => {
    if (error.response) {
      // Server responded with error
      console.error('Server error:', error.response.data);
      console.error('Status:', error.response.status);
      console.error('Headers:', error.response.headers);
      
      // Enhanced debugging for SQL conversion errors
      if (error.config && error.config.url && error.config.url.includes('convert_nl_to_sql')) {
        console.error('SQL conversion request failed:');
        console.error('Request URL:', error.config.url);
        console.error('Request data:', error.config.data);
        
        // Try to parse the request data for more context
        try {
          const requestData = JSON.parse(error.config.data);
          console.error('SQL query request details:', {
            query: requestData.query,
            connectionId: requestData.connection_id || 'Not provided',
            execute: requestData.execute
          });
        } catch (e) {
          console.error('Could not parse request data');
        }
      }
    } else if (error.request) {
      // Request made but no response
      console.error('Network error:', error.request);
      
      // Check if this is for SQL conversion
      if (error.config && error.config.url && error.config.url.includes('convert_nl_to_sql')) {
        console.error('SQL conversion network error - server might be unavailable');
      }
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
    const response = await api.post('/chat', {
      message,
      conversationId,
      datasetName,
      modelId,
      useCache,
      userId: localStorage.getItem('userId') || 'anonymous',
      includeVisualization: true,
      requestFormat: 'json'
    });
    
    const data = response.data;
    
    if (data.visualization) {
      try {
        if (typeof data.visualization === 'string') {
          data.visualization = JSON.parse(data.visualization);
        }
        
        if (!data.visualization.type && !data.visualization.data && !data.visualization.fig) {
          console.warn('Visualization data is missing required properties');
          
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
      timeout: 60000
    });
    
    console.log('Upload successful:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error in uploadFile function:', error);
    throw error;
  }
};

/**
 * Get available datasets
 * @returns {Promise<Object>} - Available datasets with metadata
 */
export const getDatasets = async () => {
  try {
    console.log('Fetching available datasets from API...');
    const response = await api.get('/datasets');
    const data = response.data;
    
    if (!data || typeof data !== 'object') {
      console.error('Invalid datasets response format:', data);
      return getHardcodedDatasets();
    }
    
    const processedData = {};
    Object.entries(data).forEach(([id, dataset]) => {
      processedData[id] = {
        name: dataset.name || id,
        description: dataset.description || '',
        rows: parseInt(dataset.rows || dataset.rowCount || dataset.row_count || 0, 10) || null
      };
    });
    
    if (!processedData.msft || !processedData.sales_data) {
      console.warn('Missing expected datasets, using hardcoded backup');
      return getHardcodedDatasets();
    }
    
    return processedData;
  } catch (error) {
    console.error('Error fetching datasets:', error);
    return getHardcodedDatasets();
  }
};

// Hardcoded datasets as backup when API fails
function getHardcodedDatasets() {
  return {
    msft: {
      name: 'MSFT',
      description: 'Microsoft financial data',
      rows: null
    },
    sales_data: {
      name: 'Sales Data',
      description: 'Product sales across regions and time periods',
      rows: null
    }
  };
}

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
    
    const response = await api.get('/status', {
      timeout: 5000,
      validateStatus: function (status) {
        return status < 500;
      }
    });
    
    const endTime = performance.now();
    console.log(`API status check completed in ${endTime - startTime}ms`);
    console.log('API status response:', response.data);
    
    return {
      ...response.data,
      responseTime: endTime - startTime
    };
  } catch (error) {
    console.error('Error checking API status:', error);
    
    if (error.code === 'ECONNABORTED') {
      throw new Error('Connection timeout - server may be down or unreachable');
    } else if (error.response) {
      throw new Error(`Server error: ${error.response.status} - ${error.response.data?.message || 'Unknown error'}`);
    } else if (error.request) {
      throw new Error('No response from server - check if the API server is running and accessible');
    } else {
      throw new Error(`Request failed: ${error.message}`);
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
  
  api.get('/status')
    .then(response => {
      console.log('API Status Response:', response);
      console.log('API Status Data:', response.data);
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

/**
 * Convert natural language to SQL query and execute it
 * @param {string} query - Natural language query to convert
 * @param {Object|null} credentials - Connection credentials (optional if connectionId provided)
 * @param {string|null} connectionId - ID of a saved connection to use (optional if credentials provided) 
 * @param {Array} tables - Array of table names to include in context
 * @param {Array} conversationHistory - Previous conversation messages for context
 * @param {boolean} execute - Whether to execute the generated SQL
 * @param {number} limit - Maximum number of results to return
 * @returns {Promise<Object>} - SQL query and results
 */
export const convertNaturalLanguageToSql = async (
  query, 
  credentials = null,
  connectionId = null,
  tables = [], 
  conversationHistory = [], 
  execute = true, 
  limit = 1000
) => {
  try {
    console.log('Converting natural language to SQL:', query);
    
    const payload = {
      query,
      conversation_history: conversationHistory,
      execute,
      limit
    };
    
    // Validate that connectionId is a string, not an array of tables
    if (connectionId && typeof connectionId === 'string') {
      console.log(`Using saved connection with ID: ${connectionId}`);
      payload.connection_id = connectionId;
    } else if (credentials) {
      console.log('Using provided credentials');
      payload.connection_params = {
        server: credentials.server,
        database: credentials.database,
        trusted_connection: credentials.trusted_connection || 'yes',
        username: credentials.username,
        password: credentials.password,
        driver: credentials.driver
      };
    } else {
      // If no valid connectionId or credentials, use default connection
      console.log('Using default connection');
      payload.connection_id = 'default';
    }
    
    // Always include tables in the database context
    let databaseContext = { tables: Array.isArray(tables) ? tables : [] };
    
    try {
      const storedDDL = localStorage.getItem('sqlDatabaseDDL');
      if (storedDDL) {
        const ddlObj = JSON.parse(storedDDL);
        if (ddlObj && ddlObj.tables) {
          console.log('Using stored database DDL for improved SQL generation');
          // Merge the stored DDL tables with the provided tables
          databaseContext = {
            ...ddlObj,
            tables: [...new Set([...(Array.isArray(ddlObj.tables) ? ddlObj.tables : []), ...databaseContext.tables])]
          };
        }
      }
    } catch (e) {
      console.warn('Error using stored DDL:', e);
    }
    
    payload.schema_info = databaseContext;
    
    console.log('Sending payload:', payload);
    
    // Try the default endpoint first (will use the endpoint from the interceptor)
    try {
    const response = await api.post('/convert_nl_to_sql', payload);
      console.log('SQL conversion successful!');
      
      // If successful, store the endpoint that worked for future use
      if (!localStorage.getItem('successful_sql_endpoint')) {
        localStorage.setItem('successful_sql_endpoint', '/api/convert_nl_to_sql');
      }
      
      console.log('Raw API response:', response);
    const responseData = response.data;
      
      // Rest of processing continues as normal
      console.log('Response data structure:', JSON.stringify(responseData, null, 2));
      
    const result = responseData.result || {};
      console.log('Result structure:', JSON.stringify(result, null, 2));
    
    if (responseData.error || result.error) {
      const errorMsg = responseData.error || result.error || 'Failed to convert natural language to SQL';
      console.error('SQL conversion error:', errorMsg);
      throw new Error(errorMsg);
    }
    
    const data = {
      success: !responseData.error && (result.success !== false),
      // Handle both old and new API response formats
      sql: result.sql || result.sql_query || '',
      explanation: result.explanation || '',
      // Set high confidence when results exist, even if the API returns 0
      confidence: (result.result || result.results || []).length > 0 ? 
        Math.max(parseFloat(result.confidence) || 0, 0.9) : // At least 90% confident when results exist
        parseFloat(result.confidence) || 0,
      result: result.result || result.results || [],
      column_names: result.columns || result.column_names || [],
      row_count: result.row_count || (result.result ? result.result.length : 0),
      execution_status: result.execution_status || '',
      reflection_applied: result.reflection_applied || false,
      diagnostic_mode: result.diagnostic_mode || false,
      diagnostic_message: result.diagnostic_message || ''
    };
      
    console.log('Processed data structure before column mapping:', JSON.stringify(data, null, 2));
    console.log('Result array type check:', Array.isArray(data.result));
    console.log('Result first item type:', data.result.length > 0 ? typeof data.result[0] : 'empty array');
    console.log('Is diagnostic mode:', data.diagnostic_mode);
    
    // Store column names for potential array-to-object conversion
    if (data.column_names && data.column_names.length > 0) {
      console.log('Storing column names for clients table:', data.column_names);
      localStorage.setItem('clientColumnNames', JSON.stringify(data.column_names));
    }
    
    if (data.result && data.result.length > 0 && 
        (data.sql.toLowerCase().includes('from clients') || data.diagnostic_mode)) {
      console.log('Processing client data with proper column mapping');
      console.log('Original first result:', JSON.stringify(data.result[0]));
      data.result = data.result.map(row => mapClientColumns(row));
      console.log('Mapped first result:', JSON.stringify(data.result[0]));
    } else if (data.result && data.result.length === 0 && 
               data.sql.toLowerCase().includes('from clients')) {
      console.warn('Client query returned zero results even though data should exist');
    }
    
    return data;
    } catch (error) {
      // If we got a 405 Method Not Allowed error, try alternative endpoints
      if (error.response && error.response.status === 405) {
        console.warn('Got 405 Method Not Allowed, trying alternative endpoints...');
        
        // Try direct endpoint without /api prefix
        try {
          console.log('Trying endpoint without /api prefix');
          // Create a new axios instance for direct calls to avoid interceptor
          const directApi = axios.create({
            baseURL: API_ROOT_URL,
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json'
            }
          });
          
          let altResponse;
          try {
            // Try option 1: direct without prefix
            altResponse = await directApi.post('/convert_nl_to_sql', payload);
            console.log('Direct endpoint worked!');
            localStorage.setItem('successful_sql_endpoint', '/convert_nl_to_sql');
          } catch (err1) {
            console.warn('First alternative failed, trying second option...');
            
            try {
              // Try option 2: nl-to-sql endpoint (some servers use kebab-case)
              altResponse = await directApi.post('/nl-to-sql', payload);
              console.log('nl-to-sql endpoint worked!');
              localStorage.setItem('successful_sql_endpoint', '/nl-to-sql');
            } catch (err2) {
              console.warn('Second alternative failed, trying third option...');
              
              // Try option 3: direct API call to Flask's route
              altResponse = await directApi.post('/api/nl-to-sql', payload);
              console.log('/api/nl-to-sql endpoint worked!');
              localStorage.setItem('successful_sql_endpoint', '/api/nl-to-sql');
            }
          }
          
          // Process the response and return data (same as above)
          const responseData = altResponse.data;
          console.log('Response data structure:', JSON.stringify(responseData, null, 2));
          
          const result = responseData.result || {};
          
          if (responseData.error || result.error) {
            const errorMsg = responseData.error || result.error || 'Failed to convert natural language to SQL';
            console.error('SQL conversion error:', errorMsg);
            throw new Error(errorMsg);
          }
          
          const data = {
            success: !responseData.error && (result.success !== false),
            sql: result.sql || result.sql_query || '',
            explanation: result.explanation || '',
            // Set high confidence when results exist, even if the API returns 0
            confidence: (result.result || result.results || []).length > 0 ? 
              Math.max(parseFloat(result.confidence) || 0, 0.9) : // At least 90% confident when results exist
              parseFloat(result.confidence) || 0,
            result: result.result || result.results || [],
            column_names: result.columns || result.column_names || [],
            row_count: result.row_count || (result.result ? result.result.length : 0),
            execution_status: result.execution_status || '',
            reflection_applied: result.reflection_applied || false,
            diagnostic_mode: result.diagnostic_mode || false,
            diagnostic_message: result.diagnostic_message || ''
          };
          
          if (data.result && data.result.length > 0 && 
              data.sql && data.sql.toLowerCase().includes('from clients')) {
            data.result = data.result.map(row => mapClientColumns(row));
          }
          
          return data;
        } catch (altError) {
          console.error('Alternative endpoint also failed:', altError);
          // Let the original error propagate
          throw error;
        }
      } else {
        // For errors other than 405, throw the original error
        throw error;
      }
    }
  } catch (error) {
    console.error('Error converting natural language to SQL:', error);
    throw error;
  }
};

// Utility function to map database column names to frontend expected properties
const mapClientColumns = (row) => {
  if (!row) {
    console.error('Empty row passed to mapClientColumns');
    return null;
  }
  
  console.log('mapClientColumns input:', JSON.stringify(row));
  
  if (Array.isArray(row)) {
    console.log('Processing array of rows in mapClientColumns, length:', row.length);
    return row.map(item => mapClientColumns(item));
  }
  
  // Debug keys available in the row
  console.log('Available keys in client row:', Object.keys(row));
  
  // Check for column format issues
  if (Object.keys(row).length === 0) {
    console.error('Row has no properties!');
    return row;
  }
  
  // Handle potential array vs. object structure issues
  if (row[0] !== undefined && typeof row[0] !== 'object') {
    console.warn('Row appears to be an array-like structure:', row);
    // Try to convert array format to object using column names
    const columnsFromStorage = localStorage.getItem('clientColumnNames');
    if (columnsFromStorage) {
      try {
        const columnNames = JSON.parse(columnsFromStorage);
        if (Array.isArray(columnNames) && columnNames.length === Object.keys(row).length) {
          console.log('Attempting to convert array-format row to object using stored column names');
          const objectRow = {};
          columnNames.forEach((colName, index) => {
            objectRow[colName] = row[index];
          });
          row = objectRow;
        }
      } catch (e) {
        console.error('Error parsing stored column names:', e);
      }
    }
  }
  
  const mappedRow = {
    ClientID: row.client_id || row.ClientID || row.clientid || row.client_no || '',
    ClientName: row.first_name && row.last_name 
      ? `${row.first_name} ${row.last_name}` 
      : (row.ClientName || row.client_name || row.name || ''),
    ContactPerson: row.first_name && row.last_name 
      ? `${row.first_name} ${row.last_name}` 
      : (row.ContactPerson || row.contact_person || row.contact || ''),
    Email: row.email || row.Email || row.email_address || '',
    Phone: row.phone || row.Phone || row.phone_number || row.telephone || '',
    CreatedDate: row.created_date || row.CreatedDate || row.date_created || '',
    ...row  // Keep original properties as well
  };
  
  console.log('Mapped row result:', JSON.stringify(mappedRow));
  return mappedRow;
};

// Utility function to map database column names to frontend display names
const mapDatabaseColumns = (data, schema) => {
  if (!data || !schema) return data;
  
  if (Array.isArray(data)) {
    return data.map(record => mapDatabaseColumns(record, schema));
  }
  
  const getTableFromSQL = (sql) => {
    if (!sql) return null;
    const match = sql.toLowerCase().match(/from\s+([^\s,;()]+)/i);
    return match ? match[1] : null;
  };
  
  const getColumnMapping = (tableName) => {
    if (!schema.tables || !tableName) return null;
    
    const tableInfo = typeof schema.tables === 'object' ? 
      schema.tables[tableName] : 
      (Array.isArray(schema.tables) ? 
        schema.tables.find(t => t.name === tableName) : null);
    
    if (!tableInfo) return null;
    
    const columns = Array.isArray(tableInfo) ? tableInfo : tableInfo.columns;
    if (!columns) return null;
    
    return columns.reduce((mapping, col) => {
      const displayName = col.display_name || 
        col.column_name.split('_')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join('');
      
      mapping[col.column_name] = displayName;
      return mapping;
    }, {});
  };
  
  const tableName = getTableFromSQL(data.sql);
  const columnMapping = getColumnMapping(tableName);
  
  if (!columnMapping) return data;
  
  const mappedData = {};
  Object.entries(data).forEach(([key, value]) => {
    mappedData[key] = value;
    if (columnMapping[key]) {
      mappedData[columnMapping[key]] = value;
    }
  });
  
  return mappedData;
};

// Modify the function that processes SQL results to use the mapping
const processSQLResults = (data) => {
  // ... existing code ...
  
  // If this is a Clients table query, map the columns
  if (data.sql && data.sql.toLowerCase().includes('from clients') && data.result) {
    data.result = mapClientColumns(data.result);
  }
  
  return data;
};

// Find where the API response is processed and add the mapping logic

const processResponse = (response) => {
  try {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return response.json().then(data => {
        // Apply column mapping if this is a SQL query result
        if (data.sql && data.result && data.schema_info) {
          data.result = mapDatabaseColumns(data.result, data.schema_info);
        }
        return data;
      });
    } else {
      return response.text();
    }
  } catch (error) {
    console.error("Error processing response:", error);
    throw error;
  }
};

// Create the API object with all exported functions
const apiObject = {
  sendMessage,
  getConversationHistory,
  getConversationMessages,
  uploadFile,
  getDatasets,
  getDebugState,
  checkApiStatus,
  debugApiConnection,
  convertNaturalLanguageToSql
};

// Export the API object as default
export default apiObject;
