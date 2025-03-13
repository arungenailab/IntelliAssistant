import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Tabs,
  Tab,
  Divider,
  Button,
  TextField,
  Grid
} from '@mui/material';
import { 
  UploadFile as UploadFileIcon,
  Storage as StorageIcon,
  BarChart as BarChartIcon,
  Send as SendIcon
} from '@mui/icons-material';
import FileUpload from '../components/FileUpload';
import DatasetSelector from '../components/DatasetSelector';
import AnalysisResult from '../components/AnalysisResult';
import { sendMessage } from '../api/chatApi';

const DataPage = () => {
  const [tabValue, setTabValue] = useState(0);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [datasetDetails, setDatasetDetails] = useState(null);
  const [queryInput, setQueryInput] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [suggestedQueries, setSuggestedQueries] = useState([]);

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Handle dataset selection
  const handleDatasetSelect = (datasetName, details) => {
    setSelectedDataset(datasetName);
    setDatasetDetails(details);
    
    // Generate suggested queries based on the dataset
    generateSuggestedQueries(details);
  };

  // Generate suggested queries based on the dataset
  const generateSuggestedQueries = (details) => {
    if (!details || !details.columns) return;
    
    const columns = details.columns;
    const queries = [];
    
    // Add general queries
    queries.push(`Summarize this dataset`);
    queries.push(`What insights can you provide about this data?`);
    
    // Add column-specific queries
    if (columns.some(col => col.toLowerCase().includes('date') || col.toLowerCase().includes('time'))) {
      queries.push(`Show trends over time`);
    }
    
    if (columns.some(col => col.toLowerCase().includes('category') || col.toLowerCase().includes('type'))) {
      queries.push(`Compare different categories`);
    }
    
    if (columns.some(col => 
      col.toLowerCase().includes('sales') || 
      col.toLowerCase().includes('revenue') || 
      col.toLowerCase().includes('profit')
    )) {
      queries.push(`Analyze sales performance`);
    }
    
    if (columns.some(col => 
      col.toLowerCase().includes('region') || 
      col.toLowerCase().includes('country') || 
      col.toLowerCase().includes('state') || 
      col.toLowerCase().includes('city')
    )) {
      queries.push(`Show geographical distribution`);
    }
    
    setSuggestedQueries(queries.slice(0, 5)); // Limit to 5 suggestions
  };

  // Handle upload success
  const handleUploadSuccess = (data) => {
    // Switch to the Datasets tab after successful upload
    setTabValue(1);
  };

  // Handle query input change
  const handleQueryInputChange = (event) => {
    setQueryInput(event.target.value);
  };

  // Handle suggested query click
  const handleSuggestedQueryClick = (query) => {
    setQueryInput(query);
  };

  // Handle query submission
  const handleSubmitQuery = async () => {
    if (!queryInput.trim() || !selectedDataset) return;
    
    setLoading(true);
    setAnalysisResult(null); // Clear previous results
    
    try {
      // Enhance the query with dataset context
      const enhancedQuery = `Analyze the "${selectedDataset}" dataset: ${queryInput}`;
      
      // Add visualization request to the query if it doesn't already mention visualization
      const visualizationTerms = ['chart', 'graph', 'plot', 'visualize', 'visualization'];
      const needsVisualization = !visualizationTerms.some(term => queryInput.toLowerCase().includes(term));
      
      const finalQuery = needsVisualization 
        ? `${enhancedQuery}. Please include a visualization of the results.` 
        : enhancedQuery;
      
      const response = await sendMessage(finalQuery, null, selectedDataset);
      
      // Process the response
      if (response.error) {
        // Handle error
        setAnalysisResult({
          query: queryInput,
          datasetName: selectedDataset,
          response: response.text,
          error: response.error,
          visualization: null
        });
      } else {
        // Handle success
        setAnalysisResult({
          query: queryInput,
          datasetName: selectedDataset,
          response: response.text,
          visualization: response.visualization
        });
        
        // Switch to the Analysis tab
        setTabValue(2);
      }
    } catch (error) {
      console.error('Error analyzing data:', error);
      
      // Set error result
      setAnalysisResult({
        query: queryInput,
        datasetName: selectedDataset,
        response: "Sorry, I encountered an error analyzing your data. Please try again.",
        error: error.message,
        visualization: null
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Data Analysis
      </Typography>
      
      <Paper sx={{ mb: 4 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="fullWidth"
          indicatorColor="primary"
          textColor="primary"
          aria-label="data analysis tabs"
        >
          <Tab icon={<UploadFileIcon />} label="Upload" />
          <Tab icon={<StorageIcon />} label="Datasets" />
          <Tab icon={<BarChartIcon />} label="Analysis" />
        </Tabs>
        
        <Divider />
        
        <Box p={3}>
          {/* Upload Tab */}
          {tabValue === 0 && (
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          )}
          
          {/* Datasets Tab */}
          {tabValue === 1 && (
            <>
              <DatasetSelector onDatasetSelect={handleDatasetSelect} />
              
              {selectedDataset && (
                <Paper elevation={3} sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Ask a Question
                  </Typography>
                  
                  <TextField
                    fullWidth
                    label="What would you like to know about this data?"
                    variant="outlined"
                    value={queryInput}
                    onChange={handleQueryInputChange}
                    sx={{ mb: 2 }}
                  />
                  
                  {suggestedQueries.length > 0 && (
                    <Box mb={2}>
                      <Typography variant="subtitle2" gutterBottom>
                        Suggested queries:
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={1}>
                        {suggestedQueries.map((query, index) => (
                          <Button
                            key={index}
                            size="small"
                            variant="outlined"
                            onClick={() => handleSuggestedQueryClick(query)}
                          >
                            {query}
                          </Button>
                        ))}
                      </Box>
                    </Box>
                  )}
                  
                  <Button
                    variant="contained"
                    color="primary"
                    endIcon={<SendIcon />}
                    onClick={handleSubmitQuery}
                    disabled={!queryInput.trim() || loading}
                  >
                    {loading ? 'Analyzing...' : 'Analyze'}
                  </Button>
                </Paper>
              )}
            </>
          )}
          
          {/* Analysis Tab */}
          {tabValue === 2 && (
            <>
              {analysisResult ? (
                <Box>
                  <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
                    <Typography variant="h6" gutterBottom>
                      Query
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                      {analysisResult.query}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Dataset: {analysisResult.datasetName}
                    </Typography>
                  </Paper>
                  
                  <AnalysisResult 
                    response={analysisResult.response} 
                    visualization={analysisResult.visualization}
                  />
                  
                  <Box mt={3} display="flex" justifyContent="space-between">
                    <Button
                      variant="outlined"
                      onClick={() => setTabValue(1)}
                    >
                      Back to Datasets
                    </Button>
                    
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={() => {
                        setQueryInput('');
                        setTabValue(1);
                      }}
                    >
                      New Analysis
                    </Button>
                  </Box>
                </Box>
              ) : (
                <Box textAlign="center" py={4}>
                  <Typography variant="h6" color="textSecondary" gutterBottom>
                    No analysis results yet
                  </Typography>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => setTabValue(1)}
                  >
                    Go to Datasets
                  </Button>
                </Box>
              )}
            </>
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default DataPage;
