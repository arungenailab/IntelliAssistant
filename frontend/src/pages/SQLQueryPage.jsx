import React from 'react';
import { Container, Typography, Box, Divider, Paper, Alert } from '@mui/material';
import SQLQueryComponent from '../components/SQLQueryComponent';

/**
 * Page component for the SQL Query feature
 */
function SQLQueryPage() {
  return (
    <Container maxWidth="xl">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          SQL Query Assistant
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" paragraph>
          Ask questions about your database in natural language, and I'll convert them to SQL and show you the results.
        </Typography>
        
        <Paper elevation={1} sx={{ p: 2, mb: 3, bgcolor: 'info.light', color: 'info.contrastText' }}>
          <Typography variant="body2">
            This page now uses saved connection IDs instead of passing credentials with each request.
            Your SQL connection details are securely stored at <code>~/.intelligassistant/sql_configs.json</code>.
          </Typography>
        </Paper>
        
        <Alert severity="info" sx={{ mb: 3 }}>
          Make sure you've tested and saved your SQL connection first. Connections are saved automatically when 
          you test them successfully through the SQL Server connection form.
        </Alert>
        
        <Divider sx={{ mb: 3 }} />
        
        <SQLQueryComponent />
      </Box>
    </Container>
  );
}

export default SQLQueryPage; 