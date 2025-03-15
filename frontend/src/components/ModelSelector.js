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
  Divider,
  useTheme
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
  const theme = useTheme();
  
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
            color: theme.palette.text.secondary,
            fontSize: '0.75rem',
            textTransform: 'none',
            opacity: 0.9,
            borderRadius: theme.shape.borderRadius,
            '&:hover': { 
              opacity: 1,
              backgroundColor: theme.palette.mode === 'dark' 
                ? 'rgba(255, 255, 255, 0.08)'
                : 'rgba(0, 0, 0, 0.04)'
            }
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
          elevation: 2,
          sx: { 
            minWidth: 250,
            maxWidth: 350,
            borderRadius: theme.shape.borderRadius,
            border: `1px solid ${theme.palette.divider}`,
            mt: 0.5
          }
        }}
      >
        <Typography variant="subtitle2" sx={{ px: 2, py: 1.5, fontWeight: 500 }}>
          AI Model Selection
        </Typography>
        
        <Divider />
        
        {MODELS.map((model) => (
          <MenuItem 
            key={model.id}
            selected={selectedModel === model.id}
            onClick={() => handleModelSelect(model.id)}
            sx={{ 
              py: 1.5,
              '&.Mui-selected': {
                backgroundColor: theme.palette.mode === 'dark' 
                  ? 'rgba(25, 118, 210, 0.12)'
                  : 'rgba(25, 118, 210, 0.08)',
                '&:hover': {
                  backgroundColor: theme.palette.mode === 'dark' 
                    ? 'rgba(25, 118, 210, 0.16)'
                    : 'rgba(25, 118, 210, 0.12)'
                }
              },
              '&:hover': {
                backgroundColor: theme.palette.mode === 'dark' 
                  ? 'rgba(255, 255, 255, 0.05)'
                  : 'rgba(0, 0, 0, 0.04)'
              }
            }}
          >
            <ListItemIcon sx={{
              color: selectedModel === model.id ? theme.palette.primary.main : 'inherit'
            }}>
              {model.icon}
            </ListItemIcon>
            <ListItemText 
              primary={model.name} 
              secondary={model.description}
              primaryTypographyProps={{ 
                fontWeight: selectedModel === model.id ? 500 : 400,
                color: selectedModel === model.id ? theme.palette.primary.main : 'inherit'
              }}
              secondaryTypographyProps={{
                fontSize: '0.75rem'
              }}
            />
          </MenuItem>
        ))}
        
        <Divider />
        
        <MenuItem sx={{ display: 'flex', justifyContent: 'space-between', py: 1.5 }}>
          <ListItemIcon>
            <CachedIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText 
            primary="Use response cache" 
            secondary="Faster responses for similar queries"
            secondaryTypographyProps={{
              fontSize: '0.75rem'
            }}
          />
          <Switch 
            size="small"
            checked={useCache}
            onChange={handleCacheToggle}
            color="primary"
            inputProps={{ 'aria-label': 'toggle cache' }}
          />
        </MenuItem>
        
        <Box sx={{ 
          px: 2, 
          py: 1.5, 
          fontSize: '0.75rem', 
          color: theme.palette.text.secondary, 
          display: 'flex', 
          alignItems: 'center',
          bgcolor: theme.palette.mode === 'dark' 
            ? 'rgba(255, 255, 255, 0.03)'
            : 'rgba(0, 0, 0, 0.02)',
        }}>
          <LightbulbIcon fontSize="small" sx={{ mr: 1, fontSize: '1rem', color: theme.palette.warning.main }} />
          <Typography variant="caption">
            Select more powerful models for complex data analysis tasks, or faster models for simple queries.
          </Typography>
        </Box>
      </Menu>
    </Box>
  );
};

export default ModelSelector;