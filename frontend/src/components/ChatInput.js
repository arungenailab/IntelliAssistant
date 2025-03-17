import React, { useRef, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  IconButton, 
  CircularProgress,
  InputAdornment,
  useTheme 
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import ModelSelector from './ModelSelector';

const ChatInput = ({ 
  message,
  setMessage,
  handleSend,
  disabled = false, 
  isLoading = false,
  placeholder = "Message IntelliAssistant...",
  selectedModel = 'gemini-2.0-flash',
  onModelChange = () => {},
  useCache = true,
  onCacheToggle = () => {}
}) => {
  const inputRef = useRef(null);
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';
  
  // Focus input when component mounts
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);
  
  const handleSendMessage = () => {
    if (message.trim()) {
      handleSend(message.trim(), selectedModel, useCache);
    }
  };
  
  const handleChange = (e) => {
    setMessage(e.target.value);
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  return (
    <Box
      sx={{
        width: '100%',
        maxWidth: '48rem',
        mx: 'auto',
        p: { xs: 1, sm: 2 },
      }}
    >
      <TextField
        fullWidth
        multiline
        variant="outlined"
        value={message}
        onChange={handleChange}
        onKeyDown={handleKeyPress}
        placeholder={placeholder || "Message IntelliAssistant..."}
        disabled={disabled}
        maxRows={8}
        minRows={1}
        sx={{
          '& .MuiOutlinedInput-root': {
            backgroundColor: theme => theme.palette.mode === 'dark' ? 'rgba(64, 65, 79, 0.9)' : 'white',
            borderRadius: '12px',
            padding: '10px 14px',
            fontSize: '16px',
            lineHeight: 1.5,
            boxShadow: theme => theme.palette.mode === 'dark' 
              ? '0 0 10px rgba(0,0,0,0.1)' 
              : '0 0 10px rgba(0,0,0,0.05)',
            border: theme => `1px solid ${
              theme.palette.mode === 'dark' 
                ? 'rgba(255,255,255,0.1)' 
                : 'rgba(0,0,0,0.1)'
            }`,
            '&.Mui-focused': {
              boxShadow: '0 0 0 2px rgba(0, 166, 126, 0.3)',
              border: '1px solid rgba(0, 166, 126, 0.5)',
            },
            '&:hover': {
              borderColor: theme => 
                theme.palette.mode === 'dark' 
                  ? 'rgba(255,255,255,0.2)' 
                  : 'rgba(0,0,0,0.2)'
            }
          },
          '& .MuiOutlinedInput-notchedOutline': {
            border: 'none',
          },
        }}
        InputProps={{
          endAdornment: (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              {isLoading && (
                <CircularProgress 
                  size={20} 
                  thickness={4}
                  sx={{ 
                    mr: 1,
                    color: message.trim() ? '#10a37f' : 'text.secondary'
                  }} 
                />
              )}
              <IconButton
                onClick={handleSendMessage}
                disabled={disabled || !message.trim()}
                sx={{
                  bgcolor: message.trim() ? '#10a37f' : 'transparent',
                  color: message.trim() ? 'white' : 'text.secondary',
                  '&:hover': {
                    bgcolor: message.trim() ? '#0e906f' : 'rgba(0,0,0,0.04)',
                  },
                  transition: 'all 0.2s ease',
                  p: 1,
                }}
              >
                <SendIcon sx={{ fontSize: '1.2rem' }} />
              </IconButton>
            </Box>
          ),
        }}
      />
      
      <Box 
        sx={{
          display: 'flex', 
          justifyContent: 'flex-end',
          opacity: 0.8,
          mr: 0.5,
          mt: -0.5,
        }}
      >
        <ModelSelector 
          selectedModel={selectedModel} 
          onModelChange={onModelChange}
          useCache={useCache}
          onCacheToggle={onCacheToggle}
          sx={{ 
            '& .MuiFormControl-root': { m: 0 },
            transform: 'scale(0.9)',
            transformOrigin: 'right',
          }}
        />
      </Box>
    </Box>
  );
};

export default ChatInput; 