import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  Typography, 
  TextField, 
  Button, 
  FormControlLabel, 
  Checkbox, 
  Box, 
  Alert, 
  MenuItem, 
  Select, 
  FormControl, 
  InputLabel,
  CircularProgress,
  Chip,
  Tooltip,
  FormHelperText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider
} from '@mui/material';
import { Database, AlertCircle, List, CheckCircle, XCircle, Info, ChevronDown } from 'lucide-react';

const SQLServerConfig = ({ 
  credentials, 
  setCredentials, 
  onSave, 
  onFetchTables, 
  onTestConnection,
  testingConnection,
  connectionStatus,
  availableDrivers = [],
  tables = [], 
  onSelectTable, 
  selectedTable 
}) => {
  const [error, setError] = useState(null);
  const [useWindowsAuth, setUseWindowsAuth] = useState(
    credentials?.trusted_connection === 'yes'
  );
  const [showSystemInfo, setShowSystemInfo] = useState(false);

  // Update credentials when Windows Auth checkbox changes
  useEffect(() => {
    setCredentials({
      ...credentials,
      trusted_connection: useWindowsAuth ? 'yes' : 'no'
    });
  }, [useWindowsAuth]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials({
      ...credentials,
      [name]: value
    });
  };

  const handleTableSelect = (e) => {
    const tableName = e.target.value;
    if (onSelectTable) {
      onSelectTable(tableName);
    }
  };

  // Format system info for display
  const renderSystemInfo = (systemInfo) => {
    if (!systemInfo) return null;
    
    return (
      <Box sx={{ mt: 2 }}>
        <Accordion>
          <AccordionSummary expandIcon={<ChevronDown size={16} />}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Info size={16} style={{ marginRight: '8px' }} />
              <Typography variant="subtitle2">System Information</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box component="pre" sx={{ 
              fontSize: '0.75rem', 
              backgroundColor: '#f5f5f5', 
              p: 1, 
              borderRadius: 1,
              maxHeight: '200px',
              overflow: 'auto'
            }}>
              {Object.entries(systemInfo).map(([key, value]) => (
                <div key={key}>
                  <strong>{key}:</strong> {
                    Array.isArray(value) 
                      ? value.join(', ') 
                      : typeof value === 'object' 
                        ? JSON.stringify(value) 
                        : String(value)
                  }
                </div>
              ))}
            </Box>
          </AccordionDetails>
        </Accordion>
      </Box>
    );
  };

  // Format troubleshooting tips for display
  const renderTroubleshooting = (tips) => {
    if (!tips || !Array.isArray(tips) || tips.length === 0) return null;
    
    return (
      <Box sx={{ mt: 2 }}>
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ChevronDown size={16} />}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <AlertCircle size={16} style={{ marginRight: '8px' }} />
              <Typography variant="subtitle2">Troubleshooting Tips</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box component="ul" sx={{ pl: 2, m: 0 }}>
              {tips.map((tip, index) => (
                <Typography component="li" key={index} variant="body2" sx={{ mb: 1 }}>
                  {tip}
                </Typography>
              ))}
            </Box>
          </AccordionDetails>
        </Accordion>
      </Box>
    );
  };

  return (
    <div style={{ marginBottom: '16px' }}>
      <Card>
        <CardHeader 
          title={
            <Box display="flex" alignItems="center">
              <Database style={{ marginRight: '8px', height: '20px', width: '20px' }} />
              <Typography variant="h6">SQL Server Connection</Typography>
            </Box>
          }
        />
        <CardContent>
          {error && (
            <Alert 
              severity="error" 
              icon={<AlertCircle style={{ height: '20px', width: '20px' }} />}
              style={{ marginBottom: '16px' }}
            >
              <Box sx={{ whiteSpace: 'pre-line' }}>{error}</Box>
            </Alert>
          )}

          {connectionStatus && (
            <Alert 
              severity={connectionStatus.success ? "success" : "error"} 
              icon={connectionStatus.success ? 
                <CheckCircle style={{ height: '20px', width: '20px' }} /> : 
                <XCircle style={{ height: '20px', width: '20px' }} />
              }
              style={{ marginBottom: '16px' }}
            >
              <Box sx={{ whiteSpace: 'pre-line' }}>{connectionStatus.message}</Box>
              
              {connectionStatus.success && availableDrivers.length > 0 && (
                <Box mt={1}>
                  <Typography variant="caption">Available drivers:</Typography>
                  <Box display="flex" flexWrap="wrap" gap={0.5} mt={0.5}>
                    {availableDrivers.map((driver, index) => (
                      <Chip key={index} label={driver} size="small" />
                    ))}
                  </Box>
                </Box>
              )}
              
              {/* Render system info if available */}
              {connectionStatus.systemInfo && renderSystemInfo(connectionStatus.systemInfo)}
              
              {/* Render troubleshooting tips if available */}
              {connectionStatus.troubleshooting && renderTroubleshooting(connectionStatus.troubleshooting)}
            </Alert>
          )}

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <Box>
                <Typography variant="subtitle2" gutterBottom>Server</Typography>
                <TextField
                  fullWidth
                  name="server"
                  placeholder="localhost\SQLEXPRESS"
                  value={credentials?.server || ''}
                  onChange={handleInputChange}
                  size="small"
                  helperText="Server name or IP address, include instance name if needed"
                />
              </Box>
              <Box>
                <Typography variant="subtitle2" gutterBottom>Database</Typography>
                <TextField
                  fullWidth
                  name="database"
                  placeholder="MyDatabase"
                  value={credentials?.database || ''}
                  onChange={handleInputChange}
                  size="small"
                />
              </Box>
            </Box>

            <FormControlLabel
              control={
                <Checkbox
                  checked={useWindowsAuth}
                  onChange={(e) => setUseWindowsAuth(e.target.checked)}
                />
              }
              label="Use Windows Authentication"
            />

            {!useWindowsAuth && (
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>Username</Typography>
                  <TextField
                    fullWidth
                    name="username"
                    placeholder="sa"
                    value={credentials?.username || ''}
                    onChange={handleInputChange}
                    disabled={useWindowsAuth}
                    size="small"
                  />
                </Box>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>Password</Typography>
                  <TextField
                    fullWidth
                    name="password"
                    type="password"
                    placeholder="Password"
                    value={credentials?.password || ''}
                    onChange={handleInputChange}
                    disabled={useWindowsAuth}
                    size="small"
                  />
                </Box>
              </Box>
            )}

            <Box>
              <Typography variant="subtitle2" gutterBottom>Driver (Optional)</Typography>
              <TextField
                fullWidth
                name="driver"
                placeholder="ODBC Driver 17 for SQL Server"
                value={credentials?.driver || ''}
                onChange={handleInputChange}
                size="small"
                helperText="Leave blank to auto-detect"
              />
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', marginTop: 2, gap: 1 }}>
              <Button 
                variant="contained" 
                onClick={onSave} 
                disabled={!credentials?.server || !credentials?.database}
              >
                Save Connection
              </Button>
              <Button 
                variant="outlined"
                onClick={onTestConnection}
                disabled={testingConnection || !credentials?.server || !credentials?.database}
                startIcon={testingConnection ? 
                  <CircularProgress size={16} /> : 
                  <CheckCircle style={{ height: '16px', width: '16px' }} />
                }
              >
                {testingConnection ? 'Testing...' : 'Test Connection'}
              </Button>
              <Button 
                variant="outlined"
                onClick={onFetchTables}
                disabled={!credentials?.server || !credentials?.database}
                startIcon={<List style={{ height: '16px', width: '16px' }} />}
              >
                List Tables
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {tables && tables.length > 0 && (
        <Card style={{ marginTop: '16px' }}>
          <CardHeader title="Available Tables" />
          <CardContent>
            <FormControl fullWidth>
              <InputLabel id="table-select-label">Select a table</InputLabel>
              <Select
                labelId="table-select-label"
                value={selectedTable || ''}
                onChange={handleTableSelect}
                label="Select a table"
              >
                {tables.map((table) => (
                  <MenuItem key={table} value={table}>
                    {table}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SQLServerConfig; 