import React, { useState, useEffect } from 'react';
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
  ButtonGroup
} from '@mui/material';
import { 
  ExpandMore, 
  ExpandLess, 
  Code, 
  BarChart, 
  CheckCircle, 
  Error, 
  Warning,
  Download,
  Article
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import * as ExcelJS from 'exceljs';

/**
 * Component to display SQL query results
 */
const SQLResultView = ({ 
  sql, 
  explanation, 
  results, 
  error, 
  confidence = 0,
  visualization = null 
}) => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const [showSql, setShowSql] = useState(false);
  const [showExplanation, setShowExplanation] = useState(true);
  
  // Get confidence level styling
  const getConfidenceLevel = () => {
    if (confidence >= 0.8) return { color: 'success', icon: <CheckCircle fontSize="small" /> };
    if (confidence >= 0.5) return { color: 'warning', icon: <Warning fontSize="small" /> };
    return { color: 'error', icon: <Error fontSize="small" /> };
  };
  
  const confidenceInfo = getConfidenceLevel();
  
  // Extract column headers from results
  const columns = results && results.length > 0 ? Object.keys(results[0]) : [];
  
  // Handle table pagination
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Calculate empty rows for pagination
  const emptyRows = rowsPerPage - Math.min(rowsPerPage, (results?.length || 0) - page * rowsPerPage);
  
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
  const downloadExcel = async () => {
    if (!results || results.length === 0) return;
    
    try {
      // Create a new workbook and worksheet
      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet('SQL Results');
      
      // Add headers
      worksheet.columns = columns.map(column => ({
        header: column,
        key: column,
        width: 20
      }));
      
      // Add data rows
      results.forEach(row => {
        const rowData = {};
        columns.forEach(column => {
          rowData[column] = row[column]?.toString() || '';
        });
        worksheet.addRow(rowData);
      });
      
      // Style the header row
      worksheet.getRow(1).font = { bold: true };
      
      // Generate Excel file
      const buffer = await workbook.xlsx.writeBuffer();
      const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = URL.createObjectURL(blob);
      
      // Create a temporary download link and trigger click
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `sql_results_${new Date().toISOString().split('T')[0]}.xlsx`);
      document.body.appendChild(link);
      link.click();
      
      // Clean up
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
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
    <Box sx={{ mt: 1, width: '100%' }}>
      {/* SQL Query & Confidence Section */}
      <Box 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          mb: 1
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Code fontSize="small" sx={{ mr: 0.5 }} />
          <Typography variant="subtitle2">SQL Query</Typography>
          <IconButton 
            size="small" 
            onClick={toggleSql} 
            sx={{ ml: 0.5 }}
            aria-label={showSql ? "Hide SQL" : "Show SQL"}
          >
            {showSql ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
          </IconButton>
        </Box>
        
        <Tooltip title={`Confidence: ${Math.round(confidence * 100)}%`}>
          <Chip 
            label={`${Math.round(confidence * 100)}% confident`} 
            size="small" 
            color={confidenceInfo.color}
            icon={confidenceInfo.icon}
            sx={{ height: 24 }}
          />
        </Tooltip>
      </Box>
      
      {/* SQL Query Collapse */}
      <Collapse in={showSql}>
        <Box sx={{ mb: 2 }}>
          <SyntaxHighlighter 
            language="sql" 
            style={vscDarkPlus}
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
              <Tooltip title="Download as Excel">
                <Button
                  startIcon={<Article />}
                  onClick={downloadExcel}
                  sx={{ fontSize: '0.75rem' }}
                >
                  Excel
                </Button>
              </Tooltip>
            </ButtonGroup>
          </Box>
          <TableContainer sx={{ maxHeight: 400 }}>
            <Table stickyHeader size="small" aria-label="SQL query results">
              <TableHead>
                <TableRow>
                  {columns.map((column) => (
                    <TableCell key={column} sx={{ fontWeight: 'bold', py: 1 }}>
                      {column}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {results
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((row, index) => (
                    <TableRow key={index} hover>
                      {columns.map((column) => (
                        <TableCell key={`${index}-${column}`} sx={{ py: 1 }}>
                          {row[column]?.toString() || ''}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                {emptyRows > 0 && (
                  <TableRow style={{ height: 33 * emptyRows }}>
                    <TableCell colSpan={columns.length} />
                  </TableRow>
                )}
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
    </Box>
  );
};

export default SQLResultView;
