import React, { useState } from 'react';
import { 
  Button, 
  Card, 
  CardContent, 
  CardHeader, 
  Typography, 
  TextField, 
  Box, 
  Alert, 
  Tabs, 
  Tab, 
  Paper,
  CircularProgress
} from '@mui/material';
import { AlertCircle, Database, List, FileText, CheckCircle } from 'lucide-react';
import SQLServerConfig from './SQLServerConfig';
import { getApiBaseUrl } from '../api/chatApi';

const SQLServerForm = ({ 
  onFetchData,
  datasetName,
  setDatasetName,
  loading,
  error,
  setError,
  onSave = () => {},
  onClose = () => {}
}) => {
  const [credentials, setCredentials] = useState({
    server: '',
    database: '',
    username: '',
    password: '',
    trusted_connection: 'yes'
  });
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState('');
  const [customQuery, setCustomQuery] = useState('');
  const [activeTab, setActiveTab] = useState('table');
  const [rowLimit, setRowLimit] = useState(100);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [availableDrivers, setAvailableDrivers] = useState([]);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Get the API base URL
  const apiBaseUrl = getApiBaseUrl();
  
  const handleSaveConnection = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Send the connection details to the backend
      const response = await fetch(`${apiBaseUrl}/external-data/configure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_source_id: 'sql_server',
          credentials: {
            server: credentials.server,
            database: credentials.database,
            username: credentials.username,
            password: credentials.password,
            trusted_connection: credentials.trusted_connection
          }
        }),
      });
      
      const data = await response.json();
      
      if (!data.success) {
        setError(data.error || 'Unknown error occurred');
        setIsLoading(false);
        return;
      }
      
      // Fetch database DDL for improved text-to-SQL capabilities
      console.log('Fetching database DDL for improved text-to-SQL capabilities...');
      try {
        const ddlResponse = await fetch(`${apiBaseUrl}/external-data/sql/get-ddl`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            credentials: {
              server: credentials.server,
              database: credentials.database,
              username: credentials.username,
              password: credentials.password,
              trusted_connection: credentials.trusted_connection
            }
          }),
        });
        
        const ddlData = await ddlResponse.json();
        
        // Safely sanitize and parse the DDL data before storing
        if (ddlData && ddlData.success && ddlData.ddl) {
          try {
            // The actual DDL is wrapped in a 'ddl' property
            const ddlObj = ddlData.ddl;
            
            // Ensure we have valid JSON by stringifying and parsing
            // This helps catch any NaN values or other JSON serialization issues
            const sanitizedDDL = JSON.stringify(ddlObj);
            const parsedDDL = JSON.parse(sanitizedDDL);
            
            // Log what tables were found
            if (parsedDDL.tables) {
              const tableNames = Object.keys(parsedDDL.tables);
              console.log(`Found ${tableNames.length} tables in database: ${tableNames.join(', ')}`);
              
              // Log full structure for debugging
              console.log('DDL structure saved to localStorage:', {
                tablesCount: tableNames.length,
                relationshipsCount: parsedDDL.relationships?.length || 0,
                indexesCount: parsedDDL.indexes?.length || 0,
                firstTableColumns: tableNames.length > 0 ? parsedDDL.tables[tableNames[0]].length : 0
              });
            } else {
              console.warn('No tables property found in DDL data structure', parsedDDL);
            }
            
            // Save the DDL to localStorage
            localStorage.setItem('sqlDatabaseDDL', sanitizedDDL);
            console.log('Database DDL saved to localStorage for text-to-SQL enhancement');
          } catch (parseError) {
            console.error('Error parsing DDL data:', parseError);
            setError(`Database connection saved, but schema fetch failed: ${parseError.message}`);
          }
        } else if (ddlData && ddlData.error) {
          console.error('Error fetching database DDL:', ddlData.error);
          setError(`Database connection saved, but schema fetch failed: ${ddlData.error}`);
        }
      } catch (ddlError) {
        console.error('Error fetching database DDL:', ddlError);
        setError(`Database connection saved, but schema fetch failed: ${ddlError.message}`);
      }
      
      console.log('SQL Server connection saved successfully');
      
      // Show success message before closing
      setSaveSuccess(true);
      
      // Save connection details for easy reconnection
      localStorage.setItem('sqlServer', credentials.server);
      localStorage.setItem('sqlDatabase', credentials.database);
      localStorage.setItem('sqlUsername', credentials.username);
      localStorage.setItem('sqlTrustedConnection', credentials.trusted_connection.toString());
      
      // Clear the password from storage for security
      localStorage.removeItem('sqlPassword');
      
      // Call onSave with the connection details
      if (onSave) {
        onSave(credentials);
      }
      
      // Set loading to false immediately but keep form open longer
      setIsLoading(false);
      
      // Delay closing the form to allow user to see success message
      setTimeout(() => {
        onClose();
      }, 3000);
    } catch (error) {
      console.error('Error saving SQL Server connection:', error);
      setError(`Error saving connection: ${error.message}`);
      setIsLoading(false);
    }
  };
  
  const handleTestConnection = async () => {
    if (!credentials.server || !credentials.database) {
      setError("Server and database names are required");
      return;
    }
    
    setError(null);
    setTestingConnection(true);
    setConnectionStatus(null);
    
    try {
      const response = await fetch(`${apiBaseUrl}/external-data/sql/test-connection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Don't automatically save connection when testing is successful
        // handleSaveConnection();
        
        setConnectionStatus({
          success: true,
          message: data.message,
          systemInfo: data.system_info
        });
        setAvailableDrivers(data.available_drivers || []);
      } else {
        // Format troubleshooting tips if available
        let errorMessage = data.error || 'Connection failed';
        
        if (data.error_details) {
          errorMessage = data.error_details;
        }
        
        if (data.troubleshooting && Array.isArray(data.troubleshooting)) {
          errorMessage += "\n\nTroubleshooting tips:\n" + data.troubleshooting.join("\n");
        }
        
        setConnectionStatus({
          success: false,
          message: errorMessage,
          systemInfo: data.system_info,
          troubleshooting: data.troubleshooting
        });
        setError(errorMessage);
      }
    } catch (err) {
      setConnectionStatus({
        success: false,
        message: 'Error testing connection'
      });
      setError('Error testing connection: ' + (err.message || 'Unknown error'));
      console.error('Error testing connection:', err);
    } finally {
      setTestingConnection(false);
    }
  };
  
  const handleFetchTables = async () => {
    if (!credentials.server || !credentials.database) {
      setError("Server and database names are required");
      return;
    }
    
    setError(null);
    
    try {
      // Show loading state
      setTables([]);
      setError(null);
      
      console.log(`Fetching tables from: ${apiBaseUrl}/external-data/sql/tables`);
      
      const response = await fetch(`${apiBaseUrl}/external-data/sql/tables`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ credentials: credentials }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`Server responded with status: ${response.status}. ${errorText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        console.log(`Retrieved ${data.tables?.length || 0} tables:`, data.tables);
        setTables(data.tables || []);
        if (!datasetName) {
          setDatasetName(`${credentials.database}_data`);
        }
      } else {
        setError(data.error || 'Failed to fetch tables');
        console.error('API error:', data.error);
      }
    } catch (err) {
      setError(`Error connecting to server: ${err.message}`);
      console.error('Error fetching tables:', err);
    }
  };
  
  const handleDataFetch = () => {
    // Prepare params based on active tab
    const params = {
      limit: rowLimit
    };
    
    if (activeTab === 'table') {
      if (!selectedTable) {
        setError('Please select a table');
        return;
      }
      params.table_name = selectedTable;
    } else {
      if (!customQuery.trim()) {
        setError('Please enter a SQL query');
        return;
      }
      params.query = customQuery;
    }
    
    onFetchData('sql_server', activeTab === 'table' ? 'table_data' : 'custom_query', params, credentials);
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };
  
  return (
    <div>
      <SQLServerConfig 
        credentials={credentials}
        setCredentials={setCredentials}
        onSave={handleSaveConnection}
        onFetchTables={handleFetchTables}
        onTestConnection={handleTestConnection}
        testingConnection={testingConnection}
        connectionStatus={connectionStatus}
        availableDrivers={availableDrivers}
        tables={tables}
        onSelectTable={setSelectedTable}
        selectedTable={selectedTable}
      />
      
      {tables.length > 0 && (
        <Card style={{ marginTop: '16px' }}>
          <CardHeader title="Query Data" subheader="Fetch data from SQL Server" />
          <CardContent>
            <Box sx={{ width: '100%' }}>
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={activeTab} onChange={handleTabChange} aria-label="SQL query options">
                  <Tab 
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Database style={{ marginRight: '8px', height: '16px', width: '16px' }} />
                        Table Data
                      </Box>
                    } 
                    value="table" 
                  />
                  <Tab 
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <FileText style={{ marginRight: '8px', height: '16px', width: '16px' }} />
                        Custom Query
                      </Box>
                    } 
                    value="query" 
                  />
                </Tabs>
              </Box>
              
              <Box sx={{ padding: 2 }}>
                {activeTab === 'table' && (
                  selectedTable ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Paper 
                        elevation={0} 
                        sx={{ 
                          p: 2, 
                          display: 'flex', 
                          alignItems: 'center',
                          bgcolor: 'primary.light',
                          color: 'primary.contrastText'
                        }}
                      >
                        <Database style={{ marginRight: '8px', height: '20px', width: '20px' }} />
                        <Typography>
                          Selected table: <strong>{selectedTable}</strong>
                        </Typography>
                      </Paper>
                      
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>Row Limit</Typography>
                        <TextField
                          type="number"
                          inputProps={{ min: 1, max: 10000 }}
                          value={rowLimit}
                          onChange={(e) => setRowLimit(parseInt(e.target.value) || 100)}
                          fullWidth
                          size="small"
                        />
                      </Box>
                    </Box>
                  ) : (
                    <Box sx={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      py: 4
                    }}>
                      <List style={{ height: '40px', width: '40px', marginBottom: '16px', color: '#888' }} />
                      <Typography color="textSecondary">
                        Select a table from the list above
                      </Typography>
                    </Box>
                  )
                )}
                
                {activeTab === 'query' && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>SQL Query</Typography>
                    <TextField
                      multiline
                      rows={6}
                      placeholder="SELECT * FROM Customers"
                      value={customQuery}
                      onChange={(e) => setCustomQuery(e.target.value)}
                      fullWidth
                      variant="outlined"
                      sx={{ fontFamily: 'monospace' }}
                    />
                  </Box>
                )}
              </Box>
            </Box>

            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle2" gutterBottom>Dataset Name</Typography>
              <TextField
                fullWidth
                value={datasetName}
                onChange={(e) => setDatasetName(e.target.value)}
                placeholder="Enter a name for this dataset"
                size="small"
                sx={{ mb: 2 }}
              />
              
              <Button 
                fullWidth 
                variant="contained" 
                onClick={handleDataFetch}
                disabled={loading || (activeTab === 'table' && !selectedTable) || (activeTab === 'query' && !customQuery.trim())}
              >
                {loading ? 'Loading...' : 'Fetch Data'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
      
      {error && (
        <Alert 
          severity="error" 
          icon={<AlertCircle style={{ height: '16px', width: '16px' }} />}
          style={{ marginTop: '16px' }}
        >
          {error}
        </Alert>
      )}

      {saveSuccess && (
        <Alert 
          severity="success" 
          icon={<CheckCircle style={{ height: '20px', width: '20px' }} />}
          style={{ 
            marginTop: '16px',
            padding: '12px',
            fontSize: '1rem',
            boxShadow: '0 1px 4px rgba(0, 0, 0, 0.05)'
          }}
          variant="outlined"
        >
          SQL Server connection saved successfully! Found {
            (() => {
              try {
                const storedDDL = localStorage.getItem('sqlDatabaseDDL');
                if (storedDDL) {
                  const ddlObj = JSON.parse(storedDDL);
                  if (ddlObj?.tables) {
                    return Object.keys(ddlObj.tables).length;
                  }
                }
                return 0;
              } catch (e) {
                return 0;
              }
            })()
          } tables.
        </Alert>
      )}
    </div>
  );
};

export default SQLServerForm; 