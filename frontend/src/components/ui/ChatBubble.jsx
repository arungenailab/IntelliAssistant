import React from 'react';
import { Box, Avatar } from '@mui/material';
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import PersonOutlineOutlinedIcon from '@mui/icons-material/PersonOutlineOutlined';
import { useTheme } from '../../contexts/ThemeContext';

/**
 * A ChatGPT-inspired chat bubble component
 * 
 * @param {Object} props
 * @param {boolean} props.isUser - Whether the message is from the user
 * @param {ReactNode} props.children - The content of the chat bubble
 */
const ChatBubble = ({ isUser, children }) => {
  const { isDarkMode } = useTheme();
  
  // Define colors based on theme
  const userBgColor = isDarkMode ? 'hsl(210, 10%, 15%)' : 'hsl(0, 0%, 95%)';
  const assistantBgColor = isDarkMode ? 'transparent' : 'transparent';
  
  // Message classes for styling
  const messageClass = isUser ? 'user-message' : 'assistant-message';

  return (
    <Box
      className={messageClass}
      sx={{
        display: 'flex',
        width: '100%',
        py: { xs: 2, sm: 3 },
        px: { xs: 1, sm: 2 },
        bgcolor: isUser ? userBgColor : assistantBgColor,
        color: 'text.primary',
        transition: 'background-color 0.2s ease',
      }}
    >
      <Box sx={{ mr: 3, pt: 0.5 }}>
        <Avatar
          sx={{
            bgcolor: isUser 
              ? (isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)')
              : (isDarkMode ? '#10a37f' : '#10a37f'),
            width: 36,
            height: 36,
            color: isUser 
              ? 'text.primary' 
              : '#ffffff',
            boxShadow: isUser ? 'none' : '0 2px 6px rgba(0,0,0,0.15)',
          }}
        >
          {isUser ? (
            <PersonOutlineOutlinedIcon 
              sx={{ 
                fontSize: '1.3rem',
                color: isDarkMode ? 'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.7)',
              }} 
            />
          ) : (
            <SmartToyOutlinedIcon sx={{ fontSize: '1.3rem' }} />
          )}
        </Avatar>
      </Box>

      <Box sx={{ 
        flex: 1, 
        maxWidth: 'calc(100% - 60px)', 
        wordBreak: 'break-word',
        fontSize: '1rem',
        lineHeight: 1.6,
      }}>
        {children}
      </Box>
    </Box>
  );
};

export default ChatBubble; 