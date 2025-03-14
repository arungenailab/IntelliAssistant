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
  setError
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
  
  // Get the API base URL
  const apiBaseUrl = getApiBaseUrl();
  
  const handleSaveConnection = async () => {
    // Validate connection parameters
    if (!credentials.server || !credentials.database) {
      setError("Server and database names are required");
      return;
    }
    
    setError(null);
    setSaveSuccess(false);
    
    try {
      console.log(`Saving SQL Server connection to ${apiBaseUrl}/external-data/configure`);
      
      const response = await fetch(`${apiBaseUrl}/external-data/configure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for CORS requests
        body: JSON.stringify({
          api_source_id: 'sql_server',
          credentials: credentials
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`Server responded with status: ${response.status}. ${errorText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        console.log('SQL Server connection saved successfully');
        setSaveSuccess(true);
      } else {
        throw new Error(data.error || 'Failed to save connection');
      }
    } catch (err) {
      setError(`Error saving connection: ${err.message}`);
      console.error('Error saving connection:', err);
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
          icon={<CheckCircle style={{ height: '16px', width: '16px' }} />}
          style={{ marginTop: '16px' }}
        >
          SQL Server connection saved successfully!
        </Alert>
      )}
    </div>
  );
};

export default SQLServerForm; 