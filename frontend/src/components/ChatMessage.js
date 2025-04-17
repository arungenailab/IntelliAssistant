import React from 'react';
import { Box, Typography, IconButton, CircularProgress, Tooltip, Fade } from '@mui/material';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import AnalysisResult from './AnalysisResult';
import ChatBubble from './ui/ChatBubble';
import CodeBlock from './ui/CodeBlock';
import DataVisualization from './DataVisualization';
import SQLResultView from './SQLResultView';

// Try to import SQLQueryVisualizer, but don't fail if it's missing
let SQLQueryVisualizer;
try {
  SQLQueryVisualizer = require('./SQLQueryVisualizer').default;
} catch (error) {
  console.warn('SQLQueryVisualizer component could not be loaded:', error);
  SQLQueryVisualizer = null;
}

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

const ChatMessage = ({ message, isUser, isLoading, onSqlQuery }) => {
  // Only calculate isUser internally if it's not provided as a prop
  const messageIsUser = isUser !== undefined ? isUser : message.role === 'user';
  
  // Check if model information is available
  const hasModelInfo = message.model_used && message.model_version;
  const isFallback = message.is_fallback;
  
  // Check if this is an SQL result view marker
  const isDisplayingSQL = !messageIsUser && message.content === '__SQL_RESULT_VIEW__' && message.sql_result;
  
  // Extract code blocks from message content
  const { textContent, codeBlocks } = !isDisplayingSQL ? extractCodeBlocks(message.content) : { textContent: '', codeBlocks: [] };
  
  // Check if the message contains an SQL query
  const { sqlQuery } = !isDisplayingSQL ? formatSQLQuery(message.content) : { sqlQuery: null };
  
  // Call onSqlQuery if sqlQuery exists and onSqlQuery is provided
  React.useEffect(() => {
    if (sqlQuery && onSqlQuery && typeof onSqlQuery === 'function') {
      onSqlQuery(sqlQuery);
    }
  }, [sqlQuery, onSqlQuery]);
  
  // Custom renderer for code blocks within ReactMarkdown
  const components = {
    code: ({node, inline, className, children, ...props}) => {
      const match = /language-(\w+)/.exec(className || '');
      const language = match && match[1] ? match[1] : '';
      
      if (!inline && language) {
        return (
          <CodeBlock 
            language={language}
            code={String(children).replace(/\n$/, '')}
          />
        );
      }
      
      // For inline code
      return (
        <code className={className} {...props}>
          {children}
        </code>
      );
    }
  };
  
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
    <Fade in={true} timeout={400} className="fade-in">
      <Box sx={{ mb: 0, width: '100%' }}>
        <ChatBubble isUser={messageIsUser}>
          {isLoading ? (
            <Box sx={{ display: 'flex', alignItems: 'center', minHeight: '20px' }}>
              <CircularProgress size={16} thickness={4} color={messageIsUser ? "secondary" : "primary"} />
            </Box>
          ) : (
            <Box>
              {/* If this is specifically a SQL Result View */}
              {isDisplayingSQL ? (
                <Box sx={{ mt: 0 }}>
                  <SQLResultView 
                    sql={message.sql_result.sql}
                    explanation={message.sql_result.explanation}
                    results={message.sql_result.results}
                    error={message.sql_result.error}
                    confidence={message.sql_result.results && message.sql_result.results.length > 0 ? 0.9 : message.sql_result.confidence}
                    visualization={message.sql_result.visualization}
                    compact={true}
                  />
                </Box>
              ) : (
                <Box sx={{
                  '& p': { my: 1, lineHeight: 1.6 },
                  '& strong, & b': { fontWeight: 600 },
                  '& ul, & ol': { pl: 2, my: 1 },
                  '& li': { mb: 0.5 },
                  '& h1, & h2, & h3, & h4, & h5, & h6': { mt: 2, mb: 1, fontWeight: 600 },
                  '& a': { color: 'primary.main', textDecoration: 'underline' },
                  '& blockquote': { 
                    borderLeft: '3px solid', 
                    borderColor: 'divider',
                    pl: 1.5, 
                    py: 0.5, 
                    my: 1,
                    fontStyle: 'italic'
                  },
                  '& hr': { 
                    border: 'none', 
                    height: '1px', 
                    bgcolor: 'divider', 
                    my: 2 
                  },
                  '& table': {
                    borderCollapse: 'collapse',
                    width: '100%',
                    my: 2
                  },
                  '& th, & td': {
                    border: '1px solid',
                    borderColor: 'divider',
                    p: 1
                  },
                  '& th': {
                    bgcolor: 'background.paper',
                    fontWeight: 600
                  }
                }}>
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]} 
                    rehypePlugins={[rehypeRaw]}
                    components={components}
                  >
                    {message.content || ''}
                  </ReactMarkdown>
                </Box>
              )}
              
              {sqlQuery && SQLQueryVisualizer && (
                <Box sx={{ mt: 2 }}>
                  <SQLQueryVisualizer query={sqlQuery} />
                </Box>
              )}
              
              {/* SQL Results Section - only show if not already displaying as main content */}
              {message.sql_result && !isDisplayingSQL && (
                <Box sx={{ mt: 2 }}>
                  <SQLResultView 
                    sql={message.sql_result.sql}
                    explanation={message.sql_result.explanation}
                    results={message.sql_result.results}
                    error={message.sql_result.error}
                    confidence={message.sql_result.results && message.sql_result.results.length > 0 ? 0.9 : message.sql_result.confidence}
                    visualization={message.sql_result.visualization}
                    compact={true}
                  />
                </Box>
              )}
              
              {message.visualization && (
                <Box sx={{ mt: 2 }}>
                  <DataVisualization data={message.visualization} />
                </Box>
              )}
              
              {message.analysis_result && (
                <Box sx={{ mt: 2 }}>
                  <AnalysisResult result={message.analysis_result} />
                </Box>
              )}
              
              {/* Message timestamp and actions in assistant messages */}
              {!messageIsUser && (
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'flex-start', 
                  alignItems: 'center',
                  mt: 2,
                  pt: 1,
                  opacity: 0.7,
                  borderTop: theme => `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)'}`
                }}>
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      fontSize: '0.7rem', 
                      mr: 1,
                      color: theme => theme.palette.text.secondary
                    }}
                  >
                    {message.timestamp && formatTimestamp(message.timestamp)}
                  </Typography>
                  
                  <Tooltip title="Copy message">
                    <IconButton 
                      size="small" 
                      onClick={handleCopyContent}
                      sx={{ 
                        color: theme => theme.palette.text.secondary,
                        padding: 0.3,
                        fontSize: '0.75rem',
                      }}
                    >
                      <ContentCopyIcon fontSize="inherit" />
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title="Like">
                    <IconButton
                      size="small"
                      sx={{
                        color: theme => theme.palette.text.secondary,
                        p: 0.3,
                        ml: 0.5,
                        '&:hover': {
                          color: theme => theme.palette.primary.main,
                        },
                      }}
                    >
                      <ThumbUpIcon sx={{ fontSize: 14 }} />
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title="Dislike">
                    <IconButton
                      size="small"
                      sx={{
                        color: theme => theme.palette.text.secondary,
                        p: 0.3,
                        '&:hover': {
                          color: theme => theme.palette.error.main,
                        },
                      }}
                    >
                      <ThumbDownIcon sx={{ fontSize: 14 }} />
                    </IconButton>
                  </Tooltip>
                </Box>
              )}
            </Box>
          )}
        </ChatBubble>
      </Box>
    </Fade>
  );
};

export default ChatMessage;
