import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, IconButton, Tooltip, Alert, CircularProgress } from '@mui/material';
import Plot from 'react-plotly.js';
import DownloadIcon from '@mui/icons-material/Download';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import FullscreenExitIcon from '@mui/icons-material/FullscreenExit';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';

const AnalysisResult = ({ response, visualization }) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [plotData, setPlotData] = useState([]);
  const [plotLayout, setPlotLayout] = useState({});
  const [plotConfig, setPlotConfig] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (visualization) {
      try {
        setLoading(true);
        console.log('Processing visualization data:', visualization);
        
        // Handle different visualization formats
        if (visualization.data && visualization.data.data) {
          console.log('Using direct data format with nested data property');
          setPlotData(visualization.data.data || []);
          setPlotLayout(visualization.data.layout || {});
          setPlotConfig(visualization.data.config || {});
        } else if (visualization.data) {
          console.log('Using direct data format');
          // This is for the case where data is an array directly
          setPlotData(Array.isArray(visualization.data) ? visualization.data : [visualization.data]);
          setPlotLayout(visualization.layout || {});
          setPlotConfig(visualization.config || {});
        } else if (visualization.type && visualization.fig) {
          console.log('Using legacy format');
          setPlotData(visualization.fig.data || []);
          setPlotLayout(visualization.fig.layout || {});
          setPlotConfig({});
        } else if (visualization.visualization_params) {
          console.log('Using parameters format');
          const params = visualization.visualization_params;
          const visType = visualization.type || params.type || 'bar';
          
          console.log('Creating Plotly data with:', { visType, params });
          const data = createPlotlyData(visType, params);
          setPlotData(data);
          
          const layout = {
            title: params.title || 'Data Visualization',
            xaxis: { title: params.x },
            yaxis: { title: params.y }
          };
          setPlotLayout(layout);
          setPlotConfig({});
        } else {
          // Try to handle the case where the visualization object itself contains the necessary properties
          console.log('Trying to extract data directly from visualization object');
          if (visualization.type) {
            // This is likely our backend format
            const visType = visualization.type;
            const title = visualization.title || 'Data Visualization';
            
            // Check if we have a direct data array in the visualization
            if (Array.isArray(visualization.data)) {
              setPlotData(visualization.data);
            } else {
              // Create a default data structure based on the type
              setPlotData([{
                type: visType,
                x: visualization.x_data || [],
                y: visualization.y_data || [],
                name: visualization.name || '',
                marker: { color: visualization.color || '#3366ff' }
              }]);
            }
            
            setPlotLayout({
              title: title,
              xaxis: { title: visualization.x || '' },
              yaxis: { title: visualization.y || '' }
            });
            setPlotConfig({});
          } else {
            console.error('Invalid visualization format:', visualization);
            setError('Invalid visualization format - missing required data');
          }
        }
      } catch (err) {
        console.error('Error processing visualization:', err);
        console.error('Visualization data:', visualization);
        setError(`Error processing visualization data: ${err.message}`);
      } finally {
        setLoading(false);
      }
    } else {
      console.log('No visualization data provided');
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
          <ReactMarkdown
            rehypePlugins={[rehypeRaw]}
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ node, ...props }) => <Typography variant="body2" component="p" sx={{ my: 1 }} {...props} />,
              h1: ({ node, ...props }) => <Typography variant="h4" component="h1" sx={{ mt: 3, mb: 2 }} {...props} />,
              h2: ({ node, ...props }) => <Typography variant="h5" component="h2" sx={{ mt: 2.5, mb: 1.5 }} {...props} />,
              h3: ({ node, ...props }) => <Typography variant="h6" component="h3" sx={{ mt: 2, mb: 1 }} {...props} />,
              h4: ({ node, ...props }) => <Typography variant="subtitle1" component="h4" sx={{ mt: 2, mb: 1 }} {...props} />,
              li: ({ node, ...props }) => <Typography component="li" variant="body2" sx={{ mb: 0.5 }} {...props} />,
              ul: ({ node, ...props }) => <Box component="ul" sx={{ pl: 2, mb: 2 }} {...props} />,
              ol: ({ node, ...props }) => <Box component="ol" sx={{ pl: 2, mb: 2 }} {...props} />,
              table: ({ node, ...props }) => (
                <Box sx={{ overflowX: 'auto', my: 2 }}>
                  <table style={{ borderCollapse: 'collapse', width: '100%' }} {...props} />
                </Box>
              ),
              tr: ({ node, ...props }) => <tr style={{ borderBottom: '1px solid rgba(0, 0, 0, 0.1)' }} {...props} />,
              th: ({ node, ...props }) => (
                <th style={{ padding: '8px 16px', textAlign: 'left', backgroundColor: 'rgba(0, 0, 0, 0.04)' }} {...props} />
              ),
              td: ({ node, ...props }) => <td style={{ padding: '8px 16px' }} {...props} />,
              code: ({ node, inline, ...props }) => (
                inline ? 
                <Typography component="code" sx={{ 
                  backgroundColor: 'rgba(0, 0, 0, 0.04)', 
                  padding: '2px 4px',
                  borderRadius: '4px',
                  fontFamily: 'monospace',
                  fontSize: '0.875rem' 
                }} {...props} /> :
                <Box component="pre" sx={{
                  backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  padding: 2,
                  borderRadius: 1,
                  overflowX: 'auto',
                  fontFamily: 'monospace',
                  fontSize: '0.875rem'
                }}>
                  <code {...props} />
                </Box>
              )
            }}
          >
            {response}
          </ReactMarkdown>
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
