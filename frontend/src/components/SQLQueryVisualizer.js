import React, { useState } from 'react';
import { Box, Typography, Paper, Divider, IconButton, Tooltip } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CodeBlock from './ui/CodeBlock';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

/**
 * SQLQueryVisualizer component
 * Displays and visualizes SQL queries with highlighted syntax
 * and a simple diagram showing tables and relations
 */
const SQLQueryVisualizer = ({ query }) => {
  const [copied, setCopied] = useState(false);
  const [showInfo, setShowInfo] = useState(false);

  // Parse the SQL query to extract tables and fields
  const extractTablesAndFields = (query) => {
    if (!query) return { tables: [], fields: [] };
    
    // Simplified SQL parser - in a real app you might want to use a proper SQL parser library
    const tables = [];
    const fields = [];
    
    // Extract tables from FROM clause
    const fromRegex = /FROM\s+([^\s,;()]+)/i;
    const fromMatch = query.match(fromRegex);
    if (fromMatch && fromMatch[1]) {
      tables.push(fromMatch[1]);
    }
    
    // Extract tables from JOIN clauses
    const joinRegex = /JOIN\s+([^\s,;()]+)/gi;
    let joinMatch;
    while ((joinMatch = joinRegex.exec(query)) !== null) {
      if (joinMatch[1] && !tables.includes(joinMatch[1])) {
        tables.push(joinMatch[1]);
      }
    }
    
    // Extract fields from SELECT clause
    const selectRegex = /SELECT\s+(.*?)\s+FROM/is;
    const selectMatch = query.match(selectRegex);
    if (selectMatch && selectMatch[1]) {
      const fieldsList = selectMatch[1].split(',').map(f => f.trim());
      fieldsList.forEach(field => {
        if (field !== '*') {
          // Remove any aliases or functions
          const cleanField = field.split(' AS ')[0].trim().split('(').pop().replace(')', '');
          fields.push(cleanField);
        } else {
          fields.push('*');
        }
      });
    }
    
    return { tables, fields };
  };
  
  const { tables, fields } = extractTablesAndFields(query);
  
  const handleCopyQuery = () => {
    navigator.clipboard.writeText(query).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  
  return (
    <Paper
      elevation={1}
      sx={{
        borderRadius: 2,
        overflow: 'hidden',
        mb: 2,
        border: theme => `1px solid ${theme.palette.divider}`,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          p: 1.5,
          bgcolor: theme => theme.palette.mode === 'dark' 
            ? 'rgba(25, 118, 210, 0.15)' 
            : 'rgba(25, 118, 210, 0.05)',
          borderBottom: theme => `1px solid ${theme.palette.divider}`,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'primary.main' }}>
            SQL Query
          </Typography>
          <Tooltip title="Show query details">
            <IconButton 
              size="small" 
              onClick={() => setShowInfo(!showInfo)}
              sx={{ ml: 1, opacity: 0.7 }}
            >
              <InfoOutlinedIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        
        <Tooltip title={copied ? "Copied!" : "Copy query"}>
          <IconButton 
            size="small" 
            onClick={handleCopyQuery}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      
      <CodeBlock language="sql" code={query} />
      
      {showInfo && (
        <Box sx={{ p: 2, bgcolor: 'background.paper' }}>
          <Divider sx={{ mb: 2 }} />
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Tables:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {tables.length > 0 ? (
                tables.map((table, index) => (
                  <Paper 
                    key={index} 
                    sx={{ 
                      p: 1, 
                      bgcolor: 'primary.main', 
                      color: 'primary.contrastText',
                      borderRadius: 1,
                      fontSize: '0.875rem',
                    }}
                  >
                    {table}
                  </Paper>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No tables detected
                </Typography>
              )}
            </Box>
          </Box>
          
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Fields:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {fields.length > 0 ? (
                fields.map((field, index) => (
                  <Paper 
                    key={index} 
                    variant="outlined"
                    sx={{ 
                      p: 1, 
                      borderRadius: 1,
                      fontSize: '0.875rem',
                    }}
                  >
                    {field}
                  </Paper>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No fields detected
                </Typography>
              )}
            </Box>
          </Box>
        </Box>
      )}
    </Paper>
  );
};

export default SQLQueryVisualizer; 