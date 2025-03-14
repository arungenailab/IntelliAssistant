import React, { useState } from 'react';
import { Upload, FileType, Check, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    setFile(file);
    setUploadStatus(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    setUploadStatus(null);
    
    try {
      // Mock upload process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setUploadStatus({
        success: true,
        message: 'File uploaded successfully!'
      });
    } catch (error) {
      setUploadStatus({
        success: false,
        message: error.message || 'Failed to upload file'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Upload Dataset</h1>
        <p className="text-muted-foreground mt-2">
          Upload your data files for analysis
        </p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Upload File</CardTitle>
          <CardDescription>
            Upload CSV, Excel, or JSON files to analyze with IntelliAssistant
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div 
            className={`border-2 border-dashed rounded-lg p-12 text-center ${
              dragActive ? 'border-primary bg-primary/5' : 'border-border'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="flex flex-col items-center justify-center space-y-4">
              <div className="rounded-full bg-primary/10 p-3">
                <Upload className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="font-medium">Drag and drop your file here</p>
                <p className="text-sm text-muted-foreground mt-1">
                  or click to browse your files
                </p>
              </div>
              <Input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={handleFileChange}
                accept=".csv,.xlsx,.xls,.json"
              />
              <Button variant="outline" onClick={() => document.getElementById('file-upload').click()}>
                Browse Files
              </Button>
              <div className="text-xs text-muted-foreground">
                Supported formats: CSV, Excel, JSON
              </div>
            </div>
          </div>
          
          {file && (
            <div className="mt-4 p-4 border rounded-md bg-muted/30">
              <div className="flex items-center gap-3">
                <div className="rounded-md bg-primary/10 p-2">
                  <FileType className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(file.size / 1024).toFixed(2)} KB • {file.type || 'Unknown type'}
                  </p>
                </div>
                <Button 
                  variant="default" 
                  size="sm" 
                  onClick={handleUpload}
                  disabled={uploading}
                >
                  {uploading ? 'Uploading...' : 'Upload'}
                </Button>
              </div>
            </div>
          )}
          
          {uploadStatus && (
            <div className={`mt-4 p-4 rounded-md ${
              uploadStatus.success ? 'bg-green-50 text-green-700 border border-green-200' : 
              'bg-red-50 text-red-700 border border-red-200'
            }`}>
              <div className="flex items-center gap-2">
                {uploadStatus.success ? (
                  <Check className="h-5 w-5" />
                ) : (
                  <AlertCircle className="h-5 w-5" />
                )}
                <p>{uploadStatus.message}</p>
              </div>
            </div>
          )}
        </CardContent>
        <CardFooter className="border-t bg-muted/30 px-6 py-4">
          <div className="flex flex-col space-y-1">
            <h4 className="text-sm font-medium">Tips for best results:</h4>
            <ul className="text-xs text-muted-foreground list-disc pl-4 space-y-1">
              <li>Ensure your data is clean and properly formatted</li>
              <li>Include headers in your CSV or Excel files</li>
              <li>Keep file size under 10MB for optimal performance</li>
              <li>Use UTF-8 encoding for CSV files</li>
            </ul>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
} 