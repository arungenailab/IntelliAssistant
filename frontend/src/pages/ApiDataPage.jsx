import React, { useState, useEffect } from 'react';
import { 
  Button, 
  Card, 
  CardContent, 
  CardHeader, 
  Typography, 
  Grid, 
  Box, 
  Alert,
  Paper,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Link,
  Tooltip
} from '@mui/material';
import { Database, RefreshCw, Settings, ArrowRight, AlertCircle, Wifi, WifiOff, Bug } from 'lucide-react';
import SQLServerForm from '../components/SQLServerForm';
import { getApiBaseUrl, checkApiStatus, debugApiConnection } from '../api/chatApi';

export default function ApiDataPage() {
  const [apiSources, setApiSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSource, setSelectedSource] = useState(null);
  const [selectedEndpoint, setSelectedEndpoint] = useState('');
  const [apiParams, setApiParams] = useState({});
  const [apiCredentials, setApiCredentials] = useState({});
  const [datasetName, setDatasetName] = useState('');
  const [fetchingData, setFetchingData] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState(null);
  
  // Get the API base URL
  const apiBaseUrl = getApiBaseUrl();

  // Check API server status and fetch available API sources on component mount
  useEffect(() => {
    checkApiServerStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  const checkApiServerStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Checking API server status...');
      
      const status = await checkApiStatus();
      setApiStatus(status);
      console.log('API server status:', status);
      
      if (status.success) {
        await fetchApiSources();
      }
    } catch (err) {
      console.error('Error checking API server status:', err);
      
      // Provide a more user-friendly error message
      let errorMessage = `Cannot connect to API server: ${err.message}`;
      
      // Add troubleshooting tips
      errorMessage += "\n\nTroubleshooting tips:";
      errorMessage += "\n- Make sure the backend server is running (python api.py)";
      errorMessage += "\n- Check that the server is running on port 5000";
      errorMessage += "\n- Verify there are no firewall or network issues";
      errorMessage += "\n- Check the browser console for CORS errors";
      
      setError(errorMessage);
      setApiStatus({ success: false, error: err.message });
    } finally {
      setLoading(false);
    }
  };

  const fetchApiSources = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log(`Fetching API sources from ${apiBaseUrl}/external-data/sources`);
      
      const response = await fetch(`${apiBaseUrl}/external-data/sources`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for CORS requests
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        console.log('API sources fetched successfully:', data.sources);
        setApiSources(data.sources || []);
      } else {
        throw new Error(data.error || 'Failed to fetch API sources');
      }
    } catch (err) {
      console.error('Error fetching API sources:', err);
      setError(`Error connecting to server: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSourceSelect = (source) => {
    setSelectedSource(source);
    setSelectedEndpoint('');
    setApiParams({});
    setPreviewData(null);
  };

  const handleEndpointSelect = (endpoint) => {
    setSelectedEndpoint(endpoint);
    setApiParams({});
    setPreviewData(null);
  };

  const handleParamChange = (key, value) => {
    setApiParams(prev => ({ ...prev, [key]: value }));
  };

  const handleCredentialChange = (key, value) => {
    setApiCredentials(prev => ({ ...prev, [key]: value }));
  };

  const handleDatasetNameChange = (event) => {
    setDatasetName(event.target.value);
  };

  const handleSaveCredentials = async () => {
    if (!selectedSource) return;
    
    setError(null);
    
    try {
      console.log(`Saving credentials to ${apiBaseUrl}/external-data/configure`);
      
      const response = await fetch(`${apiBaseUrl}/external-data/configure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for CORS requests
        body: JSON.stringify({
          api_source_id: selectedSource.id,
          credentials: apiCredentials
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        alert('API credentials saved successfully');
      } else {
        throw new Error(data.error || 'Failed to save credentials');
      }
    } catch (err) {
      console.error('Error saving credentials:', err);
      setError(`Error connecting to server: ${err.message}`);
    }
  };

  const handleFetchData = async (sourceId, endpoint, params, sqlCredentials = null) => {
    // If parameters are not provided, use the component state
    const apiSourceId = sourceId || (selectedSource ? selectedSource.id : null);
    const apiEndpoint = endpoint || selectedEndpoint;
    const apiParamsToUse = params || apiParams;
    
    // Use provided SQL credentials or fallback to component state
    const credentialsToUse = apiSourceId === 'sql_server' && sqlCredentials ? 
      sqlCredentials : apiCredentials;
    
    if (!apiSourceId || !apiEndpoint) return;
    
    setFetchingData(true);
    setError(null);
    setPreviewData(null);
    
    try {
      console.log(`Fetching data from ${apiBaseUrl}/external-data/fetch`);
      console.log('Request payload:', {
        api_source_id: apiSourceId,
        endpoint: apiEndpoint,
        params: apiParamsToUse,
        credentials: credentialsToUse ? '(credentials provided)' : '(no credentials)',
        dataset_name: datasetName || `${apiSourceId}_${apiEndpoint}`
      });
      
      const response = await fetch(`${apiBaseUrl}/external-data/fetch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for CORS requests
        body: JSON.stringify({
          api_source_id: apiSourceId,
          endpoint: apiEndpoint,
          params: apiParamsToUse,
          credentials: credentialsToUse,
          dataset_name: datasetName || `${apiSourceId}_${apiEndpoint}`
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setPreviewData(data);
        alert(`Data fetched successfully and saved as "${datasetName || `${apiSourceId}_${apiEndpoint}`}"`);
      } else {
        setError(data.error || 'Failed to fetch data');
      }
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(`Error connecting to server: ${err.message}`);
    } finally {
      setFetchingData(false);
    }
  };

  // Add debug function
  const handleDebugConnection = () => {
    console.log('Debugging API connection...');
    const debugInfo = debugApiConnection();
    console.log('Debug info:', debugInfo);
    
    // Show a more detailed error message
    if (error) {
      setError(prev => `${prev}\n\nDebug info:\nAPI Base URL: ${debugInfo.apiBaseUrl}\nOrigin: ${debugInfo.origin}`);
    }
  };

  const renderSourceList = () => {
    if (loading) return <Typography align="center" sx={{ py: 4 }}>Loading API sources...</Typography>;
    
    if (apiSources.length === 0) {
      return (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <AlertCircle style={{ height: '40px', width: '40px', color: '#888', margin: '0 auto 16px' }} />
          <Typography color="textSecondary">No API sources available</Typography>
          <Button variant="outlined" onClick={fetchApiSources} sx={{ mt: 2 }}>
            <RefreshCw style={{ marginRight: '8px', height: '16px', width: '16px' }} /> Refresh
          </Button>
        </Box>
      );
    }
    
    return (
      <Grid container spacing={2}>
        {apiSources.map((source) => (
          <Grid item xs={12} md={6} lg={4} key={source.id}>
            <Card 
              sx={{ 
                cursor: 'pointer', 
                transition: 'all 0.2s',
                '&:hover': { borderColor: 'primary.main' },
                ...(selectedSource?.id === source.id ? { 
                  borderColor: 'primary.main',
                  bgcolor: 'primary.light',
                  '& .MuiCardContent-root': { opacity: 0.9 }
                } : {})
              }}
              onClick={() => handleSourceSelect(source)}
            >
              <CardHeader
                title={
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="h6">{source.name}</Typography>
                    <Database style={{ height: '20px', width: '20px', color: '#666' }} />
                  </Box>
                }
                subheader={source.description}
              />
              <CardContent sx={{ pt: 0, borderTop: '1px solid', borderColor: 'divider' }}>
                <Typography variant="caption" color="textSecondary">
                  {source.auth_required ? 'Authentication required' : 'No authentication required'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  const renderConfigSection = () => {
    if (!selectedSource) return null;
    
    // Special case for SQL Server
    if (selectedSource.id === 'sql_server') {
      return (
        <SQLServerForm
          onFetchData={handleFetchData}
          datasetName={datasetName}
          setDatasetName={setDatasetName}
          loading={fetchingData}
          error={error}
          setError={setError}
        />
      );
    }
    
    return (
      <Card sx={{ mt: 3 }}>
        <CardHeader 
          title={`Configure ${selectedSource.name}`}
          subheader="Set up the connection parameters and credentials"
        />
        <CardContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {selectedSource.auth_required && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>Authentication</Typography>
                <Box sx={{ mb: 2 }}>
                  {selectedSource.auth_type === 'api_key' && (
                    <Box>
                      <Typography variant="body2" gutterBottom>API Key</Typography>
                      <input
                        type="password"
                        value={apiCredentials.api_key || ''}
                        onChange={(e) => handleCredentialChange('api_key', e.target.value)}
                        placeholder="Enter your API key"
                        style={{ 
                          width: '100%', 
                          padding: '8px', 
                          border: '1px solid #ddd',
                          borderRadius: '4px'
                        }}
                      />
                    </Box>
                  )}
                  <Button 
                    variant="outlined" 
                    onClick={handleSaveCredentials} 
                    size="small"
                    sx={{ mt: 1 }}
                    startIcon={<Settings style={{ height: '16px', width: '16px' }} />}
                  >
                    Save Credentials
                  </Button>
                </Box>
              </Box>
            )}
            
            <Box>
              <Typography variant="subtitle2" gutterBottom>Endpoint</Typography>
              <Grid container spacing={1}>
                {selectedSource.endpoints?.map((endpoint) => (
                  <Grid item xs={12} md={4} key={endpoint}>
                    <Button
                      variant={selectedEndpoint === endpoint ? "contained" : "outlined"}
                      onClick={() => handleEndpointSelect(endpoint)}
                      sx={{ 
                        justifyContent: 'flex-start', 
                        width: '100%',
                        textTransform: 'none'
                      }}
                      startIcon={<Database style={{ height: '16px', width: '16px' }} />}
                    >
                      {endpoint}
                    </Button>
                  </Grid>
                ))}
              </Grid>
            </Box>
            
            {selectedEndpoint && (
              <>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>Parameters</Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {selectedEndpoint === 'stocks' && (
                      <Box>
                        <Typography variant="body2" gutterBottom>Symbol</Typography>
                        <input
                          value={apiParams.symbol || ''}
                          onChange={(e) => handleParamChange('symbol', e.target.value)}
                          placeholder="e.g., MSFT"
                          style={{ 
                            width: '100%', 
                            padding: '8px', 
                            border: '1px solid #ddd',
                            borderRadius: '4px'
                          }}
                        />
                      </Box>
                    )}
                    
                    {selectedEndpoint === 'forex' && (
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="body2" gutterBottom>From Currency</Typography>
                          <input
                            value={apiParams.from_currency || ''}
                            onChange={(e) => handleParamChange('from_currency', e.target.value)}
                            placeholder="e.g., USD"
                            style={{ 
                              width: '100%', 
                              padding: '8px', 
                              border: '1px solid #ddd',
                              borderRadius: '4px'
                            }}
                          />
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" gutterBottom>To Currency</Typography>
                          <input
                            value={apiParams.to_currency || ''}
                            onChange={(e) => handleParamChange('to_currency', e.target.value)}
                            placeholder="e.g., EUR"
                            style={{ 
                              width: '100%', 
                              padding: '8px', 
                              border: '1px solid #ddd',
                              borderRadius: '4px'
                            }}
                          />
                        </Grid>
                      </Grid>
                    )}
                    
                    {selectedEndpoint === 'crypto' && (
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="body2" gutterBottom>Symbol</Typography>
                          <input
                            value={apiParams.symbol || ''}
                            onChange={(e) => handleParamChange('symbol', e.target.value)}
                            placeholder="e.g., BTC"
                            style={{ 
                              width: '100%', 
                              padding: '8px', 
                              border: '1px solid #ddd',
                              borderRadius: '4px'
                            }}
                          />
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" gutterBottom>Market</Typography>
                          <input
                            value={apiParams.market || ''}
                            onChange={(e) => handleParamChange('market', e.target.value)}
                            placeholder="e.g., USD"
                            style={{ 
                              width: '100%', 
                              padding: '8px', 
                              border: '1px solid #ddd',
                              borderRadius: '4px'
                            }}
                          />
                        </Grid>
                      </Grid>
                    )}
                  </Box>
                </Box>
                
                <Box>
                  <Typography variant="subtitle2" gutterBottom>Dataset Name</Typography>
                  <input
                    value={datasetName}
                    onChange={handleDatasetNameChange}
                    placeholder={`${selectedSource.id}_${selectedEndpoint}`}
                    style={{ 
                      width: '100%', 
                      padding: '8px', 
                      border: '1px solid #ddd',
                      borderRadius: '4px'
                    }}
                  />
                  <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
                    Name to save this dataset as. Leave blank for default name.
                  </Typography>
                </Box>
                
                <Button 
                  variant="contained" 
                  onClick={() => handleFetchData(selectedSource?.id, selectedEndpoint, apiParams)} 
                  disabled={fetchingData}
                  fullWidth
                  sx={{ mt: 1 }}
                  startIcon={fetchingData ? 
                    <CircularProgress size={20} color="inherit" /> : 
                    <Database style={{ height: '16px', width: '16px' }} />
                  }
                >
                  {fetchingData ? 'Fetching Data...' : 'Fetch Data'}
                </Button>
              </>
            )}
          </Box>
        </CardContent>
      </Card>
    );
  };

  const renderPreview = () => {
    if (!previewData) return null;
    
    return (
      <Card sx={{ mt: 3 }}>
        <CardHeader 
          title="Data Preview"
          subheader={`${previewData.shape?.[0]} rows × ${previewData.shape?.[1]} columns`}
        />
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  {previewData.preview?.columns?.map((column, i) => (
                    <TableCell key={i} sx={{ fontWeight: 'bold' }}>
                      {column}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {previewData.preview?.data?.map((row, i) => (
                  <TableRow key={i}>
                    {row.map((cell, j) => (
                      <TableCell key={j}>
                        {String(cell)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
        <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
          <Button 
            component={Link} 
            href="/data"
            variant="outlined"
            endIcon={<ArrowRight style={{ height: '16px', width: '16px' }} />}
          >
            Analyze This Data
          </Button>
        </Box>
      </Card>
    );
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Box>
        <Typography variant="h4" gutterBottom>External Data Sources</Typography>
        <Typography color="textSecondary">
          Connect to external APIs to import and analyze data
        </Typography>
        
        {/* API Server Status */}
        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
          {apiStatus ? (
            apiStatus.success ? (
              <>
                <Wifi size={16} color="green" style={{ marginRight: '8px' }} />
                <Typography variant="body2" color="success.main">
                  API Server Connected
                </Typography>
              </>
            ) : (
              <>
                <WifiOff size={16} color="red" style={{ marginRight: '8px' }} />
                <Typography variant="body2" color="error.main">
                  API Server Disconnected
                </Typography>
              </>
            )
          ) : (
            <>
              <CircularProgress size={16} style={{ marginRight: '8px' }} />
              <Typography variant="body2" color="text.secondary">
                Checking API Server...
              </Typography>
            </>
          )}
          <Button 
            size="small" 
            variant="text" 
            onClick={checkApiServerStatus} 
            sx={{ ml: 2 }}
            disabled={loading}
          >
            <RefreshCw size={14} style={{ marginRight: '4px' }} />
            Refresh
          </Button>
          
          {/* Debug button */}
          <Tooltip title="Debug API connection">
            <Button 
              size="small" 
              variant="text" 
              color="secondary"
              onClick={handleDebugConnection} 
              sx={{ ml: 1 }}
            >
              <Bug size={14} style={{ marginRight: '4px' }} />
              Debug
            </Button>
          </Tooltip>
        </Box>
      </Box>
      
      {error && (
        <Alert 
          severity="error"
          icon={<AlertCircle style={{ height: '20px', width: '20px' }} />}
          sx={{ mb: 3, whiteSpace: 'pre-line' }}
        >
          {error}
          
          {/* Add a retry button */}
          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button 
              variant="outlined" 
              size="small" 
              color="error" 
              onClick={checkApiServerStatus}
              startIcon={<RefreshCw size={16} />}
              disabled={loading}
            >
              Retry Connection
            </Button>
            
            <Button 
              variant="outlined" 
              size="small" 
              color="secondary" 
              onClick={handleDebugConnection}
              startIcon={<Bug size={16} />}
            >
              Debug Connection
            </Button>
          </Box>
        </Alert>
      )}
      
      {renderSourceList()}
      {renderConfigSection()}
      {renderPreview()}
    </Box>
  );
} 