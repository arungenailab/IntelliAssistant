import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, IconButton, Tooltip, Alert, CircularProgress } from '@mui/material';
import Plot from 'react-plotly.js';
import DownloadIcon from '@mui/icons-material/Download';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import FullscreenExitIcon from '@mui/icons-material/FullscreenExit';

const AnalysisResult = ({ response, visualization }) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [plotData, setPlotData] = useState(null);
  const [plotLayout, setPlotLayout] = useState(null);
  const [plotConfig, setPlotConfig] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Process visualization data when it changes
    if (visualization) {
      try {
        setLoading(true);
        
        // Handle different visualization formats
        if (visualization.data) {
          // Direct data format
          setPlotData(visualization.data.data || []);
          setPlotLayout(visualization.data.layout || {});
          setPlotConfig(visualization.data.config || {});
        } else if (visualization.type && visualization.fig) {
          // Legacy format
          setPlotData(visualization.fig.data || []);
          setPlotLayout(visualization.fig.layout || {});
          setPlotConfig({});
        } else if (visualization.visualization_params) {
          // Parameters format - convert to Plotly format
          const params = visualization.visualization_params;
          const visType = visualization.type || params.type || 'bar';
          
          // Create appropriate data structure based on visualization type
          const data = createPlotlyData(visType, params);
          setPlotData(data);
          
          // Create layout
          const layout = {
            title: params.title || 'Data Visualization',
            xaxis: { title: params.x },
            yaxis: { title: params.y }
          };
          setPlotLayout(layout);
          setPlotConfig({});
        } else {
          setError('Invalid visualization format');
        }
      } catch (err) {
        console.error('Error processing visualization:', err);
        setError('Error processing visualization data');
      } finally {
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, [visualization]);
  
  // Helper function to create Plotly data from parameters
  const createPlotlyData = (visType, params) => {
    switch (visType.toLowerCase()) {
      case 'bar':
        return [{
          type: 'bar',
          x: params.x_data || [],
          y: params.y_data || [],
          marker: { color: params.color || '#3366ff' }
        }];
      case 'line':
        return [{
          type: 'scatter',
          mode: 'lines+markers',
          x: params.x_data || [],
          y: params.y_data || [],
          line: { color: params.color || '#3366ff' }
        }];
      case 'scatter':
        return [{
          type: 'scatter',
          mode: 'markers',
          x: params.x_data || [],
          y: params.y_data || [],
          marker: { color: params.color || '#3366ff' }
        }];
      case 'pie':
        return [{
          type: 'pie',
          labels: params.labels || [],
          values: params.values || [],
          marker: { colors: params.colors || [] }
        }];
      default:
        return [{
          type: 'bar',
          x: params.x_data || [],
          y: params.y_data || []
        }];
    }
  };
  
  const handleDownload = () => {
    const plotElement = document.getElementById('visualization-plot');
    if (plotElement && window.Plotly) {
      window.Plotly.downloadImage(plotElement, {
        format: 'png',
        filename: (plotLayout?.title?.text || 'visualization'),
        width: 1200,
        height: 800
      });
    }
  };
  
  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // If no visualization data and no error, return null
  if (!visualization && !error) return null;
  
  // If loading, show loading indicator
  if (loading) {
    return (
      <Paper elevation={1} sx={{ width: '100%', mt: 2, p: 4, textAlign: 'center' }}>
        <CircularProgress size={40} />
        <Typography variant="body2" sx={{ mt: 2 }}>
          Preparing visualization...
        </Typography>
      </Paper>
    );
  }
  
  // If error, show error message
  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }
  
  // If no plot data, show message
  if (!plotData || plotData.length === 0) {
    return (
      <Paper elevation={1} sx={{ width: '100%', mt: 2, p: 3 }}>
        <Typography variant="body1">
          {response || "No visualization data available. The analysis was completed successfully, but no visualization could be generated."}
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper 
      elevation={1} 
      sx={{ 
        width: '100%', 
        mt: 2,
        p: 2,
        borderRadius: 2,
        bgcolor: '#ffffff'
      }}
    >
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        mb: 2
      }}>
        <Typography variant="h6" sx={{ color: 'text.primary', fontSize: '1rem' }}>
          {plotLayout?.title?.text || visualization?.title || 'Data Visualization'}
        </Typography>
        
        <Box>
          <Tooltip title="Download as PNG">
            <IconButton onClick={handleDownload} size="small">
              <DownloadIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          
          <Tooltip title={isFullscreen ? "Exit Fullscreen" : "View Fullscreen"}>
            <IconButton onClick={handleFullscreen} size="small">
              {isFullscreen ? <FullscreenExitIcon fontSize="small" /> : <FullscreenIcon fontSize="small" />}
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
      
      {/* Text response if available */}
      {response && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2">{response}</Typography>
        </Box>
      )}
      
      <Box 
        sx={{ 
          width: '100%',
          height: isFullscreen ? 'calc(100vh - 200px)' : 250,
          transition: 'height 0.3s ease'
        }}
      >
        <Plot
          id="visualization-plot"
          data={plotData}
          layout={{
            autosize: true,
            height: isFullscreen ? 'calc(100vh - 200px)' : 250,
            margin: { l: 40, r: 10, t: 30, b: 40 },
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff',
            font: { 
              family: 'Roboto, sans-serif',
              size: 10
            },
            modebar: {
              orientation: 'v',
              bgcolor: 'rgba(255, 255, 255, 0.9)'
            },
            hoverlabel: {
              bgcolor: '#ffffff',
              font: { size: 10 }
            },
            legend: {
              orientation: 'h',
              yanchor: 'bottom',
              y: 1.02,
              xanchor: 'right',
              x: 1,
              bgcolor: 'rgba(255, 255, 255, 0.9)',
              bordercolor: '#e0e0e0',
              borderwidth: 1,
              font: { size: 10 }
            },
            ...plotLayout
          }}
          config={{
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            scrollZoom: true,
            toImageButtonOptions: {
              format: 'png',
              filename: plotLayout?.title?.text || 'visualization',
              height: 800,
              width: 1200,
              scale: 2
            },
            ...plotConfig
          }}
          style={{ 
            width: '100%',
            height: '100%'
          }}
          useResizeHandler={true}
        />
      </Box>
    </Paper>
  );
};

export default AnalysisResult;
