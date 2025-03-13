import React from 'react';
import { Box, TextField, IconButton, CircularProgress, Typography } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';

const MessageInput = ({ value, onChange, onSend, isLoading, suggestedQueries }) => {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <Box>
      {suggestedQueries && suggestedQueries.length > 0 && (
        <Box sx={{ mb: 1 }}>
          <Typography variant="body2" sx={{ color: 'text.secondary', mb: 0.5 }}>
            Suggested: {suggestedQueries.map((query, index) => (
              <React.Fragment key={index}>
                {index > 0 && ' • '}
                <Box 
                  component="span" 
                  sx={{ 
                    cursor: 'pointer', 
                    '&:hover': { textDecoration: 'underline' } 
                  }}
                  onClick={() => onChange({ target: { value: query } })}
                >
                  "{query}"
                </Box>
              </React.Fragment>
            ))}
          </Typography>
        </Box>
      )}
      
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <IconButton sx={{ mr: 1 }}>
          <AttachFileIcon />
        </IconButton>
        
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Do you have a follow up question?"
          value={value}
          onChange={onChange}
          onKeyPress={handleKeyPress}
          multiline
          maxRows={4}
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
              backgroundColor: '#f5f7fa',
            }
          }}
        />
        
        <IconButton 
          sx={{ ml: 1 }}
          color="primary"
          onClick={onSend}
          disabled={isLoading || !value.trim()}
        >
          {isLoading ? <CircularProgress size={24} /> : <SendIcon />}
        </IconButton>
      </Box>
    </Box>
  );
};

export default MessageInput;
