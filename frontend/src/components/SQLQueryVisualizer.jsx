import React from 'react';
import { Box, Typography, IconButton, Tooltip, useTheme } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CodeBlock from './ui/CodeBlock';

/**
 * A component that visualizes SQL queries with syntax highlighting and a clean modern design
 * @param {string} query - The SQL query to visualize
 * @param {object} results - Optional query results
 * @param {object} visualization - Optional visualization data
 * @returns {JSX.Element}
 */
const SQLQueryVisualizer = ({ query, results, visualization }) => {
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';
  
  const handleCopy = () => {
    navigator.clipboard.writeText(query)
      .then(() => {
        console.log('SQL query copied to clipboard');
      })
      .catch(err => {
        console.error('Failed to copy: ', err);
      });
  };
  
  const formattedQuery = formatSQLQuery(query);
  
  return (
    <Box
      sx={{
        borderRadius: theme.shape.borderRadius,
        border: `1px solid ${theme.palette.divider}`,
        overflow: 'hidden',
        mb: 2,
        mt: 2,
        bgcolor: theme.palette.background.paper,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          px: 2,
          py: 1.5,
          borderBottom: `1px solid ${theme.palette.divider}`,
          bgcolor: isDarkMode ? 'rgba(25, 118, 210, 0.08)' : 'rgba(25, 118, 210, 0.04)',
        }}
      >
        <Typography
          variant="subtitle2"
          sx={{
            fontWeight: 500,
            fontSize: '0.875rem',
            display: 'flex',
            alignItems: 'center',
            color: theme.palette.primary.main,
          }}
        >
          SQL Query
          <Box 
            component="span" 
            sx={{ 
              ml: 1,
              px: 1,
              py: 0.25,
              borderRadius: theme.shape.borderRadius,
              fontSize: '0.675rem',
              fontWeight: 500,
              bgcolor: theme.palette.primary.main,
              color: 'white',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Executed
          </Box>
        </Typography>
        
        <Tooltip title="Copy SQL Query">
          <IconButton
            size="small"
            onClick={handleCopy}
            sx={{
              color: theme.palette.text.secondary,
              '&:hover': {
                color: theme.palette.primary.main,
              },
            }}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      
      <Box sx={{ p: 0 }}>
        <CodeBlock 
          language="sql" 
          code={formattedQuery} 
          showLineNumbers={true} 
        />
      </Box>
      
      {results && (
        <Box
          sx={{
            p: 2,
            borderTop: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 500, mb: 1, color: theme.palette.text.secondary }}
          >
            Results:
          </Typography>
          <Box
            sx={{
              maxHeight: '200px',
              overflow: 'auto',
              fontSize: '0.875rem',
              bgcolor: theme.palette.background.default,
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: theme.shape.borderRadius,
              p: 1.5,
            }}
          >
            <pre
              style={{
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                fontSize: '0.8rem',
                fontFamily: '"Roboto Mono", monospace',
                color: theme.palette.text.primary,
              }}
            >
              {typeof results === 'string' ? results : JSON.stringify(results, null, 2)}
            </pre>
          </Box>
        </Box>
      )}
      
      {visualization && (
        <Box
          sx={{
            p: 2,
            borderTop: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Typography
            variant="subtitle2"
            sx={{ fontWeight: 500, mb: 1, color: theme.palette.text.secondary }}
          >
            Visualization:
          </Typography>
          
          <Box
            sx={{
              width: '100%',
              minHeight: '300px',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              position: 'relative',
              bgcolor: theme.palette.background.default,
              borderRadius: theme.shape.borderRadius,
              border: `1px solid ${theme.palette.divider}`,
              p: 2,
            }}
          >
            {/* Visualization content would go here */}
            <div id="visualization-container"></div>
          </Box>
        </Box>
      )}
    </Box>
  );
};

// Helper function to format SQL query for better readability
const formatSQLQuery = (query) => {
  if (!query) return '';
  
  // Simple SQL formatting - could be replaced with a more sophisticated formatter
  return query
    .replace(/\s+/g, ' ')
    .replace(/\s*,\s*/g, ', ')
    .replace(/\s*=\s*/g, ' = ')
    .replace(/\s*>\s*/g, ' > ')
    .replace(/\s*<\s*/g, ' < ')
    .replace(/\s*SELECT\s+/ig, 'SELECT\n  ')
    .replace(/\s*FROM\s+/ig, '\nFROM\n  ')
    .replace(/\s*WHERE\s+/ig, '\nWHERE\n  ')
    .replace(/\s*GROUP BY\s+/ig, '\nGROUP BY\n  ')
    .replace(/\s*HAVING\s+/ig, '\nHAVING\n  ')
    .replace(/\s*ORDER BY\s+/ig, '\nORDER BY\n  ')
    .replace(/\s*LIMIT\s+/ig, '\nLIMIT\n  ')
    .replace(/\s*AND\s+/ig, '\n  AND ')
    .replace(/\s*OR\s+/ig, '\n  OR ')
    .replace(/\s*JOIN\s+/ig, '\nJOIN\n  ')
    .replace(/\s*LEFT JOIN\s+/ig, '\nLEFT JOIN\n  ')
    .replace(/\s*RIGHT JOIN\s+/ig, '\nRIGHT JOIN\n  ')
    .replace(/\s*INNER JOIN\s+/ig, '\nINNER JOIN\n  ')
    .replace(/\s*OUTER JOIN\s+/ig, '\nOUTER JOIN\n  ')
    .replace(/\s*ON\s+/ig, '\n  ON ');
};

export default SQLQueryVisualizer; 