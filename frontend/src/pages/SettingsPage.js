import React from 'react';
import { Container, Typography, Box, Paper, Divider } from '@mui/material';
import FeatureFlags from '../components/Settings/FeatureFlags';

/**
 * SettingsPage component for application configuration
 */
const SettingsPage = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Settings
        </Typography>
        
        <Typography variant="body1" color="text.secondary" paragraph>
          Configure application features and preferences
        </Typography>
        
        <Divider sx={{ my: 3 }} />
        
        {/* Feature Flags Section */}
        <Typography variant="h5" component="h2" gutterBottom>
          Feature Management
        </Typography>
        
        <FeatureFlags />
        
        {/* Additional settings sections can be added here */}
      </Box>
    </Container>
  );
};

export default SettingsPage; 