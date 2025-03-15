import React from 'react';
import { Box, Typography, IconButton, CircularProgress, Tooltip, Fade } from '@mui/material';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import AnalysisResult from './AnalysisResult';
import ChatBubble from './ui/ChatBubble';
import CodeBlock from './ui/CodeBlock';
import SQLQueryVisualizer from './SQLQueryVisualizer';

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

  return (
    <Fade in={true} timeout={400}>
      <Box sx={{ mb: 2 }}>
        <Box 
          sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            px: 0.5, 
            mb: 0.25,
            alignItems: 'center'
          }}
        >
          <Typography
            variant="caption"
            sx={{
              color: (theme) => theme.palette.text.secondary,
              fontSize: '0.7rem',
              fontWeight: 500,
              ml: isUser ? 'auto' : '0',
              mr: isUser ? '0' : 'auto',
            }}
          >
            {isUser ? 'You' : 'IntelliAssistant'}
            {message.timestamp && (
              <Typography 
                component="span" 
                sx={{ 
                  fontSize: '0.65rem',
                  color: (theme) => theme.palette.text.secondary,
                  opacity: 0.6,
                  ml: 0.75,
                }}
              >
                {formatTimestamp(message.timestamp)}
              </Typography>
            )}
          </Typography>
          
          {!isLoading && message.content && (
            <Tooltip title="Copy message">
              <IconButton 
                size="small" 
                onClick={handleCopyContent}
                sx={{ 
                  color: (theme) => theme.palette.text.secondary,
                  padding: 0.3,
                  fontSize: '0.7rem',
                }}
              >
                <ContentCopyIcon fontSize="inherit" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
        
        <ChatBubble isUser={isUser}>
          {isLoading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', p: 0.5 }}>
              <CircularProgress size={18} thickness={4} color={isUser ? "secondary" : "primary"} />
            </Box>
          ) : (
            <Box>
              {textContent.split('\n').map((paragraph, index) => {
                if (paragraph.includes('[CODE_BLOCK_')) {
                  // Replace code block placeholder with actual code block
                  const codeBlockIndexMatch = paragraph.match(/\[CODE_BLOCK_(\d+)\]/);
                  if (codeBlockIndexMatch) {
                    const codeBlockIndex = parseInt(codeBlockIndexMatch[1]);
                    const codeBlock = codeBlocks[codeBlockIndex];
                    return (
                      <Box key={`code-${index}`} sx={{ my: 1 }}>
                        <CodeBlock 
                          language={codeBlock.language}
                          code={codeBlock.code}
                        />
                      </Box>
                    );
                  }
                }
                return paragraph ? (
                  <Typography
                    key={index}
                    variant="body2"
                    component="p"
                    sx={{
                      my: paragraph.trim() === '' ? 0.5 : 0,
                      lineHeight: 1.5,
                      fontSize: '0.9rem',
                    }}
                  >
                    {paragraph}
                  </Typography>
                ) : (
                  <Box key={index} sx={{ height: '0.5rem' }} />
                );
              })}
              
              {sqlQuery && (
                <Box sx={{ mt: 1.5 }}>
                  <SQLQueryVisualizer query={sqlQuery} />
                </Box>
              )}
              
              {message.analysis_result && (
                <Box sx={{ mt: 1.5 }}>
                  <AnalysisResult result={message.analysis_result} />
                </Box>
              )}
            </Box>
          )}
        </ChatBubble>
        
        {!isLoading && !isUser && (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-start',
              mt: 0.25,
              ml: 5,
              gap: 0.5,
            }}
          >
            <Tooltip title="Like">
              <IconButton
                size="small"
                sx={{
                  color: (theme) => theme.palette.text.secondary,
                  p: 0.3,
                  '&:hover': {
                    color: (theme) => theme.palette.primary.main,
                  },
                }}
              >
                <ThumbUpIcon sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
            <Tooltip title="Dislike">
              <IconButton
                size="small"
                sx={{
                  color: (theme) => theme.palette.text.secondary,
                  p: 0.3,
                  '&:hover': {
                    color: (theme) => theme.palette.error.main,
                  },
                }}
              >
                <ThumbDownIcon sx={{ fontSize: 16 }} />
              </IconButton>
            </Tooltip>
          </Box>
        )}
        
        {hasModelInfo && (
          <Typography
            variant="caption"
            sx={{
              color: (theme) => theme.palette.text.secondary,
              opacity: 0.5,
              fontSize: '0.65rem',
              display: 'block',
              mt: 0.25,
              ml: 5,
            }}
          >
            {isFallback ? 'Fallback model: ' : 'Model: '}{message.model_used}
            {message.model_version && ` (${message.model_version})`}
          </Typography>
        )}
      </Box>
    </Fade>
  );
};

export default ChatMessage;
