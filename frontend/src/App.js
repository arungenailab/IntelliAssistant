import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import ChatPage from './pages/ChatPage';
import DataPage from './pages/DataPage';
import HomePage from './pages/HomePage';
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
            <MainLayout title="Dashboard">
              <HomePage />
            </MainLayout>
          } />
          <Route path="/chat" element={
            <MainLayout title="Chat">
              <ChatPage />
            </MainLayout>
          } />
          <Route path="/data" element={
            <MainLayout title="Data Analysis">
              <DataPage />
            </MainLayout>
          } />
          <Route path="/datasets" element={
            <MainLayout title="Datasets">
              <DatasetsPage />
            </MainLayout>
          } />
          <Route path="/upload" element={
            <MainLayout title="Upload">
              <UploadPage />
            </MainLayout>
          } />
          <Route path="/api-data" element={
            <MainLayout title="External Data Sources">
              <ApiDataPage />
            </MainLayout>
          } />
          <Route path="/settings" element={
            <MainLayout title="Settings">
              <SettingsPage />
            </MainLayout>
          } />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
