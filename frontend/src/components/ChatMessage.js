import React from 'react';
import { Box, Typography, Paper, IconButton, Divider, CircularProgress, Tooltip } from '@mui/material';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import ShareIcon from '@mui/icons-material/Share';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import AnalysisResult from './AnalysisResult';

const ChatMessage = ({ message, isLoading }) => {
  const isUser = message.role === 'user';
  
  const handleCopyContent = () => {
    navigator.clipboard.writeText(message.content);
  };
  
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        mb: 2.5,
        maxWidth: '90%',
        alignSelf: isUser ? 'flex-end' : 'flex-start',
      }}
    >
      {/* Message sender indicator */}
      <Typography 
        variant="caption" 
        sx={{ 
          mb: 0.5, 
          ml: isUser ? 0 : 1.5,
          mr: isUser ? 1.5 : 0,
          color: 'text.secondary',
          fontWeight: 500
        }}
      >
        {isUser ? 'You' : 'Data Analysis Assistant'}
      </Typography>
      
      {/* Message content */}
      <Box sx={{ display: 'flex', position: 'relative' }}>
        {!isUser && (
          <Box
            sx={{
              width: 28,
              height: 28,
              borderRadius: '50%',
              bgcolor: 'primary.main',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mr: 1,
              flexShrink: 0,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 11.5C21.0034 12.8199 20.6951 14.1219 20.1 15.3C19.3944 16.7118 18.3098 17.8992 16.9674 18.7293C15.6251 19.5594 14.0782 19.9994 12.5 20C11.1801 20.0035 9.87812 19.6951 8.7 19.1L3 21L4.9 15.3C4.30493 14.1219 3.99656 12.8199 4 11.5C4.00061 9.92179 4.44061 8.37488 5.27072 7.03258C6.10083 5.69028 7.28825 4.6056 8.7 3.90003C9.87812 3.30496 11.1801 2.99659 12.5 3.00003H13C15.0843 3.11502 17.053 3.99479 18.5291 5.47089C20.0052 6.94699 20.885 8.91568 21 11V11.5Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </Box>
        )}
        
        <Paper
          elevation={0}
          sx={{
            p: 2,
            maxWidth: isUser ? '85%' : '90%',
            borderRadius: 1.5,
            bgcolor: isUser ? 'primary.light' : 'background.paper',
            color: isUser ? 'white' : 'text.primary',
            position: 'relative',
            border: isUser ? 'none' : '1px solid rgba(0, 0, 0, 0.08)',
            boxShadow: 'none',
            ...(message.error && {
              bgcolor: '#ffebee',
              borderColor: '#ffcdd2',
            }),
          }}
        >
          {/* Message content */}
          {isUser ? (
            <Typography variant="body1" sx={{ color: 'white', fontWeight: 500 }}>
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
                  backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  padding: '2px 4px',
                  borderRadius: '4px',
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                },
                '& pre': {
                  backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  padding: '12px',
                  borderRadius: '6px',
                  overflowX: 'auto',
                  '& code': {
                    backgroundColor: 'transparent',
                    padding: 0,
                  }
                },
                '& a': {
                  color: 'primary.main',
                  textDecoration: 'none',
                  '&:hover': {
                    textDecoration: 'underline',
                  }
                },
                '& strong': {
                  fontWeight: 600,
                },
                '& h1, & h2, & h3, & h4, & h5, & h6': {
                  fontWeight: 600,
                  mt: 2,
                  mb: 1,
                },
                '& table': {
                  borderCollapse: 'collapse',
                  width: '100%',
                  my: 2,
                  '& th, & td': {
                    border: '1px solid rgba(0, 0, 0, 0.1)',
                    padding: '8px 12px',
                    textAlign: 'left',
                  },
                  '& th': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    fontWeight: 600,
                  },
                  '& tr:nth-of-type(even)': {
                    backgroundColor: 'rgba(0, 0, 0, 0.02)',
                  }
                }
              }}
            >
              {message.content}
            </Typography>
          )}
          
          {/* Loading indicator */}
          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <CircularProgress size={20} color="primary" />
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
          
          {/* Copy button for assistant messages */}
          {!isUser && !isLoading && (
            <Tooltip title="Copy to clipboard">
              <IconButton 
                size="small" 
                onClick={handleCopyContent}
                sx={{ 
                  position: 'absolute', 
                  top: 8, 
                  right: 8,
                  opacity: 0.4,
                  '&:hover': {
                    opacity: 0.8,
                    bgcolor: 'rgba(0, 0, 0, 0.04)',
                  }
                }}
              >
                <ContentCopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          
          {/* Timestamp */}
          <Typography 
            variant="caption" 
            sx={{ 
              display: 'block', 
              mt: 1, 
              color: isUser ? 'rgba(255, 255, 255, 0.8)' : 'text.secondary',
              textAlign: 'right',
              fontSize: '0.7rem',
            }}
          >
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Typography>
        </Paper>
      </Box>
      
      {/* Feedback buttons for assistant messages - simplified */}
      {!isUser && !isLoading && (
        <Box sx={{ 
          display: 'flex', 
          mt: 0.5, 
          ml: 4.5,
          gap: 0.5,
        }}>
          <Tooltip title="Helpful">
            <IconButton 
              size="small" 
              sx={{ 
                color: 'text.secondary',
                opacity: 0.6,
                '&:hover': { 
                  color: 'success.main',
                  opacity: 1,
                }
              }}
            >
              <ThumbUpIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Not helpful">
            <IconButton 
              size="small" 
              sx={{ 
                color: 'text.secondary',
                opacity: 0.6,
                '&:hover': { 
                  color: 'error.main',
                  opacity: 1,
                }
              }}
            >
              <ThumbDownIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Save">
            <IconButton 
              size="small" 
              sx={{ 
                color: 'text.secondary',
                opacity: 0.6,
                '&:hover': { 
                  color: 'primary.main',
                  opacity: 1,
                }
              }}
            >
              <BookmarkIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Share">
            <IconButton 
              size="small" 
              sx={{ 
                color: 'text.secondary',
                opacity: 0.6,
                '&:hover': { 
                  color: 'primary.main',
                  opacity: 1,
                }
              }}
            >
              <ShareIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      )}
    </Box>
  );
};

export default ChatMessage;
