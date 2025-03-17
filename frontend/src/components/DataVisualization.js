import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell
} from 'recharts';

// Default colors for charts
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#A4DE6C'];

const DataVisualization = ({ data }) => {
  if (!data) return null;

  // Debug logging to see what data we're receiving
  console.log('Visualization data received:', data);

  // Handle string data that may need parsing
  let parsedData = data;
  if (typeof data === 'string') {
    try {
      parsedData = JSON.parse(data);
      console.log('Parsed visualization data:', parsedData);
    } catch (error) {
      console.error('Failed to parse visualization data string:', error);
      return (
        <Box sx={{ my: 2, p: 2, border: '1px solid #ddd', borderRadius: 2 }}>
          <Typography color="error">
            Unable to parse visualization data
          </Typography>
          <pre>{data}</pre>
        </Box>
      );
    }
  }

  // Check if we have the expected data structure
  if (!parsedData.type || !parsedData.data) {
    console.error('Invalid visualization data format:', parsedData);
    
    // If data is an array, try to auto-detect the chart type
    if (Array.isArray(parsedData)) {
      console.log('Trying to auto-detect chart type for array data');
      // Create a "best guess" visualization
      parsedData = {
        type: 'bar',
        title: 'Auto-detected Visualization',
        data: parsedData
      };
    } else {
      return (
        <Box sx={{ my: 2, p: 2, border: '1px solid #ddd', borderRadius: 2 }}>
          <Typography color="error">
            Unable to render visualization: invalid data format
          </Typography>
          <Typography variant="caption" component="div" sx={{ mt: 1 }}>
            Expected format: {`{ type: 'bar|line|pie', data: [...] }`}
          </Typography>
          <Box sx={{ mt: 1, p: 1, bgcolor: '#f5f5f5', borderRadius: 1, overflowX: 'auto' }}>
            <pre style={{ margin: 0 }}>{JSON.stringify(parsedData, null, 2)}</pre>
          </Box>
        </Box>
      );
    }
  }

  // Extract visualization type and data
  const { type, data: chartData, title, xAxisLabel, yAxisLabel } = parsedData;

  // Render different chart types based on the type field
  const renderChart = () => {
    switch (type.toLowerCase()) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                label={{ 
                  value: xAxisLabel || '', 
                  position: 'bottom', 
                  offset: 0 
                }}
              />
              <YAxis 
                label={{ 
                  value: yAxisLabel || '', 
                  angle: -90, 
                  position: 'left' 
                }}
              />
              <Tooltip />
              <Legend />
              {Object.keys(chartData[0] || {})
                .filter(key => key !== 'name')
                .map((key, index) => (
                  <Bar 
                    key={key} 
                    dataKey={key} 
                    fill={COLORS[index % COLORS.length]} 
                    name={key}
                  />
                ))}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                label={{ 
                  value: xAxisLabel || '', 
                  position: 'bottom', 
                  offset: 0 
                }}
              />
              <YAxis 
                label={{ 
                  value: yAxisLabel || '', 
                  angle: -90, 
                  position: 'left' 
                }}
              />
              <Tooltip />
              <Legend />
              {Object.keys(chartData[0] || {})
                .filter(key => key !== 'name')
                .map((key, index) => (
                  <Line 
                    key={key} 
                    type="monotone" 
                    dataKey={key} 
                    stroke={COLORS[index % COLORS.length]} 
                    name={key}
                  />
                ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={true}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => new Intl.NumberFormat().format(value)} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        return (
          <Box sx={{ p: 2 }}>
            <Typography color="error">
              Unsupported chart type: {type}
            </Typography>
          </Box>
        );
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        my: 2,
        p: 2,
        border: theme => `1px solid ${theme.palette.divider}`,
        borderRadius: 2,
        bgcolor: theme => theme.palette.background.paper,
      }}
    >
      {title && (
        <Typography 
          variant="h6" 
          component="h3" 
          align="center" 
          sx={{ mb: 2, fontWeight: 600 }}
        >
          {title}
        </Typography>
      )}
      {renderChart()}
    </Paper>
  );
};

export default DataVisualization;
