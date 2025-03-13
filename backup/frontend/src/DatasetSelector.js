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
  CircularProgress,
  Alert,
  Button,
  Collapse,
  IconButton
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
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
      const data = await getDatasets();
      if (!data) {
        throw new Error('No data received from server');
      }
      setDatasets(data);
      
      // If there's only one dataset, select it automatically
      const datasetNames = Object.keys(data);
      if (datasetNames.length === 1) {
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
    setSelectedDataset(datasetName);
    
    // Call the parent component's callback if provided
    if (onDatasetSelect && datasetName) {
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
    <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="h6">
          Available Datasets
        </Typography>
        {selectedDataset && (
          <Button 
            size="small" 
            onClick={togglePreview}
            endIcon={showPreview ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          >
            {showPreview ? "Hide Preview" : "Show Preview"}
          </Button>
        )}
      </Box>
      
      {loading ? (
        <Box display="flex" justifyContent="center" my={2}>
          <CircularProgress size={24} />
        </Box>
      ) : error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      ) : Object.keys(datasets).length === 0 ? (
        <Alert severity="info">
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
              size="small"
            >
              {Object.keys(datasets).map((name) => {
                const shape = getDatasetShape(name);
                return (
                  <MenuItem key={name} value={name}>
                    {name} ({shape.rows} rows, {shape.columns} columns)
                  </MenuItem>
                );
              })}
            </Select>
          </FormControl>
          
          {selectedDataset && datasets[selectedDataset] && (
            <>
              <Box mb={1}>
                <Typography variant="subtitle2" gutterBottom>
                  Columns:
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={0.5}>
                  {getSelectedDatasetColumns().map((column) => (
                    <Chip key={column} label={column} size="small" />
                  ))}
                </Box>
              </Box>
              
              <Collapse in={showPreview}>
                <Box mt={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    Data Preview:
                  </Typography>
                  <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 200 }}>
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          {getSelectedDatasetColumns().map((column) => (
                            <TableCell key={column}>{column}</TableCell>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {getSelectedDatasetPreview().map((row, index) => (
                          <TableRow key={index}>
                            {getSelectedDatasetColumns().map((column) => (
                              <TableCell key={column}>
                                {typeof row[column] === 'object' 
                                  ? JSON.stringify(row[column]) 
                                  : String(row[column] !== undefined ? row[column] : '')}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              </Collapse>
            </>
          )}
        </>
      )}
    </Paper>
  );
};

export default DatasetSelector;
