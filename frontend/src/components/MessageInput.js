import React from 'react';
import { Box, TextField, IconButton, Paper } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

const MessageInput = ({ value, onChange, onSubmit, isLoading, placeholder = "Type a message..." }) => {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isLoading) {
        onSubmit();
      }
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        display: 'flex',
        alignItems: 'center',
        p: 1,
        pl: 2,
        borderRadius: 2,
        border: '1px solid rgba(0, 0, 0, 0.1)',
        '&:focus-within': {
          borderColor: 'primary.main',
          boxShadow: '0 0 0 2px rgba(37, 99, 235, 0.15)'
        }
      }}
    >
      <TextField
        fullWidth
        variant="standard"
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        onKeyPress={handleKeyPress}
        disabled={isLoading}
        InputProps={{
          disableUnderline: true,
        }}
        sx={{
          '& .MuiInputBase-input': {
            py: 1,
          }
        }}
      />
      <IconButton 
        color="primary"
        onClick={() => {
          if (value.trim() && !isLoading) {
            onSubmit();
          }
        }}
        disabled={!value.trim() || isLoading}
        sx={{
          bgcolor: value.trim() && !isLoading ? 'primary.main' : 'action.disabledBackground',
          color: value.trim() && !isLoading ? 'white' : 'text.disabled',
          '&:hover': {
            bgcolor: value.trim() && !isLoading ? 'primary.dark' : 'action.disabledBackground',
          },
          '&.Mui-disabled': {
            bgcolor: 'action.disabledBackground',
            color: 'text.disabled',
          },
          width: 36,
          height: 36,
          mr: 0.5
        }}
      >
        <SendIcon fontSize="small" />
      </IconButton>
    </Paper>
  );
};

export default MessageInput;
