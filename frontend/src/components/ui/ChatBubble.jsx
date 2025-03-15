import React from 'react';
import { Box, Paper, useTheme } from '@mui/material';

/**
 * A modern chat bubble component with arrow indicators
 * @param {boolean} isUser - Whether the message is from the user
 * @param {React.ReactNode} children - The content to be displayed inside the bubble
 * @param {object} sx - Additional styles to apply to the bubble
 * @returns {JSX.Element}
 */
const ChatBubble = ({ isUser, children, sx = {} }) => {
  const theme = useTheme();
  
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        position: 'relative',
        mb: 1.5,
        maxWidth: '100%',
      }}
    >
      <Paper
        elevation={0}
        sx={{ 
          p: 2, 
          borderRadius: '18px',
          maxWidth: '85%',
          bgcolor: isUser ? 'primary.main' : 'background.paper',
          color: isUser ? 'white' : 'text.primary',
          position: 'relative',
          border: isUser ? 'none' : '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: theme => isUser 
            ? `0 1px 2px 0 ${theme.palette.primary.dark}30` 
            : '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
          
          // Arrow styling for the bubble
          '&::before': {
            content: '""',
            position: 'absolute',
            bottom: 8,
            [isUser ? 'right' : 'left']: -8,
            width: 16,
            height: 16,
            backgroundColor: isUser ? theme.palette.primary.main : theme.palette.background.paper,
            borderBottomLeftRadius: isUser ? 16 : 0,
            borderBottomRightRadius: isUser ? 0 : 16,
            zIndex: 0,
            border: isUser ? 'none' : '1px solid rgba(0, 0, 0, 0.08)',
            borderTop: 'none',
            borderRight: isUser ? 'none' : '1px solid rgba(0, 0, 0, 0.08)',
            borderLeft: isUser ? '1px solid rgba(0, 0, 0, 0.08)' : 'none',
            boxShadow: isUser 
              ? `1px 1px 0 0 ${theme.palette.primary.dark}30` 
              : '1px 1px 0 0 rgba(0, 0, 0, 0.05)',
            transform: 'rotate(45deg)',
            display: { xs: 'none', sm: 'block' }, // Hide on mobile
          },
          
          ...sx
        }}
      >
        {children}
      </Paper>
    </Box>
  );
};

export default ChatBubble; 