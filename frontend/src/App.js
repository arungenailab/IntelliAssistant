import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import ChatPage from './pages/ChatPage';
import DataPage from './pages/DataPage';
import SettingsPage from './pages/SettingsPage';
import DatasetsPage from './pages/DatasetsPage';
import UploadPage from './pages/UploadPage';
import ApiDataPage from './pages/ApiDataPage';
import ThemeProvider from './contexts/ThemeContext';
import './App.css';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Routes>
          <Route path="/" element={
            <MainLayout>
              <ChatPage />
            </MainLayout>
          } />
          <Route path="/data" element={
            <MainLayout>
              <DataPage />
            </MainLayout>
          } />
          <Route path="/datasets" element={
            <MainLayout>
              <DatasetsPage />
            </MainLayout>
          } />
          <Route path="/upload" element={
            <MainLayout>
              <UploadPage />
            </MainLayout>
          } />
          <Route path="/api-data" element={
            <MainLayout>
              <ApiDataPage />
            </MainLayout>
          } />
          <Route path="/settings" element={
            <MainLayout>
              <SettingsPage />
            </MainLayout>
          } />
          {/* Redirect /chat to home page */}
          <Route path="/chat" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
