import React, { useState, useRef } from 'react';
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
  Tooltip
} from '@mui/material';
import { 
  Close as CloseIcon,
  FileUpload as FileUploadIcon,
  Refresh as RefreshIcon,
  InsertDriveFile as InsertDriveFileIcon
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
  const fileInputRef = useRef(null);

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

    if (!datasetName) {
      setError('Please provide a name for the dataset');
      setShowAlert(true);
      return;
    }

    // Check file size (limit to 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds 10MB limit');
      setShowAlert(true);
      return;
    }

    // Check file type
    const allowedTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    if (!allowedTypes.includes(file.type)) {
      setError('Only CSV and Excel files are supported');
      setShowAlert(true);
      return;
    }

    setLoading(true);
    setError('');
    setSuccess(false);
    setShowAlert(false);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('datasetName', datasetName);
      formData.append('userId', 'anonymous'); // Replace with actual user ID if available

      console.log('File being uploaded:', file.name, file.type, file.size);
      
      const response = await uploadFile(formData);
      
      if (response.success) {
        setSuccess(true);
        setShowAlert(true);
        setPreview(response.preview);
        
        // Call the callback function if provided
        if (onUploadSuccess) {
          onUploadSuccess(response);
        }
      } else {
        throw new Error(response.error || 'Failed to upload file');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setError(error.message || 'Failed to upload file. Please try again.');
      setShowAlert(true);
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
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Get file icon based on file type
  const getFileIcon = () => {
    if (!file) return null;
    
    const fileExtension = file.name.split('.').pop().toLowerCase();
    
    let color = '#2563eb'; // Default blue
    
    if (['csv'].includes(fileExtension)) {
      color = '#10b981'; // Green for CSV
    } else if (['xls', 'xlsx'].includes(fileExtension)) {
      color = '#6366f1'; // Purple for Excel
    }
    
    return (
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center',
        color: color
      }}>
        <InsertDriveFileIcon sx={{ mr: 1 }} />
        <Typography variant="body2" sx={{ fontWeight: 500 }}>
          {file.name}
        </Typography>
      </Box>
    );
  };

  return (
    <Paper 
      elevation={0} 
      sx={{ 
        p: 0, 
        border: '1px solid rgba(0, 0, 0, 0.08)',
        borderRadius: 2,
        overflow: 'hidden'
      }}
    >
      {/* Header */}
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
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Upload Dataset
        </Typography>
        <Tooltip title="Reset form">
          <IconButton 
            size="small" 
            onClick={handleReset}
            disabled={loading}
            sx={{ 
              color: 'text.secondary',
              '&:hover': { color: 'primary.main' }
            }}
          >
            <RefreshIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      
      {/* Content */}
      <Box sx={{ p: 2 }}>
        {/* Alerts */}
        {showAlert && (
          <Alert 
            severity={success ? "success" : "error"} 
            sx={{ 
              mb: 2, 
              borderRadius: 1,
              '& .MuiAlert-icon': {
                color: success ? 'success.main' : 'error.main'
              }
            }}
            action={
              <IconButton
                size="small"
                onClick={() => setShowAlert(false)}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            }
          >
            {success ? 'File uploaded successfully!' : error}
          </Alert>
        )}
        
        {/* File Input */}
        <Box 
          sx={{ 
            border: '1px dashed rgba(0, 0, 0, 0.2)',
            borderRadius: 1,
            p: 3,
            mb: 2,
            textAlign: 'center',
            bgcolor: 'rgba(0, 0, 0, 0.01)',
            cursor: 'pointer',
            '&:hover': {
              bgcolor: 'rgba(0, 0, 0, 0.02)',
              borderColor: 'primary.main',
            }
          }}
          onClick={() => fileInputRef.current.click()}
        >
          <input
            type="file"
            accept=".csv,.xls,.xlsx"
            onChange={handleFileChange}
            style={{ display: 'none' }}
            ref={fileInputRef}
            disabled={loading}
          />
          
          {file ? (
            getFileIcon()
          ) : (
            <>
              <FileUploadIcon 
                sx={{ 
                  fontSize: 40, 
                  color: 'primary.main', 
                  mb: 1,
                  opacity: 0.8
                }} 
              />
              <Typography variant="body1" sx={{ mb: 0.5, fontWeight: 500 }}>
                Drag and drop a file or click to browse
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Supports CSV and Excel files (max 10MB)
              </Typography>
            </>
          )}
        </Box>
        
        {/* Dataset Name Input */}
        <TextField
          fullWidth
          label="Dataset Name"
          variant="outlined"
          value={datasetName}
          onChange={handleDatasetNameChange}
          disabled={loading}
          sx={{ 
            mb: 2,
            '& .MuiOutlinedInput-root': {
              borderRadius: 1,
            }
          }}
        />
        
        {/* Upload Button */}
        <Button
          fullWidth
          variant="contained"
          color="primary"
          onClick={handleUpload}
          disabled={!file || !datasetName || loading}
          sx={{ 
            py: 1,
            borderRadius: 1,
            textTransform: 'none',
            fontWeight: 500
          }}
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <FileUploadIcon />}
        >
          {loading ? 'Uploading...' : 'Upload Dataset'}
        </Button>
        
        {/* Data Preview */}
        {preview && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
              Data Preview
            </Typography>
            
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
                    {preview.columns.map((column, index) => (
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
                  {preview.data.map((row, rowIndex) => (
                    <TableRow 
                      key={rowIndex}
                      sx={{ 
                        '&:hover': { 
                          bgcolor: 'rgba(0, 0, 0, 0.01)' 
                        }
                      }}
                    >
                      {preview.columns.map((column, colIndex) => (
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
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default FileUpload;
