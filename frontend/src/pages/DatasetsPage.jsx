import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  ArrowUpDown, 
  ChevronDown, 
  MoreHorizontal, 
  File, 
  Trash2, 
  Download, 
  BarChart3, 
  MessageSquare,
  AlertCircle,
  Loader2,
  RefreshCw
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { getDatasets } from '../api/chatApi';

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [retryCount, setRetryCount] = useState(0);

  // Fetch datasets with a memoized function to prevent infinite loops
  const fetchDatasets = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Fetching datasets...');
      
      // Try direct fetch first for comparison
      try {
        const directResponse = await fetch('http://localhost:5000/api/datasets', {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (directResponse.ok) {
          const directData = await directResponse.json();
          console.log('Direct fetch successful:', directData);
          
          if (directData && typeof directData === 'object' && Object.keys(directData).length > 0) {
            console.log('Setting datasets from direct fetch');
            setDatasets(directData);
            setLoading(false);
            return; // Exit early if direct fetch worked
          }
        } else {
          console.error('Direct fetch failed with status:', directResponse.status);
        }
      } catch (directError) {
        console.error('Direct fetch error:', directError);
      }
      
      // Fall back to the API method from chatApi.js
      console.log('Trying API method from chatApi.js');
      const data = await getDatasets();
      
      console.log('Datasets received from API method:', data);
      
      if (!data) {
        throw new Error('No data received from server');
      }
      
      // Log the structure of the response
      console.log('Dataset keys:', Object.keys(data));
      
      if (Object.keys(data).length > 0) {
        const firstDatasetKey = Object.keys(data)[0];
        console.log('First dataset structure:', JSON.stringify(data[firstDatasetKey], null, 2));
      }
      
      // Set data to state
      setDatasets(data);
    } catch (error) {
      console.error('Error fetching datasets:', error);
      
      // Create detailed error message
      let errorMessage = 'Failed to load datasets. Please try again.';
      if (error.response) {
        errorMessage += ` Server responded with status ${error.response.status}.`;
        console.error('Error response data:', error.response.data);
      } else if (error.request) {
        errorMessage += ' No response received from server.';
        console.error('Error request:', error.request);
      } else {
        errorMessage += ` Error: ${error.message}`;
      }
      
      // Check if backend might be unavailable
      if (error.message && error.message.includes('Network Error')) {
        errorMessage = 'Could not connect to the backend server. Please ensure the API server is running.';
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [retryCount]); // Include retryCount to re-run when retried

  // Fetch datasets on component mount or when retry count changes
  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  // Handle manual refresh
  const handleRefresh = () => {
    setRetryCount(prev => prev + 1);
  };

  // Automatically retry once if it fails on first load
  useEffect(() => {
    if (error && retryCount === 0) {
      console.log('Auto-retrying dataset fetch after initial failure');
      // Wait 1 second before retrying
      const timer = setTimeout(() => {
        setRetryCount(1);
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [error, retryCount]);

  // Filter datasets based on search term
  const filteredDatasets = Object.entries(datasets || {}).filter(([name]) => 
    name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get file type icon based on dataset name or source
  const getFileTypeFromName = (name) => {
    const nameLower = name.toLowerCase();
    
    if (nameLower.includes('csv')) return 'CSV';
    if (nameLower.includes('excel') || nameLower.includes('xlsx')) return 'XLSX';
    if (nameLower.includes('json')) return 'JSON';
    if (nameLower.includes('sql')) return 'SQL';
    if (nameLower.includes('financial') || nameLower.includes('stock') || nameLower === 'msft') return 'API';
    if (nameLower.includes('api')) return 'API';
    if (nameLower.includes('sales')) return 'Sales';
    
    return 'DATA';
  };

  // Format dataset information safely
  const formatDatasetInfo = (details) => {
    if (!details) return { rows: '?', columns: '?' };
    
    const rows = details.shape?.rows ?? 
                 (details.preview?.length ? `${details.preview.length}+` : '?');
                 
    const columns = details.shape?.columns ?? 
                    details.columns?.length ?? 
                    (details.preview?.[0] ? Object.keys(details.preview[0]).length : '?');
                    
    return { rows, columns };
  };

  console.log('Rendering DatasetsPage with:', { 
    datasetsLoaded: datasets && Object.keys(datasets).length > 0,
    loading, 
    error, 
    filteredDatasetsCount: filteredDatasets.length
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Datasets</h1>
          <p className="text-muted-foreground mt-1">
            Manage your uploaded and imported datasets
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleRefresh} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
            Refresh
          </Button>
          <Button asChild>
            <Link to="/upload">Upload Dataset</Link>
          </Button>
        </div>
      </div>

      <div className="flex flex-col md:flex-row items-center gap-4 pb-4">
        <div className="relative w-full md:w-64">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search datasets..." 
            className="pl-8 w-full"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">Loading datasets...</span>
        </div>
      ) : error ? (
        <Card className="p-6">
          <div className="flex items-center gap-3 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <p>{error}</p>
          </div>
          <Button variant="outline" className="mt-4" onClick={handleRefresh}>
            Try Again
          </Button>
        </Card>
      ) : (!datasets || Object.keys(datasets).length === 0) ? (
        <Card className="p-6 text-center">
          <p className="text-muted-foreground mb-4">No datasets found. Upload a dataset or import from an external API.</p>
          <div className="flex justify-center gap-4">
            <Button asChild>
              <Link to="/upload">Upload Dataset</Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/api-data">Connect to API</Link>
            </Button>
          </div>
        </Card>
      ) : filteredDatasets.length === 0 ? (
        <Card className="p-6 text-center">
          <p className="text-muted-foreground mb-4">No matching datasets found. Clear your search or upload a new dataset.</p>
          <Button variant="outline" onClick={() => setSearchTerm('')}>
            Clear Search
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDatasets.map(([name, details]) => {
            console.log(`Rendering dataset card for: ${name}`, details);
            
            // Get formatted info
            const { rows, columns } = formatDatasetInfo(details);
            const fileType = getFileTypeFromName(name);
            
            return (
              <Card key={name} className="overflow-hidden">
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10 text-primary">
                        <File className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="font-medium">{name}</h3>
                        <p className="text-sm text-muted-foreground mt-0.5">
                          {fileType} • {rows} rows • {columns} columns
                        </p>
                      </div>
                    </div>
                    <div className="relative">
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="flex gap-2 mt-4">
                    <Button variant="outline" size="sm" className="w-full" asChild>
                      <Link to={`/data?dataset=${name}`}>
                        <BarChart3 className="mr-2 h-4 w-4" />
                        Analyze
                      </Link>
                    </Button>
                    <Button variant="outline" size="sm" className="w-full" asChild>
                      <Link to={`/chat?dataset=${name}`}>
                        <MessageSquare className="mr-2 h-4 w-4" />
                        Chat
                      </Link>
                    </Button>
                  </div>

                  <div className="flex gap-2 mt-2">
                    <Button variant="ghost" size="sm" className="w-full">
                      <Download className="mr-2 h-4 w-4" />
                      Download
                    </Button>
                    <Button variant="ghost" size="sm" className="w-full text-destructive hover:text-destructive">
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </Button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
} 