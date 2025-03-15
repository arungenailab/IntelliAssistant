import React, { useState } from 'react';
import { Box, Paper, Typography, Tabs, Tab, IconButton, Tooltip } from '@mui/material';
import CodeBlock from './ui/CodeBlock';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import AnalysisResult from './AnalysisResult';

/**
 * A component for visualizing SQL queries and their results
 * @param {string} query - The SQL query to display
 * @param {object} results - The results of the query
 * @param {object} visualization - The visualization data
 * @returns {JSX.Element}
 */
const SQLQueryVisualizer = ({ query, results, visualization }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [expanded, setExpanded] = useState(false);
  
  // Format the query with proper indentation if needed
  const formattedQuery = query;
  
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };
  
  const toggleExpanded = () => {
    setExpanded(prev => !prev);
  };
  
  return (
    <Paper 
      elevation={1}
      sx={{ 
        borderRadius: '8px',
        overflow: 'hidden',
        mb: 2,
        border: '1px solid rgba(0, 0, 0, 0.08)',
        transition: 'all 0.3s ease',
      }}
    >
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        px: 2,
        py: 1,
        borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
        bgcolor: 'background.default'
      }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'text.secondary' }}>
          SQL Query
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Tooltip title="Execute Query">
            <IconButton size="small" color="primary" sx={{ mr: 1 }}>
              <PlayArrowIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          
          <Tooltip title={expanded ? "Collapse" : "Expand"}>
            <IconButton size="small" onClick={toggleExpanded}>
              {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
      
      <Box sx={{ maxHeight: expanded ? '600px' : '200px', transition: 'max-height 0.3s ease', overflow: 'hidden' }}>
        <Tabs 
          value={activeTab}
          onChange={handleTabChange}
          sx={{ 
            borderBottom: 1, 
            borderColor: 'divider',
            minHeight: '36px',
            '& .MuiTab-root': {
              minHeight: '36px',
              py: 0.5
            }
          }}
        >
          <Tab label="Query" />
          {results && <Tab label="Results" />}
          {visualization && <Tab label="Visualization" />}
        </Tabs>
        
        {/* Query Panel */}
        {activeTab === 0 && (
          <Box sx={{ p: 0 }}>
            <CodeBlock 
              language="sql" 
              code={formattedQuery} 
              showLineNumbers={true}
            />
          </Box>
        )}
        
        {/* Results Panel */}
        {activeTab === 1 && results && (
          <Box sx={{ p: 2, overflowX: 'auto' }}>
            {Array.isArray(results) ? (
              <Box component="table" sx={{ 
                width: '100%', 
                borderCollapse: 'collapse',
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
              }}>
                {/* Table headers */}
                {results.length > 0 && (
                  <Box component="thead">
                    <Box component="tr">
                      {Object.keys(results[0]).map((key, index) => (
                        <Box component="th" key={index}>{key}</Box>
                      ))}
                    </Box>
                  </Box>
                )}
                
                {/* Table body */}
                <Box component="tbody">
                  {results.map((row, rowIndex) => (
                    <Box component="tr" key={rowIndex}>
                      {Object.values(row).map((value, cellIndex) => (
                        <Box component="td" key={cellIndex}>
                          {String(value)}
                        </Box>
                      ))}
                    </Box>
                  ))}
                </Box>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No results available.
              </Typography>
            )}
          </Box>
        )}
        
        {/* Visualization Panel */}
        {activeTab === 2 && visualization && (
          <Box sx={{ p: 2 }}>
            <AnalysisResult visualization={visualization} />
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default SQLQueryVisualizer; 