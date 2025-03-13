import React from 'react';
import { Box, Typography, Paper, IconButton, Divider, CircularProgress } from '@mui/material';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import ShareIcon from '@mui/icons-material/Share';
import AnalysisResult from './AnalysisResult';

const ChatMessage = ({ message, isLoading }) => {
  const isUser = message.role === 'user';
  
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2
      }}
    >
      <Paper
        elevation={1}
        sx={{
          p: 2,
          maxWidth: '80%',
          borderRadius: 2,
          bgcolor: isUser ? '#e3f2fd' : '#ffffff',
          position: 'relative'
        }}
      >
        {/* Message content */}
        {isUser ? (
          <Typography variant="body1">
            {message.content}
          </Typography>
        ) : (
          <Typography 
            variant="body1" 
            component="div" 
            sx={{ 
              whiteSpace: 'pre-wrap',
              fontFamily: 'inherit',
              '& p': { mt: 1, mb: 1 },
              '& ul, & ol': { pl: 3 },
              '& li': { mb: 0.5 },
              '& code': {
                backgroundColor: '#f5f5f5',
                padding: '2px 4px',
                borderRadius: '4px',
                fontFamily: 'monospace'
              }
            }}
          >
            {message.content}
          </Typography>
        )}
        
        {/* Loading indicator */}
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        
        {/* Visualization if available */}
        {!isUser && message.visualization && (
          <>
            <Divider sx={{ my: 2 }} />
            <AnalysisResult 
              visualization={message.visualization} 
            />
          </>
        )}
        
        {/* Timestamp */}
        <Typography 
          variant="caption" 
          sx={{ 
            display: 'block', 
            mt: 1, 
            color: 'text.secondary',
            textAlign: 'right'
          }}
        >
          {new Date(message.timestamp).toLocaleTimeString()}
        </Typography>
      </Paper>
      
      {!isUser && !isLoading && (
        <Box sx={{ display: 'flex', mt: 1, ml: 5 }}>
          <IconButton size="small" sx={{ mr: 1 }}>
            <ThumbUpIcon fontSize="small" />
          </IconButton>
          <IconButton size="small" sx={{ mr: 1 }}>
            <ThumbDownIcon fontSize="small" />
          </IconButton>
          <IconButton size="small" sx={{ mr: 1 }}>
            <BookmarkIcon fontSize="small" />
          </IconButton>
          <IconButton size="small">
            <ShareIcon fontSize="small" />
          </IconButton>
        </Box>
      )}
    </Box>
  );
};

export default ChatMessage;
