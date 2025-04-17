import React from 'react';
import { Container, Typography, Box } from '@mui/material';
import FeatureFlags from '../components/Settings/FeatureFlags';

const Settings = () => {
  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Settings
        </Typography>
        
        {/* Feature Flags Section */}
        <FeatureFlags />
        
        {/* Add other settings sections here */}
      </Box>
    </Container>
  );
};

export default Settings; 