import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  Paper, 
  CircularProgress, 
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  IconButton,
  Collapse
} from '@mui/material';
import { 
  CloudUpload as CloudUploadIcon,
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { uploadFile } from '../api/chatApi';

const FileUpload = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [datasetName, setDatasetName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState(null);
  const [success, setSuccess] = useState(false);
  const [showAlert, setShowAlert] = useState(false);

  // Handle file selection
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      // Generate a default dataset name based on the file name
      const baseName = selectedFile.name.split('.')[0];
      setDatasetName(baseName);
      setError('');
      setPreview(null);
      setSuccess(false);
    }
  };

  // Handle dataset name change
  const handleDatasetNameChange = (event) => {
    setDatasetName(event.target.value);
  };

  // Handle file upload
  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload');
      setShowAlert(true);
      return;
    }

    if (!datasetName.trim()) {
      setError('Please provide a dataset name');
      setShowAlert(true);
      return;
    }

    setLoading(true);
    setError('');
    setShowAlert(true);

    try {
      console.log('Uploading file:', file.name, 'Size:', file.size, 'Type:', file.type);
      
      // Check file size (limit to 10MB)
      if (file.size > 10 * 1024 * 1024) {
        throw new Error('File size exceeds 10MB limit');
      }
      
      // Check file type
      const fileExt = file.name.split('.').pop().toLowerCase();
      const allowedTypes = ['csv', 'xlsx', 'xls', 'json', 'txt'];
      if (!allowedTypes.includes(fileExt)) {
        throw new Error(`File type .${fileExt} is not supported. Allowed types: ${allowedTypes.join(', ')}`);
      }
      
      const response = await uploadFile(file, datasetName);
      console.log('Upload response:', response);
      
      setPreview(response.preview);
      setSuccess(true);
      
      // Call the parent component's callback if provided
      if (onUploadSuccess) {
        onUploadSuccess(response);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      
      // Extract error message
      let errorMessage = 'Error uploading file. Please try again.';
      if (error.response) {
        console.error('Error response:', error.response);
        errorMessage = error.response.data?.error || errorMessage;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
      setSuccess(false);
    } finally {
      setLoading(false);
    }
  };

  // Reset the form
  const handleReset = () => {
    setFile(null);
    setDatasetName('');
    setError('');
    setPreview(null);
    setSuccess(false);
    setShowAlert(false);
    
    // Reset the file input
    const fileInput = document.getElementById('file-upload-input');
    if (fileInput) {
      fileInput.value = '';
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Upload Data
      </Typography>
      
      {/* Alert for success or error */}
      <Collapse in={showAlert}>
        <Box mb={2}>
          {error ? (
            <Alert 
              severity="error" 
              action={
                <IconButton
                  aria-label="close"
                  color="inherit"
                  size="small"
                  onClick={() => setShowAlert(false)}
                >
                  <CloseIcon fontSize="inherit" />
                </IconButton>
              }
            >
              {error}
            </Alert>
          ) : success ? (
            <Alert 
              severity="success"
              action={
                <IconButton
                  aria-label="close"
                  color="inherit"
                  size="small"
                  onClick={() => setShowAlert(false)}
                >
                  <CloseIcon fontSize="inherit" />
                </IconButton>
              }
            >
              File uploaded successfully!
            </Alert>
          ) : null}
        </Box>
      </Collapse>
      
      {/* File input and dataset name */}
      <Box display="flex" flexDirection="column" gap={2} mb={3}>
        <Box>
          <input
            accept=".csv,.xlsx,.xls,.json,.txt"
            style={{ display: 'none' }}
            id="file-upload-input"
            type="file"
            onChange={handleFileChange}
          />
          <label htmlFor="file-upload-input">
            <Button
              variant="outlined"
              component="span"
              startIcon={<CloudUploadIcon />}
              fullWidth
            >
              Select File
            </Button>
          </label>
          {file && (
            <Typography variant="body2" mt={1} color="textSecondary">
              Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
            </Typography>
          )}
        </Box>
        
        <TextField
          label="Dataset Name"
          variant="outlined"
          value={datasetName}
          onChange={handleDatasetNameChange}
          fullWidth
          disabled={loading}
          helperText="Provide a name for this dataset"
        />
      </Box>
      
      {/* Upload and Reset buttons */}
      <Box display="flex" gap={2}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleUpload}
          disabled={loading || !file}
          startIcon={loading ? <CircularProgress size={20} /> : success ? <CheckCircleIcon /> : null}
        >
          {loading ? 'Uploading...' : success ? 'Uploaded' : 'Upload'}
        </Button>
        
        <Button
          variant="outlined"
          onClick={handleReset}
          disabled={loading}
        >
          Reset
        </Button>
      </Box>
      
      {/* Data preview */}
      {preview && (
        <Box mt={4}>
          <Typography variant="h6" gutterBottom>
            Data Preview
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  {Object.keys(preview[0] || {}).map((key) => (
                    <TableCell key={key}>{key}</TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {preview.map((row, index) => (
                  <TableRow key={index}>
                    {Object.values(row).map((value, i) => (
                      <TableCell key={i}>
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}
    </Paper>
  );
};

export default FileUpload;
