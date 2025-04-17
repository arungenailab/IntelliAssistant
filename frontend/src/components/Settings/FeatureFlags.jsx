import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Box,
  Grid,
  Divider,
  Alert
} from '@mui/material';

// Mock feature flags service for now
// In a real app, this would connect to a backend API
const mockFlags = {
  'enable_langgraph_sql': {
    name: 'LangGraph SQL',
    description: 'Use the new LangGraph-based SQL generation with reflection capabilities',
    enabled: true,
  },
  'enable_visualization': {
    name: 'Advanced Visualizations',
    description: 'Enable advanced data visualization capabilities',
    enabled: true,
  },
  'enable_reflection': {
    name: 'Query Reflection',
    description: 'Enable reflection capabilities for SQL queries to improve accuracy',
    enabled: true,
  },
  'enable_execution': {
    name: 'SQL Execution',
    description: 'Allow system to execute generated SQL queries against the database',
    enabled: false,
  }
};

const FeatureFlags = () => {
  const [flags, setFlags] = useState(mockFlags);
  const [saveStatus, setSaveStatus] = useState(null);

  useEffect(() => {
    // In a real app, this would fetch flags from an API
    setFlags(mockFlags);
  }, []);

  const handleToggleFlag = (flagKey) => {
    setFlags(prevFlags => ({
      ...prevFlags,
      [flagKey]: {
        ...prevFlags[flagKey],
        enabled: !prevFlags[flagKey].enabled
      }
    }));
    
    // Simulate saving to backend
    setSaveStatus({ type: 'success', message: `Updated ${flags[flagKey].name} setting` });
    
    // Clear the status after 3 seconds
    setTimeout(() => {
      setSaveStatus(null);
    }, 3000);
  };

  return (
    <Card elevation={0} sx={{ mb: 4 }}>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          Feature Flags
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          Enable or disable experimental features.
        </Typography>
        
        {saveStatus && (
          <Alert 
            severity={saveStatus.type} 
            sx={{ mb: 2 }}
            onClose={() => setSaveStatus(null)}
          >
            {saveStatus.message}
          </Alert>
        )}
        
        <Grid container spacing={2}>
          {Object.entries(flags).map(([key, flag]) => (
            <Grid item xs={12} key={key}>
              <Box 
                sx={{ 
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  py: 1
                }}
              >
                <Box>
                  <Typography variant="subtitle1">
                    {flag.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {flag.description}
                  </Typography>
                </Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={flag.enabled}
                      onChange={() => handleToggleFlag(key)}
                      color="primary"
                    />
                  }
                  label=""
                />
              </Box>
              <Divider sx={{ mt: 1 }} />
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default FeatureFlags;