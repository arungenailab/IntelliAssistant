import React from 'react';
import { Box, Paper, Avatar, useTheme } from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';

/**
 * A modern chat bubble component following the specified requirements
 * @param {boolean} isUser - Whether the message is from the user
 * @param {React.ReactNode} children - The content to be displayed inside the bubble
 * @param {object} sx - Additional styles to apply to the bubble
 * @returns {JSX.Element}
 */
const ChatBubble = ({ isUser, children, sx = {} }) => {
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';
  
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
        gap: 1,
        mb: 1.5,
        width: '100%',
        maxWidth: '100%',
      }}
    >
      {/* Avatar */}
      <Avatar
        sx={{
          bgcolor: isUser ? 'secondary.main' : 'primary.main',
          width: 34,
          height: 34,
          mt: 1,
          boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)',
          opacity: 0.9,
        }}
      >
        {isUser ? <PersonIcon sx={{ fontSize: 18 }} /> : <SmartToyIcon sx={{ fontSize: 18 }} />}
      </Avatar>
      
      {/* Message Bubble */}
      <Paper
        elevation={1}
        sx={{
          p: 1.5,
          borderRadius: 2,
          maxWidth: { xs: '85%', sm: '75%', md: '70%' },
          bgcolor: isUser 
            ? isDarkMode ? 'rgba(245, 245, 245, 0.08)' : '#f5f5f5' 
            : isDarkMode ? 'rgba(227, 242, 253, 0.12)' : '#e3f2fd',
          color: theme.palette.text.primary,
          boxShadow: isDarkMode 
            ? '0 1px 3px rgba(0, 0, 0, 0.25)' 
            : '0 1px 2px rgba(0, 0, 0, 0.1)',
          ...sx
        }}
      >
        {children}
      </Paper>
    </Box>
  );
};

export default ChatBubble; 