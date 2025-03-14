import React, { useState } from 'react';
import { 
  Button, 
  Menu, 
  MenuItem, 
  FormControlLabel,
  Switch,
  Tooltip,
  Typography,
  Box,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import TuneIcon from '@mui/icons-material/Tune';
import FlashOnIcon from '@mui/icons-material/FlashOn';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import CachedIcon from '@mui/icons-material/Cached';
import LightbulbIcon from '@mui/icons-material/Lightbulb';

// Define available models
const MODELS = [
  {
    id: 'gemini-2.0-flash',
    name: 'Gemini 2.0 Flash',
    description: 'Fast responses, best for most queries',
    icon: <FlashOnIcon fontSize="small" />,
    isDefault: true
  },
  {
    id: 'gemini-2.0-pro',
    name: 'Gemini 2.0 Pro',
    description: 'More powerful, best for complex analysis',
    icon: <AutoAwesomeIcon fontSize="small" />
  },
  {
    id: 'gemini-1.5-flash',
    name: 'Gemini 1.5 Flash',
    description: 'Legacy model (fallback)',
    icon: <SmartToyIcon fontSize="small" />
  }
];

const ModelSelector = ({ selectedModel, useCache, onModelChange, onCacheToggle }) => {
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);
  
  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };
  
  const handleClose = () => {
    setAnchorEl(null);
  };
  
  const handleModelSelect = (modelId) => {
    onModelChange(modelId);
    handleClose();
  };
  
  const handleCacheToggle = (event) => {
    onCacheToggle(event.target.checked);
  };
  
  // Find the currently selected model
  const currentModel = MODELS.find(model => model.id === selectedModel) || MODELS[0];
  
  return (
    <Box>
      <Tooltip title="Model settings">
        <Button
          size="small"
          onClick={handleClick}
          startIcon={<TuneIcon />}
          variant="text"
          color="inherit"
          sx={{ 
            color: 'text.secondary',
            fontSize: '0.75rem',
            textTransform: 'none',
            opacity: 0.8,
            '&:hover': { opacity: 1 }
          }}
        >
          {currentModel.name}
        </Button>
      </Tooltip>
      
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          elevation: 3,
          sx: { 
            minWidth: 250,
            maxWidth: 350
          }
        }}
      >
        <Typography variant="subtitle2" sx={{ px: 2, py: 1, fontWeight: 600 }}>
          AI Model Selection
        </Typography>
        
        <Divider />
        
        {MODELS.map((model) => (
          <MenuItem 
            key={model.id}
            selected={selectedModel === model.id}
            onClick={() => handleModelSelect(model.id)}
            sx={{ py: 1 }}
          >
            <ListItemIcon>
              {model.icon}
            </ListItemIcon>
            <ListItemText 
              primary={model.name} 
              secondary={model.description}
              primaryTypographyProps={{ fontWeight: selectedModel === model.id ? 600 : 400 }}
            />
          </MenuItem>
        ))}
        
        <Divider />
        
        <MenuItem sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
          <ListItemIcon>
            <CachedIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText 
            primary="Use response cache" 
            secondary="Faster responses for similar queries"
          />
          <Switch 
            size="small"
            checked={useCache}
            onChange={handleCacheToggle}
            inputProps={{ 'aria-label': 'toggle cache' }}
          />
        </MenuItem>
        
        <Box sx={{ px: 2, py: 1, fontSize: '0.75rem', color: 'text.secondary', display: 'flex', alignItems: 'center' }}>
          <LightbulbIcon fontSize="small" sx={{ mr: 1, fontSize: '1rem' }} />
          <Typography variant="caption">
            Select more powerful models for complex data analysis tasks, or faster models for simple queries.
          </Typography>
        </Box>
      </Menu>
    </Box>
  );
};

export default ModelSelector; 