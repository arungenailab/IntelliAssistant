import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  IconButton, 
  Tooltip, 
  Paper,
  InputAdornment,
  useTheme
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import ModelSelector from './ModelSelector';

const ChatInput = ({ 
  onSendMessage, 
  disabled = false, 
  placeholder = "Ask about your data..."
}) => {
  const [message, setMessage] = useState('');
  const [selectedModel, setSelectedModel] = useState('gemini-2.0-flash');
  const [useCache, setUseCache] = useState(true);
  const inputRef = useRef(null);
  const theme = useTheme();
  
  // Focus input when component mounts
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);
  
  const handleSend = () => {
    if (message.trim()) {
      onSendMessage(message.trim(), selectedModel, useCache);
      setMessage('');
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
  
  const handleModelChange = (modelId) => {
    setSelectedModel(modelId);
  };
  
  const handleCacheToggle = (useCache) => {
    setUseCache(useCache);
  };
  
  return (
    <Paper
      elevation={3}
      sx={{
        p: 1.5,
        borderRadius: 2,
        background: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-end' }}>
        <TextField
          inputRef={inputRef}
          fullWidth
          multiline
          maxRows={5}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          variant="standard"
          disabled={disabled}
          InputProps={{
            disableUnderline: true,
            sx: { 
              fontSize: '1rem',
              p: 1,
              '&.Mui-focused': {
                boxShadow: 'none',
              }
            },
            endAdornment: (
              <InputAdornment position="end">
                <Tooltip title="Attach file">
                  <IconButton 
                    disabled={true}  // Disabled until file upload is implemented
                    sx={{ opacity: 0.6 }}
                  >
                    <AttachFileIcon />
                  </IconButton>
                </Tooltip>
              </InputAdornment>
            )
          }}
        />
        <Tooltip title="Send">
          <IconButton 
            onClick={handleSend} 
            disabled={disabled || !message.trim()}
            color="primary"
            sx={{ 
              ml: 1, 
              bgcolor: message.trim() ? 'primary.main' : 'transparent',
              color: message.trim() ? 'white' : 'primary.main',
              '&:hover': {
                bgcolor: message.trim() ? 'primary.dark' : 'rgba(25, 118, 210, 0.04)',
              },
              transition: 'background-color 0.2s',
            }}
          >
            <SendIcon />
          </IconButton>
        </Tooltip>
      </Box>
      
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        mt: 1, 
        px: 1 
      }}>
        <ModelSelector
          selectedModel={selectedModel}
          useCache={useCache}
          onModelChange={handleModelChange}
          onCacheToggle={handleCacheToggle}
        />
        
        <Box sx={{ 
          fontSize: '0.75rem', 
          color: 'text.secondary',
          opacity: 0.7,
        }}>
          Powered by Google Gemini
        </Box>
      </Box>
    </Paper>
  );
};

export default ChatInput; 