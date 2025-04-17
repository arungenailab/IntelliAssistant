import React, { useState, useEffect } from 'react';
import { Switch, FormControlLabel, Typography, Paper, Box, Divider } from '@mui/material';

/**
 * Feature Flags component for controlling application features
 */
const FeatureFlags = () => {
  // State for feature flags
  const [enableLangGraphSql, setEnableLangGraphSql] = useState(false);
  const [enableSqlReflection, setEnableSqlReflection] = useState(true);
  const [enableSqlExecution, setEnableSqlExecution] = useState(true);

  // Load saved settings on component mount
  useEffect(() => {
    // Load settings from localStorage
    const savedLangGraphSql = localStorage.getItem('enableLangGraphSql');
    const savedSqlReflection = localStorage.getItem('enableSqlReflection');
    const savedSqlExecution = localStorage.getItem('enableSqlExecution');
    
    // Set states with saved values or defaults
    setEnableLangGraphSql(savedLangGraphSql === 'true');
    setEnableSqlReflection(savedSqlReflection === null ? true : savedSqlReflection === 'true');
    setEnableSqlExecution(savedSqlExecution === null ? true : savedSqlExecution === 'true');
  }, []);

  // Handle LangGraph SQL toggle
  const handleLangGraphSqlToggle = (event) => {
    const newValue = event.target.checked;
    setEnableLangGraphSql(newValue);
    localStorage.setItem('enableLangGraphSql', newValue);
    console.log(`LangGraph SQL ${newValue ? 'enabled' : 'disabled'}`);
  };

  // Handle SQL Reflection toggle
  const handleSqlReflectionToggle = (event) => {
    const newValue = event.target.checked;
    setEnableSqlReflection(newValue);
    localStorage.setItem('enableSqlReflection', newValue);
    console.log(`SQL Reflection ${newValue ? 'enabled' : 'disabled'}`);
  };

  // Handle SQL Execution toggle
  const handleSqlExecutionToggle = (event) => {
    const newValue = event.target.checked;
    setEnableSqlExecution(newValue);
    localStorage.setItem('enableSqlExecution', newValue);
    console.log(`SQL Execution ${newValue ? 'enabled' : 'disabled'}`);
  };

  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Feature Flags
      </Typography>
      
      <Divider sx={{ mb: 2 }} />
      
      <Box sx={{ mb: 2 }}>
        <FormControlLabel
          control={
            <Switch
              checked={enableLangGraphSql}
              onChange={handleLangGraphSqlToggle}
              color="primary"
            />
          }
          label="Use LangGraph SQL Converter"
        />
        <Typography variant="body2" color="text.secondary" sx={{ ml: 3, mt: 0.5 }}>
          Enables the new LangGraph-based SQL converter with improved accuracy and reflection capabilities
        </Typography>
      </Box>
      
      <Box sx={{ mb: 2, ml: 3 }}>
        <FormControlLabel
          control={
            <Switch
              checked={enableSqlReflection}
              onChange={handleSqlReflectionToggle}
              color="primary"
              disabled={!enableLangGraphSql}
            />
          }
          label="Enable SQL Reflection"
        />
        <Typography variant="body2" color="text.secondary" sx={{ ml: 3, mt: 0.5 }}>
          Validates and improves generated SQL queries (requires LangGraph SQL)
        </Typography>
      </Box>
      
      <Box sx={{ mb: 2, ml: 3 }}>
        <FormControlLabel
          control={
            <Switch
              checked={enableSqlExecution}
              onChange={handleSqlExecutionToggle}
              color="primary"
              disabled={!enableLangGraphSql}
            />
          }
          label="Enable SQL Execution"
        />
        <Typography variant="body2" color="text.secondary" sx={{ ml: 3, mt: 0.5 }}>
          Executes generated SQL queries (disable for query-only mode)
        </Typography>
      </Box>
    </Paper>
  );
};

export default FeatureFlags; 