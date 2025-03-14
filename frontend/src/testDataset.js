/**
 * Test script to fetch datasets directly from the API
 * Run this with: node testDataset.js
 */

// Simple fetch without any dependencies
async function fetchDatasets() {
  try {
    console.log('Fetching datasets from API...');
    
    const response = await fetch('http://localhost:5000/api/datasets', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }
    
    const data = await response.json();
    console.log('API Response:', data);
    
    // Check if the response data is in the expected format
    if (!data || typeof data !== 'object') {
      throw new Error('Invalid response format, expected an object');
    }
    
    // Check if we have any datasets
    const datasetCount = Object.keys(data).length;
    console.log(`Found ${datasetCount} datasets`);
    
    // Log the structure of each dataset
    for (const [name, details] of Object.entries(data)) {
      console.log(`Dataset: ${name}`);
      console.log(`- Columns: ${details.columns ? details.columns.length : 'unknown'}`);
      console.log(`- Preview rows: ${details.preview ? details.preview.length : 'unknown'}`);
      console.log(`- Shape: ${details.shape ? 
        `${details.shape.rows} rows, ${details.shape.columns} columns` : 
        'unknown'}`);
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching datasets:', error);
    return null;
  }
}

// Execute the test function
fetchDatasets().then(data => {
  if (data) {
    console.log('Test completed successfully with data');
  } else {
    console.log('Test failed, no data returned');
  }
}); 