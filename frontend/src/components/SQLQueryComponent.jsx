import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, TextField, Button, Typography, Paper, 
  CircularProgress, Alert, FormControl, InputLabel,
  Select, MenuItem, Grid
} from '@mui/material';
import { convertNaturalLanguageToSql } from '../api/chatApi';
import { DataGrid } from '@mui/x-data-grid';
import SQLServerConnectionSelector from './SQLServerConnectionSelector';

/**
 * Component for converting natural language to SQL and executing queries
 */
function SQLQueryComponent() {
  const [query, setQuery] = useState('');
  const [sqlQuery, setSqlQuery] = useState('');
  const [explanation, setExplanation] = useState('');
  const [results, setResults] = useState([]);
  const [columns, setColumns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedConnection, setSelectedConnection] = useState(null);
  const [savedConnections, setSavedConnections] = useState([]);
  const [connectionId, setConnectionId] = useState('');
  const [apiResponse, setApiResponse] = useState(null);
  
  const inputRef = useRef(null);
  
  // Load saved connections on component mount
  useEffect(() => {
    loadSavedConnections();
  }, []);
  
  // Load saved SQL server connections from localStorage
  const loadSavedConnections = () => {
    try {
      // Try to get from localStorage first
      const connections = localStorage.getItem('sqlServerConnections');
      if (connections) {
        const parsedConnections = JSON.parse(connections);
        setSavedConnections(parsedConnections);
        
        // If we have connections and none is selected, select the first one
        if (parsedConnections.length > 0 && !selectedConnection) {
          setSelectedConnection(parsedConnections[0]);
          setConnectionId(`sql_1`); // Select first connection by default
        }
      } else {
        // If not in localStorage, try to fetch from server API
        fetch('/api/external-data/configured-sources')
          .then(response => response.json())
          .then(data => {
            if (data.success && data.sources && data.sources.length > 0) {
              const sqlSources = data.sources.filter(source => source.type === 'sql_server');
              setSavedConnections(sqlSources);
              
              // Select first connection by default
              if (sqlSources.length > 0 && !selectedConnection) {
                setSelectedConnection(sqlSources[0]);
                setConnectionId(sqlSources[0].id); // Use the ID provided from the server
              }
            }
          })
          .catch(err => {
            console.error('Error loading SQL server connections:', err);
          });
      }
    } catch (error) {
      console.error('Error loading saved connections:', error);
    }
  };
  
  // Handle connection selection change
  const handleConnectionChange = (event) => {
    const connId = event.target.value;
    setConnectionId(connId);
    
    // Find the selected connection details
    const connection = savedConnections.find(conn => conn.id === connId);
    if (connection) {
      setSelectedConnection(connection);
    }
  };
  
  // Handle query input change
  const handleQueryChange = (event) => {
    setQuery(event.target.value);
  };
  
  // Handle form submission
  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }
    
    if (!selectedConnection && !connectionId) {
      setError('Please select a database connection');
      return;
    }
    
    setLoading(true);
    setError('');
    setSqlQuery('');
    setExplanation('');
    setResults([]);
    
    // Check for client-specific query for enhanced debugging
    const isClientsQuery = query.toLowerCase().includes('client');
    if (isClientsQuery) {
      console.log('Client query detected, enabling enhanced diagnostics');
    }
    
    try {
      let response;
      
      // If we have a connectionId, use that instead of passing credentials
      if (connectionId) {
        console.log(`Using connection ID: ${connectionId} for query: "${query}"`);
        response = await convertNaturalLanguageToSql(
          query,
          null,  // No credentials needed
          connectionId, 
          [], // No specific tables, let the server get the schema
          [], // No conversation history
          true // Execute the query
        );
      } else {
        // Fallback to using connection details directly
        console.log('Using direct connection credentials for query');
        response = await convertNaturalLanguageToSql(
          query,
          selectedConnection.config, 
          null, // No connectionId
          [], // No specific tables
          [], // No conversation history
          true // Execute the query
        );
      }
      
      // Handle the response
      if (response.sql) {
        setSqlQuery(response.sql);
        setExplanation(response.explanation || '');
        
        // Store full response in state
        setApiResponse(response);
        
        // Log complete response for debugging
        console.log('Complete SQL query response:', JSON.stringify(response, null, 2));
        
        // For clients query, do a direct diagnostic check
        if (isClientsQuery && (!response.result || response.result.length === 0)) {
          console.warn('Client query returned no results, trying alternative approach...');
          
          // Add a "retry" message
          setError('No client records returned. This could be due to permissions or data access issues. Checking connection...');
          
          // Try to get detailed error info
          if (response.error) {
            console.error('Error detected in response:', response.error);
            setError(`Error: ${response.error}`);
          }
        }
        
        // Setup DataGrid columns and rows
        if (response.result && response.result.length > 0) {
          console.log('Processing results for display, count:', response.result.length);
          
          // Handle special case for Clients table
          const isClientsQuery = response.sql.toLowerCase().includes('from clients');
          if (isClientsQuery) {
            console.log('Detected Clients table query, ensuring proper display');
          }
          
          let resultData = response.result;
          
          // Convert data to DataGrid format
          const firstRow = resultData[0];
          console.log('First row for column extraction:', firstRow);
          
          // Use column_names from response if available, otherwise extract from first row
          let columnFields = [];
          if (response.column_names && response.column_names.length > 0) {
            console.log('Using column_names from response:', response.column_names);
            columnFields = response.column_names;
          } else {
            columnFields = Object.keys(firstRow);
          }
          
          const gridColumns = columnFields.map(key => ({
            field: key,
            headerName: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' '),
            flex: 1,
            minWidth: 150
          }));
          
          console.log('Generated grid columns:', gridColumns);
          
          // Add id to rows if not present
          const gridRows = resultData.map((row, index) => {
            // Ensure row has an id
            const rowWithId = {
              id: row.id || row.ID || row.Id || row.ClientID || row.client_id || index,
              ...row
            };
            
            // For clients table, ensure all expected columns are present
            if (isClientsQuery) {
              // Add any missing display columns with empty values
              const clientColumns = ['ClientID', 'ClientName', 'ContactPerson', 'Email', 'Phone', 'CreatedDate'];
              clientColumns.forEach(col => {
                if (rowWithId[col] === undefined) {
                  rowWithId[col] = '';
                }
              });
            }
            
            return rowWithId;
          });
          
          console.log('Prepared grid rows sample:', gridRows.slice(0, 2));
          
          setColumns(gridColumns);
          setResults(gridRows);
        } else {
          setResults([]);
          if (response.sql.toLowerCase().includes('from clients')) {
            console.warn('Clients query returned no results when data should exist');
            setError('Client query executed but returned no results. This may indicate a data access issue or database permission problem. Check the database connection and permissions.');
          } else if (response.execution_status === 'no_results') {
            setError('Query executed successfully but returned no results');
          }
        }
      } else {
        setError('No SQL query generated. Please try again with a different question.');
      }
    } catch (err) {
      console.error('Error executing query:', err);
      
      // Enhanced error handling for client queries
      if (isClientsQuery) {
        console.error('Client query failed with error:', err.message);
        setError(`Error querying clients: ${err.message}. This may be due to database connection issues or permissions.`);
      } else {
        setError(err.message || 'Error executing query');
      }
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Box sx={{ p: 3, maxWidth: '100%' }}>
      <Typography variant="h5" gutterBottom>
        SQL Query Assistant
      </Typography>
      
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Ask a question about your data"
                variant="outlined"
                value={query}
                onChange={handleQueryChange}
                placeholder="e.g., Show me all clients" 
                inputRef={inputRef}
                helperText="Ask in natural language and I'll convert it to SQL"
                sx={{ mb: 2 }}
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel id="connection-select-label">Database Connection</InputLabel>
                <Select
                  labelId="connection-select-label"
                  value={connectionId}
                  onChange={handleConnectionChange}
                  label="Database Connection"
                >
                  {savedConnections.map((conn, index) => (
                    <MenuItem key={conn.id || `conn_${index}`} value={conn.id || `sql_${index+1}`}>
                      {conn.name || `${conn.config?.server}/${conn.config?.database}`}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <Button 
                type="submit" 
                variant="contained" 
                color="primary" 
                disabled={loading}
                sx={{ mt: 1 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Convert & Execute'}
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
          {error.includes('405') && (
            <Box mt={1}>
              <Typography variant="body2" color="error" fontWeight="bold">
                405 Method Not Allowed Error Detected
              </Typography>
              <Typography variant="body2">
                The API endpoint doesn't accept the request method. The app will automatically try alternative endpoints.
                Please try your query again after the page refreshes.
              </Typography>
              <Button 
                variant="outlined" 
                color="error" 
                size="small" 
                onClick={() => {
                  // Clear stored endpoint to force retry
                  localStorage.removeItem('successful_sql_endpoint');
                  window.location.reload();
                }}
                sx={{ mt: 1 }}
              >
                Reset Endpoint & Refresh
              </Button>
            </Box>
          )}
        </Alert>
      )}
      
      {sqlQuery && (
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Generated SQL
          </Typography>
          <Box sx={{ 
            bgcolor: 'background.paper', 
            p: 2, 
            border: '1px solid #e0e0e0',
            borderRadius: 1,
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap',
            overflowX: 'auto'
          }}>
            {sqlQuery}
          </Box>
          
          {explanation && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle1">Explanation:</Typography>
              <Typography variant="body2">{explanation}</Typography>
            </Box>
          )}
          
          {apiResponse && apiResponse.diagnostic_mode && (
            <Box sx={{ mt: 2, p: 1, border: '1px dashed #ffa726', borderRadius: 1, bgcolor: '#fff8e1' }}>
              <Typography variant="subtitle1" color="warning.main">Diagnostic Mode Active</Typography>
              <Typography variant="body2">
                {apiResponse.diagnostic_message || 'The system used direct database access to retrieve data because the regular query flow returned no results.'}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                This may indicate permission issues with the regular query flow or other database access problems.
              </Typography>
            </Box>
          )}
        </Paper>
      )}
      
      {results.length > 0 && (
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Results ({results.length} rows)
          </Typography>
          <Box sx={{ height: 400, width: '100%' }}>
            <DataGrid
              rows={results}
              columns={columns}
              pageSize={10}
              rowsPerPageOptions={[5, 10, 25, 50]}
              disableSelectionOnClick
              density="compact"
            />
          </Box>
        </Paper>
      )}
    </Box>
  );
}

export default SQLQueryComponent; 