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
  placeholder = "Ask IntelliAssistant anything...",
  selectedModel = 'gemini-2.0-flash',
  onModelChange = () => {},
  useCache = true,
  onCacheToggle = () => {}
}) => {
  const inputRef = useRef(null);
  const theme = useTheme();
  
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
        maxWidth: '1000px',
        mx: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
      }}
    >
      <TextField
        inputRef={inputRef}
        fullWidth
        multiline
        maxRows={4}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={placeholder}
        variant="outlined"
        disabled={disabled || isLoading}
        sx={{
          '& .MuiOutlinedInput-root': {
            backgroundColor: theme.palette.background.paper,
            borderRadius: 2,
            boxShadow: theme.palette.mode === 'dark' 
              ? '0px 1px 4px rgba(0, 0, 0, 0.2)' 
              : '0px 1px 3px rgba(0, 0, 0, 0.05)',
            transition: 'all 0.2s',
            '&.Mui-focused': {
              boxShadow: `0 0 0 2px ${theme.palette.primary.main}30`,
            },
            '&:hover': {
              borderColor: theme.palette.primary.main,
            },
          },
        }}
        InputProps={{
          sx: { 
            fontSize: '0.95rem',
            p: 1,
          },
          endAdornment: (
            <InputAdornment position="end">
              {isLoading ? (
                <CircularProgress size={24} color="primary" thickness={4} />
              ) : (
                <IconButton
                  onClick={handleSendMessage}
                  disabled={!message.trim() || disabled}
                  color="primary"
                  sx={{
                    ml: 0.5,
                    bgcolor: message.trim() 
                      ? theme.palette.primary.main 
                      : theme.palette.action.disabledBackground,
                    color: message.trim() 
                      ? theme.palette.primary.contrastText 
                      : theme.palette.text.disabled,
                    '&:hover': {
                      bgcolor: message.trim() 
                        ? theme.palette.primary.dark 
                        : theme.palette.action.disabledBackground,
                    },
                    width: 36,
                    height: 36,
                    transition: 'all 0.2s',
                  }}
                >
                  <SendIcon fontSize="small" />
                </IconButton>
              )}
            </InputAdornment>
          ),
        }}
      />
      
      <Box 
        sx={{
          display: 'flex', 
          justifyContent: 'flex-end',
          opacity: 0.8,
          mr: 0.5,
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