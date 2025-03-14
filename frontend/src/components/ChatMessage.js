import React from 'react';
import { Box, Typography, Paper, IconButton, Divider, CircularProgress, Tooltip, Avatar } from '@mui/material';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import ShareIcon from '@mui/icons-material/Share';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import AnalysisResult from './AnalysisResult';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';

// Helper function to format message content
const formatMessage = (content) => {
  if (!content) return '';
  return content;
};

// Helper function to format timestamps
const formatTimestamp = (timestamp) => {
  if (!timestamp) return '';
  
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch (e) {
    return '';
  }
};

// Helper function to render visualizations
const renderVisualization = (visualization) => {
  if (!visualization) return null;
  
  return (
    <Box sx={{ width: '100%', maxWidth: '800px' }}>
      <AnalysisResult visualization={visualization} />
    </Box>
  );
};

const ChatMessage = ({ message, isLoading }) => {
  const isUser = message.role === 'user';
  const isError = message.error;
  
  // Check if model information is available
  const hasModelInfo = message.model_used && message.model_version;
  const isFallback = message.is_fallback;
  
  const handleCopyContent = () => {
    if (message.content) {
      navigator.clipboard.writeText(message.content)
        .then(() => {
          console.log('Content copied to clipboard');
        })
        .catch(err => {
          console.error('Failed to copy: ', err);
        });
    }
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
            <SmartToyIcon sx={{ fontSize: 16, color: 'white' }} />
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
              {formatMessage(message.content)}
            </Typography>
          )}
          
          {/* Model information display for AI messages */}
          {!isUser && hasModelInfo && (
            <Box 
              sx={{
                display: 'flex',
                alignItems: 'center',
                mt: 1.5,
                pt: 1,
                borderTop: theme => `1px solid ${theme.palette.divider}`,
                opacity: 0.7,
                fontSize: '0.75rem',
                color: 'text.secondary'
              }}
            >
              <SmartToyIcon sx={{ fontSize: '0.875rem', mr: 0.5 }} />
              <Typography variant="caption">
                {`Model: ${message.model_used} (v${message.model_version})`}
                {isFallback && (
                  <Typography 
                    component="span" 
                    variant="caption" 
                    sx={{ 
                      ml: 1, 
                      color: 'warning.main',
                      bgcolor: 'warning.light',
                      px: 0.5,
                      py: 0.1,
                      borderRadius: 0.5,
                      fontWeight: 500
                    }}
                  >
                    Fallback
                  </Typography>
                )}
              </Typography>
            </Box>
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
              <Box sx={{ width: '100%' }}>
                <AnalysisResult 
                  visualization={message.visualization} 
                />
              </Box>
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
            {formatTimestamp(message.timestamp)}
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
