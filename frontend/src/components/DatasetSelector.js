import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  Button,
  Collapse,
  Skeleton,
  Tooltip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import StorageIcon from '@mui/icons-material/Storage';
import { getDatasets } from '../api/chatApi';

const DatasetSelector = ({ onDatasetSelect }) => {
  const [datasets, setDatasets] = useState({});
  const [selectedDataset, setSelectedDataset] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showPreview, setShowPreview] = useState(false);

  // Fetch datasets on component mount
  useEffect(() => {
    fetchDatasets();
  }, []);

  // Fetch datasets from the API
  const fetchDatasets = async () => {
    setLoading(true);
    setError('');
    
    try {
      console.log('Fetching datasets...');
      const data = await getDatasets();
      console.log('Datasets received:', data);
      
      if (!data) {
        throw new Error('No data received from server');
      }
      setDatasets(data);
      
      // If there's only one dataset, select it automatically
      const datasetNames = Object.keys(data);
      console.log('Dataset names:', datasetNames);
      
      if (datasetNames.length === 1) {
        console.log('Auto-selecting the only dataset:', datasetNames[0]);
        setSelectedDataset(datasetNames[0]);
        if (onDatasetSelect) {
          onDatasetSelect(datasetNames[0], data[datasetNames[0]]);
        }
      }
    } catch (error) {
      console.error('Error fetching datasets:', error);
      setError('Failed to load datasets. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle dataset selection change
  const handleDatasetChange = (event) => {
    const datasetName = event.target.value;
    console.log('Dataset selected:', datasetName);
    setSelectedDataset(datasetName);
    
    // Call the parent component's callback if provided
    if (onDatasetSelect && datasetName) {
      console.log('Calling onDatasetSelect with:', datasetName, datasets[datasetName]);
      onDatasetSelect(datasetName, datasets[datasetName]);
    }
  };

  // Get the selected dataset's preview data
  const getSelectedDatasetPreview = () => {
    if (!selectedDataset || !datasets[selectedDataset]) {
      return [];
    }
    
    return datasets[selectedDataset].preview || [];
  };

  // Get the selected dataset's columns
  const getSelectedDatasetColumns = () => {
    if (!selectedDataset || !datasets[selectedDataset]) {
      return [];
    }
    
    return datasets[selectedDataset].columns || [];
  };

  // Get dataset shape information
  const getDatasetShape = (name) => {
    const dataset = datasets[name];
    if (!dataset || !dataset.shape) {
      return { rows: '?', columns: '?' };
    }
    return dataset.shape;
  };

  // Toggle preview visibility
  const togglePreview = () => {
    setShowPreview(!showPreview);
  };

  return (
    <Paper 
      elevation={0} 
      sx={{ 
        p: 0, 
        mb: 2, 
        border: '1px solid rgba(0, 0, 0, 0.08)',
        borderRadius: 2,
        overflow: 'hidden'
      }}
    >
      <Box 
        sx={{ 
          p: 2, 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
          bgcolor: 'background.paper'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box 
            sx={{ 
              width: 32, 
              height: 32, 
              borderRadius: '50%', 
              bgcolor: 'primary.main', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              mr: 1.5,
              color: 'white'
            }}
          >
            <StorageIcon fontSize="small" />
          </Box>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
        Available Datasets
      </Typography>
        </Box>
        {selectedDataset && (
          <Button 
            size="small" 
            onClick={togglePreview}
            endIcon={showPreview ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            sx={{
              borderRadius: 1,
              px: 1.5,
              py: 0.5,
              bgcolor: showPreview ? 'primary.main' : 'transparent',
              color: showPreview ? 'white' : 'primary.main',
              border: showPreview ? 'none' : '1px solid rgba(0, 0, 0, 0.12)',
              '&:hover': {
                bgcolor: showPreview ? 'primary.dark' : 'rgba(37, 99, 235, 0.04)',
              }
            }}
          >
            {showPreview ? "Hide Preview" : "Show Preview"}
          </Button>
        )}
      </Box>
      
      <Box sx={{ p: 2 }}>
      {loading ? (
          <Box sx={{ width: '100%' }}>
            <Skeleton variant="rectangular" width="100%" height={48} sx={{ borderRadius: 1, mb: 2 }} />
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Skeleton variant="rectangular" width={80} height={28} sx={{ borderRadius: 1 }} />
              <Skeleton variant="rectangular" width={100} height={28} sx={{ borderRadius: 1 }} />
              <Skeleton variant="rectangular" width={90} height={28} sx={{ borderRadius: 1 }} />
            </Box>
        </Box>
      ) : error ? (
          <Alert 
            severity="error" 
            sx={{ 
              mb: 2, 
              borderRadius: 1,
              '& .MuiAlert-icon': {
                color: 'error.main'
              }
            }}
          >
          {error}
        </Alert>
      ) : Object.keys(datasets).length === 0 ? (
          <Alert 
            severity="info" 
            sx={{ 
              borderRadius: 1,
              '& .MuiAlert-icon': {
                color: 'info.main'
              }
            }}
          >
          No datasets available. Please upload a data file first.
        </Alert>
      ) : (
        <>
            <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="dataset-select-label">Select Dataset</InputLabel>
            <Select
              labelId="dataset-select-label"
              id="dataset-select"
              value={selectedDataset}
              label="Select Dataset"
              onChange={handleDatasetChange}
                size="medium"
                sx={{
                  borderRadius: 1,
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(0, 0, 0, 0.15)',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'primary.main',
                    borderWidth: 1.5,
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(0, 0, 0, 0.3)',
                  },
                }}
            >
              {Object.keys(datasets).map((name) => {
                const shape = getDatasetShape(name);
                return (
                  <MenuItem key={name} value={name}>
                      <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                        <Typography sx={{ fontWeight: 500 }}>
                          {name}
                        </Typography>
                        <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center' }}>
                          <Chip 
                            label={`${shape.rows} rows`} 
                            size="small" 
                            sx={{ 
                              mr: 1, 
                              bgcolor: 'rgba(37, 99, 235, 0.08)', 
                              color: 'primary.main',
                              fontWeight: 500,
                              fontSize: '0.7rem',
                              height: 20,
                            }} 
                          />
                          <Chip 
                            label={`${shape.columns} cols`} 
                            size="small" 
                            sx={{ 
                              bgcolor: 'rgba(37, 99, 235, 0.08)', 
                              color: 'primary.main',
                              fontWeight: 500,
                              fontSize: '0.7rem',
                              height: 20,
                            }} 
                          />
                        </Box>
                      </Box>
                  </MenuItem>
                );
              })}
            </Select>
          </FormControl>
          
            {selectedDataset && (
              <>
                <Box sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Columns
                </Typography>
                  <Tooltip title="These are the columns available in your dataset">
                    <InfoOutlinedIcon fontSize="small" sx={{ ml: 0.5, color: 'text.secondary', fontSize: 16 }} />
                  </Tooltip>
                </Box>
                
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                  {getSelectedDatasetColumns().map((column, index) => (
                    <Chip 
                      key={index} 
                      label={column} 
                      size="small" 
                      sx={{ 
                        bgcolor: 'rgba(0, 0, 0, 0.04)', 
                        color: 'text.primary',
                        fontWeight: 400,
                        fontSize: '0.75rem',
                      }} 
                    />
                  ))}
                </Box>
                
                <Collapse in={showPreview} timeout="auto">
                  <Box sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      Data Preview
                    </Typography>
                    <Tooltip title="This is a preview of your dataset">
                      <InfoOutlinedIcon fontSize="small" sx={{ ml: 0.5, color: 'text.secondary', fontSize: 16 }} />
                    </Tooltip>
              </Box>
              
                  <TableContainer 
                    component={Paper} 
                    elevation={0}
                    sx={{ 
                      maxHeight: 300,
                      border: '1px solid rgba(0, 0, 0, 0.08)',
                      borderRadius: 1,
                    }}
                  >
                    <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                          {getSelectedDatasetColumns().map((column, index) => (
                            <TableCell 
                              key={index}
                              sx={{ 
                                fontWeight: 600, 
                                bgcolor: 'rgba(0, 0, 0, 0.02)',
                                py: 1,
                                fontSize: '0.75rem',
                              }}
                            >
                              {column}
                            </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                        {getSelectedDatasetPreview().map((row, rowIndex) => (
                          <TableRow 
                            key={rowIndex}
                            sx={{ 
                              '&:hover': { 
                                bgcolor: 'rgba(0, 0, 0, 0.01)' 
                              }
                            }}
                          >
                            {getSelectedDatasetColumns().map((column, colIndex) => (
                              <TableCell 
                                key={colIndex}
                                sx={{ 
                                  py: 0.75,
                                  fontSize: '0.75rem',
                                  borderBottom: '1px solid rgba(0, 0, 0, 0.04)',
                                }}
                              >
                                {row[column] !== null && row[column] !== undefined ? String(row[column]) : ''}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
                </Collapse>
            </>
          )}
        </>
      )}
      </Box>
    </Paper>
  );
};

export default DatasetSelector;
