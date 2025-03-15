import React, { useState } from 'react';
import { Box, Typography, IconButton, Divider, CircularProgress, Tooltip } from '@mui/material';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import ShareIcon from '@mui/icons-material/Share';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import AnalysisResult from './AnalysisResult';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import SQLQueryVisualizer from './SQLQueryVisualizer';
import ChatBubble from './ui/ChatBubble';
import CodeBlock from './ui/CodeBlock';

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

// Helper function to extract code blocks from message content
const extractCodeBlocks = (content) => {
  if (!content) return { textContent: '', codeBlocks: [] };
  
  // Regular expression to match code blocks with language (```sql, ```js, etc.)
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
  const codeBlocks = [];
  let match;
  let textContent = content;
  
  // Find all code blocks
  while ((match = codeBlockRegex.exec(content)) !== null) {
    const language = match[1] || 'text';
    const code = match[2];
    const fullMatch = match[0];
    const startIndex = match.index;
    const endIndex = startIndex + fullMatch.length;
    
    codeBlocks.push({
      language,
      code,
      startIndex,
      endIndex
    });
    
    // Replace code block with placeholder
    textContent = textContent.replace(fullMatch, `[CODE_BLOCK_${codeBlocks.length - 1}]`);
  }
  
  return { textContent, codeBlocks };
};

// Helper function to detect and format SQL queries
const formatSQLQuery = (content) => {
  if (!content) return { content, sqlQuery: null };
  
  // Check if the message contains an SQL query
  const sqlRegex = /SELECT[\s\S]*?FROM[\s\S]*?(?:WHERE|GROUP BY|ORDER BY|LIMIT|;|$)/i;
  const match = content.match(sqlRegex);
  
  if (match) {
    const sqlQuery = match[0];
    return { content, sqlQuery };
  }
  
  return { content, sqlQuery: null };
};

const ChatMessage = ({ message, isLoading }) => {
  const isUser = message.role === 'user';
  const isError = message.error;
  const [showFeedback, setShowFeedback] = useState(false);
  
  // Check if model information is available
  const hasModelInfo = message.model_used && message.model_version;
  const isFallback = message.is_fallback;
  
  // Extract code blocks from message content
  const { textContent, codeBlocks } = extractCodeBlocks(message.content);
  
  // Check if the message contains an SQL query
  const { sqlQuery } = formatSQLQuery(message.content);
  
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
  
  // Render content with code blocks replaced by CodeBlock components
  const renderContentWithCodeBlocks = () => {
    if (codeBlocks.length === 0) {
      return (
        <Typography 
          variant="body1" 
          component="div"
          sx={{ 
            whiteSpace: 'pre-wrap',
            fontFamily: 'inherit',
            '& p': { mt: 1, mb: 1 },
            '& ul, & ol': { pl: 3 },
            '& li': { mb: 0.5 },
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
      );
    }
    
    const parts = textContent.split(/\[CODE_BLOCK_(\d+)\]/);
    
    return (
      <React.Fragment>
        {parts.map((part, index) => {
          // Even indices are text content
          if (index % 2 === 0) {
            return part ? (
              <Typography 
                key={`text-${index}`}
                variant="body1" 
                component="div"
                sx={{ 
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'inherit',
                  mt: index === 0 ? 0 : 1,
                  mb: 1,
                  '& p': { mt: 1, mb: 1 },
                  '& ul, & ol': { pl: 3 },
                  '& li': { mb: 0.5 },
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
                  }
                }}
              >
                {part}
              </Typography>
            ) : null;
          }
          
          // Odd indices correspond to code block placeholders
          const blockIndex = parseInt(part, 10);
          const block = codeBlocks[blockIndex];
          
          if (!block) return null;
          
          return (
            <CodeBlock
              key={`code-${index}`}
              language={block.language}
              code={block.code}
              showLineNumbers={true}
            />
          );
        })}
      </React.Fragment>
    );
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        mb: 2.5,
        maxWidth: '100%',
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
      <Box sx={{ display: 'flex', position: 'relative', maxWidth: '100%', width: '100%' }}>
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
              alignSelf: 'flex-start',
            }}
          >
            <SmartToyIcon sx={{ fontSize: 16, color: 'white' }} />
          </Box>
        )}
        
        <Box sx={{ 
          maxWidth: isUser ? '85%' : 'calc(100% - 40px)',
          width: isUser ? 'auto' : '100%'
        }}>
          <ChatBubble 
            isUser={isUser}
            sx={{
              ...(message.error && {
                bgcolor: '#ffebee',
                borderColor: '#ffcdd2',
              }),
            }}
          >
            {/* Message content with code blocks */}
            {isUser ? (
              <Typography variant="body1" sx={{ color: 'white', fontWeight: 500 }}>
                {message.content}
              </Typography>
            ) : (
              renderContentWithCodeBlocks()
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
          </ChatBubble>
          
          {/* SQL Query Visualizer - only shown for assistant messages with SQL */}
          {!isUser && sqlQuery && !isLoading && (
            <Box sx={{ mt: 2, width: '100%' }}>
              <SQLQueryVisualizer 
                query={sqlQuery}
                results={message.query_results}
                visualization={message.visualization}
              />
            </Box>
          )}
          
          {/* Visualization if available but no SQL */}
          {!isUser && !sqlQuery && message.visualization && !isLoading && (
            <Box sx={{ mt: 2, width: '100%' }}>
              <Box sx={{ p: 2, border: '1px solid rgba(0, 0, 0, 0.08)', borderRadius: '8px' }}>
                <AnalysisResult visualization={message.visualization} />
              </Box>
            </Box>
          )}
        </Box>
      </Box>
      
      {/* Feedback buttons for assistant messages - simplified */}
      {!isUser && !isLoading && (
        <Box sx={{ 
          display: 'flex', 
          mt: 0.5, 
          ml: 4.5,
          opacity: showFeedback ? 1 : 0,
          transition: 'opacity 0.2s',
          '&:hover': {
            opacity: 1
          }
        }}>
          <Tooltip title="This was helpful">
            <IconButton size="small" sx={{ mr: 1 }}>
              <ThumbUpIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="This was not helpful">
            <IconButton size="small" sx={{ mr: 1 }}>
              <ThumbDownIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Save this response">
            <IconButton size="small" sx={{ mr: 1 }}>
              <BookmarkIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Share this response">
            <IconButton size="small">
              <ShareIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      )}
    </Box>
  );
};

export default ChatMessage;
