import React, { useState } from 'react';
import { 
  Box, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  TablePagination,
  Paper,
  Typography,
  Divider,
  Chip,
  IconButton,
  Tooltip,
  Collapse,
  Button,
  ButtonGroup,
  useTheme
} from '@mui/material';
import { 
  ExpandMore, 
  ExpandLess, 
  Code, 
  BarChart, 
  CheckCircle, 
  Error as ErrorIcon, 
  Warning,
  Download,
  Article
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, prism } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Safe import of xlsx
let XLSX;
try {
  XLSX = require('xlsx');
} catch (e) {
  console.warn('XLSX library not available:', e);
}

/**
 * Component to display SQL query results
 */
const SQLResultView = ({ 
  sql, 
  explanation, 
  results = [], 
  error = null,
  confidence = 0,
  visualization = null,
  compact = false // Add compact mode for chat interface
}) => {
  const theme = useTheme();
  
  // Determine which syntax highlighter theme to use based on the current theme mode
  const syntaxTheme = theme.palette.mode === 'dark' ? vscDarkPlus : prism;
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(compact ? results.length : 10);
  const [showSql, setShowSql] = useState(compact); // Change to show SQL by default in compact mode
  const [showExplanation, setShowExplanation] = useState(!compact);
  
  // Get confidence level styling
  const getConfidenceLevel = () => {
    // Ensure confidence is a number and between 0 and 1
    const confidenceValue = typeof confidence === 'number' ? Math.max(0, Math.min(1, confidence)) : 0;
    
    if (confidenceValue >= 0.75) return { color: 'success', icon: <CheckCircle fontSize="small" /> };
    if (confidenceValue >= 0.5) return { color: 'warning', icon: <Warning fontSize="small" /> };
    return { color: 'error', icon: <ErrorIcon fontSize="small" /> };
  };
  
  const confidenceInfo = getConfidenceLevel();
  
  // Extract column headers from results
  const columns = results && results.length > 0 ? Object.keys(results[0]) : [];
  
  // Format table for chat messages if compact
  const formatTableForChat = () => {
    if (!results || results.length === 0) return 'No results';
    
    // Create header row
    const header = columns.join(' | ');
    const separator = columns.map(() => '---').join(' | ');
    
    // Create data rows (limited to first 5 for chat display)
    const dataRows = results.slice(0, 5).map(row => {
      return columns.map(col => {
        const value = row[col];
        return value !== null && value !== undefined ? String(value) : '';
      }).join(' | ');
    });
    
    // Add a message if there are more rows
    const moreRowsMessage = results.length > 5 ? 
      `\n\n*Showing 5 of ${results.length} results. See full results in the data view.*` : '';
    
    return '```\n' + [header, separator, ...dataRows].join('\n') + '\n```' + moreRowsMessage;
  };
  
  // Handle table pagination
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(1);
  };
  
  // Calculate pagination indices
  const startIndex = (page - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const displayedResults = results.slice(startIndex, endIndex);
  const totalPages = Math.ceil(results.length / rowsPerPage);
  
  // Handle SQL display toggle
  const toggleSql = () => {
    setShowSql(!showSql);
  };
  
  // Handle explanation display toggle
  const toggleExplanation = () => {
    setShowExplanation(!showExplanation);
  };
  
  // Download results as CSV
  const downloadCsv = () => {
    if (!results || results.length === 0) return;

    // Create CSV header row
    let csvContent = columns.join(',') + '\n';
    
    // Add data rows
    results.forEach(row => {
      const rowValues = columns.map(column => {
        // Handle values that might contain commas or quotes by wrapping in quotes
        const value = row[column]?.toString() || '';
        if (value.includes(',') || value.includes('"')) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      });
      csvContent += rowValues.join(',') + '\n';
    });
    
    // Create a Blob and download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    // Create a temporary download link and trigger click
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `sql_results_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    
    // Clean up
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Download results as Excel
  const downloadExcel = () => {
    if (!results || results.length === 0) return;
    
    if (!XLSX) {
      console.warn('XLSX library not available, falling back to CSV');
      downloadCsv();
      return;
    }
    
    try {
      const worksheet = XLSX.utils.json_to_sheet(results);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Results");
      XLSX.writeFile(workbook, `sql_results_${new Date().toISOString().split('T')[0]}.xlsx`);
    } catch (error) {
      console.error("Error generating Excel file:", error);
      // Fallback to CSV if Excel generation fails
      downloadCsv();
    }
  };

  // Generate visualization if applicable
  const renderVisualization = () => {
    if (!visualization) return null;
    
    // If visualization is provided as a base64 image
    if (visualization.type === 'image' && visualization.data) {
      return (
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>Visualization</Typography>
          <img 
            src={`data:image/png;base64,${visualization.data}`} 
            alt="Data visualization" 
            style={{ maxWidth: '100%', maxHeight: '300px' }} 
          />
        </Box>
      );
    }
    
    // For other visualization types, show a placeholder
    return (
      <Box sx={{ mt: 2, textAlign: 'center', color: 'text.secondary' }}>
        <BarChart sx={{ fontSize: 40 }} />
        <Typography variant="body2">Visualization data available but not rendered</Typography>
      </Box>
    );
  };
  
  return (
    <Box sx={{ width: '100%' }}>
      {/* If in compact mode for chat, render a simpler version */}
      {compact ? (
        <>
          {/* Compact SQL Result View for Chat */}
          <Box sx={{ mb: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Chip 
                size="small" 
                label={`SQL Query (${confidence ? Math.round(confidence * 100) : 0}% confident)`} 
                color={confidenceInfo.color} 
                icon={confidenceInfo.icon} 
                sx={{ mr: 1, textTransform: 'none' }}
              />
              <IconButton 
                size="small" 
                onClick={toggleSql}
                sx={{ mr: 0.5 }}
                aria-label={showSql ? "Hide SQL" : "Show SQL"}
              >
                {showSql ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
              </IconButton>
            </Box>
            
            {/* SQL Query Collapse for Compact View */}
            <Collapse in={showSql}>
              <Box sx={{ mb: 1 }}>
                <SyntaxHighlighter 
                  language="sql" 
                  style={syntaxTheme}
                  customStyle={{ 
                    margin: 0, 
                    borderRadius: '4px',
                    maxHeight: '150px',
                    fontSize: '0.75rem'
                  }}
                >
                  {sql || '-- No SQL query available'}
                </SyntaxHighlighter>
              </Box>
            </Collapse>
            
            {error ? (
              <Box sx={{ p: 1, bgcolor: 'error.light', borderRadius: 1, mb: 1 }}>
                <Typography variant="body2" color="error.dark">{error}</Typography>
              </Box>
            ) : (
              <>
                {/* Download Options for Compact View */}
                {results && results.length > 0 && (
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 1 }}>
                    <ButtonGroup size="small" variant="outlined">
                      <Tooltip title="Download as CSV">
                        <Button
                          size="small"
                          startIcon={<Download fontSize="small" />}
                          onClick={downloadCsv}
                          sx={{ fontSize: '0.7rem', py: 0.5 }}
                        >
                          CSV
                        </Button>
                      </Tooltip>
                      {XLSX && (
                        <Tooltip title="Download as Excel">
                          <Button
                            size="small"
                            startIcon={<Article fontSize="small" />}
                            onClick={downloadExcel}
                            sx={{ fontSize: '0.7rem', py: 0.5 }}
                          >
                            Excel
                          </Button>
                        </Tooltip>
                      )}
                    </ButtonGroup>
                  </Box>
                )}
                
                {/* Simple Table Display */}
                {results && results.length > 0 ? (
                  <Box 
                    component="div" 
                    sx={{ 
                      overflow: 'auto',
                      borderRadius: 1,
                      border: '1px solid rgba(224, 224, 224, 0.4)',
                      maxHeight: '300px',
                      mb: 1,
                      width: '100%',
                      '&::-webkit-scrollbar': {
                        height: '8px',
                        width: '8px'
                      },
                      '&::-webkit-scrollbar-thumb': {
                        backgroundColor: 'rgba(0,0,0,0.1)',
                        borderRadius: '4px',
                      },
                      '&::-webkit-scrollbar-track': {
                        backgroundColor: 'rgba(0,0,0,0.05)',
                      }
                    }}
                  >
                    <Table 
                      size="small" 
                      aria-label="SQL query results" 
                      sx={{ 
                        tableLayout: 'auto', 
                        minWidth: columns.length * 120, 
                        width: '100%',
                        backgroundColor: theme.palette.background.paper
                      }}
                    >
                      <TableHead>
                        <TableRow>
                          {columns.map((column) => (
                            <TableCell 
                              key={column} 
                              sx={{ 
                                fontWeight: 'bold',
                                py: 0.5,
                                px: 1,
                                fontSize: '0.8rem',
                                whiteSpace: 'nowrap',
                                minWidth: '100px'
                              }}
                            >
                              {column}
                            </TableCell>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {results.slice(0, 5).map((row, index) => (
                          <TableRow key={index}>
                            {columns.map((column) => (
                              <TableCell 
                                key={`${index}-${column}`} 
                                sx={{ 
                                  py: 0.5, 
                                  px: 1,
                                  fontSize: '0.8rem',
                                  minWidth: '100px',
                                  maxWidth: '200px',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap'
                                }}
                              >
                                <Tooltip title={row[column]?.toString() || ''}>
                                  <span>{row[column]?.toString() || ''}</span>
                                </Tooltip>
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                        {results.length > 5 && (
                          <TableRow>
                            <TableCell 
                              colSpan={columns.length} 
                              align="center"
                              sx={{ py: 0.5, fontSize: '0.75rem', color: 'text.secondary' }}
                            >
                              {results.length - 5} more rows...
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">No results returned</Typography>
                )}
              </>
            )}
          </Box>
        </>
      ) : (
        // Original full-featured SQLResultView follows...
        <>
          {/* The header section with SQL query info */}
          <Box sx={{ display: 'flex', flexDirection: 'column', mb: 2 }}>
            {/* SQL Header with Confidence Level */}
      <Box 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          mb: 1
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="subtitle2">SQL Query</Typography>
                <Chip 
                  size="small" 
                  label={`${confidence ? Math.round(confidence * 100) : 0}% confident`} 
                  color={confidenceInfo.color} 
                  icon={confidenceInfo.icon} 
                  sx={{ ml: 1, height: 20, fontSize: '0.75rem' }}
                />
          <IconButton 
            size="small" 
            onClick={toggleSql} 
            sx={{ ml: 0.5 }}
            aria-label={showSql ? "Hide SQL" : "Show SQL"}
          >
            {showSql ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
          </IconButton>
        </Box>
        
              <Tooltip title="View syntax highlighted SQL">
                <IconButton 
            size="small" 
                  onClick={toggleSql}
                  aria-label="SQL code"
                >
                  <Code fontSize="small" />
                </IconButton>
        </Tooltip>
      </Box>
      
      {/* SQL Query Collapse */}
      <Collapse in={showSql}>
        <Box sx={{ mb: 2 }}>
          <SyntaxHighlighter 
            language="sql" 
                  style={syntaxTheme}
            customStyle={{ 
              margin: 0, 
              borderRadius: '4px',
              maxHeight: '200px',
              fontSize: '0.85rem'
            }}
          >
            {sql || '-- No SQL query available'}
          </SyntaxHighlighter>
        </Box>
      </Collapse>
          </Box>
      
      {/* Explanation Section */}
      <Box 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          mb: 1
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="subtitle2">Explanation</Typography>
          <IconButton 
            size="small" 
            onClick={toggleExplanation} 
            sx={{ ml: 0.5 }}
            aria-label={showExplanation ? "Hide explanation" : "Show explanation"}
          >
            {showExplanation ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
          </IconButton>
        </Box>
      </Box>
      
      {/* Explanation Collapse */}
      <Collapse in={showExplanation}>
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" sx={{ fontSize: '0.9rem', color: 'text.secondary' }}>
            {explanation || 'No explanation available'}
          </Typography>
        </Box>
      </Collapse>
      
      {/* Error Message */}
      {error && (
        <Box sx={{ mb: 2, p: 1, bgcolor: 'error.light', borderRadius: 1 }}>
          <Typography variant="body2" color="error.dark">
            {error}
          </Typography>
        </Box>
      )}
      
      {/* Results Table */}
      {results && results.length > 0 && (
        <Paper variant="outlined" sx={{ width: '100%', mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 1 }}>
            <ButtonGroup size="small">
              <Tooltip title="Download as CSV">
                <Button
                  startIcon={<Download />}
                  onClick={downloadCsv}
                  sx={{ fontSize: '0.75rem' }}
                >
                  CSV
                </Button>
              </Tooltip>
                  {XLSX && (
              <Tooltip title="Download as Excel">
                <Button
                  startIcon={<Article />}
                  onClick={downloadExcel}
                  sx={{ fontSize: '0.75rem' }}
                >
                  Excel
                </Button>
              </Tooltip>
                  )}
            </ButtonGroup>
          </Box>
          <TableContainer sx={{ maxHeight: 400, overflowX: 'auto' }}>
            <Table stickyHeader size="small" aria-label="SQL query results">
              <TableHead>
                <TableRow>
                  {columns.map((column) => {
                    // Format column header for display - handle table prefixes
                    const displayColumn = column.includes('.') ? column.split('.').pop() : column;
                    
                    return (
                      <TableCell 
                        key={column} 
                        sx={{ 
                          fontWeight: 'bold', 
                          py: 1,
                          px: 2,
                          bgcolor: 'background.paper',
                          minWidth: displayColumn.length > 15 ? 180 : 120, // Set wider columns for long column names
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          borderRight: '1px solid rgba(224, 224, 224, 0.4)',
                          '&:last-child': {
                            borderRight: 'none'
                          }
                        }}
                      >
                        <Tooltip title={column} placement="top" arrow>
                          <Box component="span">
                            {displayColumn}
                          </Box>
                        </Tooltip>
                      </TableCell>
                    );
                  })}
                </TableRow>
              </TableHead>
              <TableBody>
                {results
                      .slice(startIndex, endIndex)
                  .map((row, index) => (
                    <TableRow 
                      key={index} 
                      hover
                      sx={{
                        '&:nth-of-type(odd)': {
                          backgroundColor: 'rgba(0, 0, 0, 0.02)',
                        },
                      }}
                    >
                      {columns.map((column) => {
                        // Determine content type for proper alignment
                        const cellValue = row[column]?.toString() || '';
                        const isNumber = !isNaN(cellValue) && cellValue.trim() !== '';
                        const isDate = /^\d{4}-\d{2}-\d{2}/.test(cellValue);
                        
                        return (
                          <TableCell 
                            key={`${index}-${column}`} 
                            align={isNumber && !isDate ? 'right' : 'left'}
                            sx={{ 
                              py: 1, 
                              px: 2,
                              minWidth: column.length > 15 ? 180 : 120,
                              maxWidth: 300,
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              borderRight: '1px solid rgba(224, 224, 224, 0.4)',
                              '&:last-child': {
                                borderRight: 'none'
                              }
                            }}
                          >
                            <Tooltip title={cellValue} arrow placement="top">
                              <Box component="span" sx={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {cellValue}
                              </Box>
                            </Tooltip>
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={results.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            sx={{ 
              '& .MuiTablePagination-toolbar': { 
                minHeight: '40px', 
                px: 1 
              },
              '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                fontSize: '0.75rem',
                mb: 0
              }
            }}
          />
        </Paper>
      )}
      
      {/* No Results Message */}
      {(!results || results.length === 0) && !error && (
        <Box sx={{ my: 2, textAlign: 'center', color: 'text.secondary' }}>
          <Typography variant="body2">
            No results returned from the query
          </Typography>
        </Box>
      )}
      
      {/* Visualization Section */}
      {visualization && renderVisualization()}
        </>
      )}
    </Box>
  );
};

export default SQLResultView;
