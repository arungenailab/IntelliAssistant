import React, { useState, useEffect, useRef } from 'react';
import { Box, Grid, Typography, Paper, IconButton, TextField, Button, Divider, List, ListItem, ListItemText, Avatar, CircularProgress, Alert } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import ShareIcon from '@mui/icons-material/Share';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ChatHistory from '../components/ChatHistory';
import MessageInput from '../components/MessageInput';
import ChatMessage from '../components/ChatMessage';
import AnalysisResult from '../components/AnalysisResult';
import DatasetSelector from '../components/DatasetSelector';
import { sendMessage, getConversationHistory, getConversationMessages } from '../api/chatApi';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ReactDOM from 'react-dom/client';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CloseIcon from '@mui/icons-material/Close';

// Create a modern theme with enhanced visual elements
const theme = createTheme({
  palette: {
    primary: {
      main: '#2563eb', // Minimalistic blue
      light: '#93c5fd',
      dark: '#1e40af',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#4b5563', // Neutral gray
      light: '#9ca3af',
      dark: '#1f2937',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f9fafb',
      paper: '#ffffff',
    },
    text: {
      primary: '#111827',
      secondary: '#6b7280',
    },
    success: {
      main: '#10b981',
    },
    error: {
      main: '#ef4444',
    },
    warning: {
      main: '#f59e0b',
    },
    info: {
      main: '#3b82f6',
    },
  },
  typography: {
    fontFamily: [
      'Inter',
      'Segoe UI',
      'Roboto',
      'Helvetica',
      'Arial',
      'sans-serif',
    ].join(','),
    h4: {
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    h6: {
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    subtitle1: {
      fontWeight: 500,
    },
    button: {
      fontWeight: 500,
      textTransform: 'none',
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          boxShadow: 'none',
          padding: '6px 16px',
          '&:hover': {
            boxShadow: 'none',
          },
        },
        contained: {
          '&:hover': {
            boxShadow: 'none',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: 'none',
          border: '1px solid rgba(0, 0, 0, 0.08)',
        },
        elevation1: {
          boxShadow: 'none',
          border: '1px solid rgba(0, 0, 0, 0.08)',
        },
        elevation3: {
          boxShadow: 'none',
          border: '1px solid rgba(0, 0, 0, 0.12)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 6,
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(37, 99, 235, 0.08)',
          },
        },
      },
    },
  },
});

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [suggestedQueries, setSuggestedQueries] = useState([
    "Show total sales by country",
    "Compare sales across different products",
    "Analyze sales trends over time",
    "Show top 5 customers by amount"
  ]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Load conversation history
    const loadHistory = async () => {
      try {
        const history = await getConversationHistory();
        setConversationHistory(history);
      } catch (error) {
        console.error('Error loading conversation history:', error);
      }
    };
    
    loadHistory();
  }, []);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    
    // Create a temporary loading message
    const loadingMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: 'Analyzing your request...',
      timestamp: new Date().toISOString(),
      isLoading: true
    };
    
    setMessages(prev => [...prev, loadingMessage]);
    
    try {
      // Enhance query with visualization request if needed
      let enhancedQuery = inputValue;
      
      // Check if query is about data but doesn't mention visualization
      const dataTerms = ['data', 'analyze', 'show', 'display', 'chart', 'graph'];
      const visualizationTerms = ['chart', 'graph', 'plot', 'visualize', 'visualization'];
      
      const isDataQuery = dataTerms.some(term => inputValue.toLowerCase().includes(term));
      const mentionsVisualization = visualizationTerms.some(term => inputValue.toLowerCase().includes(term));
      
      if (isDataQuery && !mentionsVisualization && selectedDataset) {
        enhancedQuery = `${inputValue}. Please include a visualization of the results.`;
      }
      
      const response = await sendMessage(
        enhancedQuery, 
        activeConversation,
        selectedDataset?.name
      );
      
      // Remove the loading message
      setMessages(prev => prev.filter(msg => !msg.isLoading));
      
      // Process visualization data
      let visualizationData = null;
      if (response.visualization) {
        try {
          // If visualization is a string, parse it
          if (typeof response.visualization === 'string') {
            visualizationData = JSON.parse(response.visualization);
          } else {
            visualizationData = response.visualization;
          }
        } catch (error) {
          console.error('Error parsing visualization data:', error);
        }
      }
      
      const botMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.text || response.message || 'I analyzed your request.',
        timestamp: new Date().toISOString(),
        visualization: visualizationData,
        error: response.error
      };
      
      setMessages(prev => [...prev, botMessage]);
      
      // If this is a new conversation, update the active conversation
      if (!activeConversation && response.conversationId) {
        setActiveConversation(response.conversationId);
        // Update conversation history
        setConversationHistory(prev => [
          { 
            id: response.conversationId, 
            title: inputValue, 
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            message_count: 2
          },
          ...prev
        ]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Remove the loading message
      setMessages(prev => prev.filter(msg => !msg.isLoading));
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        error: error.message
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    console.log('New Chat button clicked');
    setMessages([]);
    setInputValue('');
    setActiveConversation(null);
    console.log('Messages cleared, activeConversation set to null');
  };

  const handleSelectConversation = async (conversationId) => {
    try {
      setIsLoading(true);
      const messages = await getConversationMessages(conversationId);
      setMessages(messages);
      setActiveConversation(conversationId);
    } catch (error) {
      console.error('Error loading conversation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedQuery = (query) => {
    setInputValue(query);
  };

  const handleDatasetSelect = (name, info) => {
    setSelectedDataset({ name, info });
    
    // Update suggested queries based on dataset columns
    if (info?.columns) {
      const columns = info.columns;
      const newQueries = [
        `Show distribution of ${columns[0]}`,
        `Compare ${columns[0]} by ${columns[1]}`,
        `Analyze trends in ${columns[0]} over time`,
        `Show top 5 records by ${columns[0]}`
      ];
      setSuggestedQueries(newQueries);
    }
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.default' }}>
        {/* Left Sidebar - Conversation History */}
        <Box sx={{ 
          width: sidebarOpen ? 260 : 0, 
          borderRight: '1px solid rgba(0, 0, 0, 0.08)', 
          p: sidebarOpen ? 2 : 0,
          bgcolor: 'background.paper',
          overflow: 'hidden',
          transition: 'width 0.3s, padding 0.3s',
          position: 'relative',
          flexShrink: 0, // Prevent sidebar from shrinking
          display: 'flex',
          flexDirection: 'column',
          boxShadow: 'none',
          zIndex: 10
        }}>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            mb: 2,
            pb: 2,
            borderBottom: '1px solid rgba(0, 0, 0, 0.06)'
          }}>
            <Typography variant="h6" component="div" sx={{ 
              fontWeight: 600,
              color: 'primary.main',
              letterSpacing: '-0.02em'
            }}>
              Data Analysis Assistant
            </Typography>
          </Box>
          
          <Button 
            variant="contained" 
            fullWidth 
            sx={{ 
              mb: 3,
              py: 1,
              fontWeight: 500,
              bgcolor: 'primary.main',
              '&:hover': {
                bgcolor: 'primary.dark',
              }
            }}
            onClick={handleNewChat}
            startIcon={<svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 5V19M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>}
          >
            New Chat
          </Button>
          
          <Box sx={{ flex: 1, overflowY: 'auto' }}>
            <ChatHistory 
              conversations={conversationHistory}
              activeConversation={activeConversation}
              onSelectConversation={handleSelectConversation}
            />
          </Box>
        </Box>
        
        {/* Toggle button for sidebar */}
        <Box sx={{ 
          position: 'absolute', 
          left: sidebarOpen ? 260 : 0, 
          top: '50%',
          zIndex: 20,
          transition: 'left 0.3s',
          transform: 'translateY(-50%)'
        }}>
          <IconButton 
            onClick={toggleSidebar}
            sx={{ 
              bgcolor: 'background.paper', 
              border: '1px solid rgba(0, 0, 0, 0.08)',
              '&:hover': { bgcolor: 'background.paper' },
              width: 28,
              height: 28
            }}
            size="small"
          >
            {sidebarOpen ? <ChevronLeftIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
          </IconButton>
        </Box>
        
        {/* Main Chat Area */}
        <Box sx={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column', 
          height: '100%',
          width: `calc(100% - ${sidebarOpen ? 260 : 0}px)`, // Adjust width based on sidebar state
          marginLeft: sidebarOpen ? 0 : '40px', // Add margin when sidebar is collapsed to account for toggle button
          transition: 'width 0.3s, margin-left 0.3s',
          position: 'relative' // Ensure proper positioning of children
        }}>
          {/* Dataset Selector - Hidden but still functional */}
          <Box sx={{ 
            position: 'absolute', 
            top: 16, 
            right: 16, 
            zIndex: 5, 
            p: 1.5,
            display: 'flex',
            alignItems: 'center',
            bgcolor: 'background.paper',
            borderRadius: 1,
            border: '1px solid rgba(0, 0, 0, 0.08)',
          }}>
            <Typography variant="body2" sx={{ mr: 2, fontWeight: 'medium', color: 'text.secondary' }}>
              {selectedDataset ? (
                <>
                  <span style={{ fontWeight: 'bold', color: 'text.primary' }}>Dataset:</span> {selectedDataset.name}
                </>
              ) : (
                'No dataset selected'
              )}
            </Typography>
            <Button
              variant="outlined"
              size="small"
              sx={{
                borderColor: 'primary.main',
                color: 'primary.main',
                '&:hover': {
                  borderColor: 'primary.dark',
                  bgcolor: 'rgba(37, 99, 235, 0.04)',
                },
                textTransform: 'none',
                fontWeight: 500,
                fontSize: '0.75rem',
              }}
              onClick={() => {
                // Open a dialog to select dataset
                const datasetDialog = document.createElement('div');
                datasetDialog.style.position = 'fixed';
                datasetDialog.style.top = '0';
                datasetDialog.style.left = '0';
                datasetDialog.style.width = '100%';
                datasetDialog.style.height = '100%';
                datasetDialog.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
                datasetDialog.style.display = 'flex';
                datasetDialog.style.alignItems = 'center';
                datasetDialog.style.justifyContent = 'center';
                datasetDialog.style.zIndex = '9999';
                
                const root = ReactDOM.createRoot(datasetDialog);
                
                root.render(
                  <ThemeProvider theme={theme}>
                    <Box sx={{ 
                      width: '600px',
                      maxWidth: '90vw',
                      maxHeight: '80vh',
                      bgcolor: 'background.paper',
                      borderRadius: 2,
                      border: '1px solid rgba(0, 0, 0, 0.12)',
                      overflow: 'hidden',
                      animation: 'fadeIn 0.2s ease-out',
                      '@keyframes fadeIn': {
                        '0%': {
                          opacity: 0,
                          transform: 'translateY(10px)'
                        },
                        '100%': {
                          opacity: 1,
                          transform: 'translateY(0)'
                        }
                      }
                    }}>
                      <Box sx={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center', 
                        p: 2,
                        borderBottom: '1px solid rgba(0, 0, 0, 0.06)'
                      }}>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>Select Dataset</Typography>
                        <IconButton onClick={() => {
                          document.body.removeChild(datasetDialog);
                        }}>
                          <CloseIcon />
                        </IconButton>
                      </Box>
                      <Box sx={{ p: 2, overflowY: 'auto' }}>
                        <DatasetSelector onDatasetSelect={(name, info) => {
                          handleDatasetSelect(name, info);
                          document.body.removeChild(datasetDialog);
                        }} />
                      </Box>
                    </Box>
                  </ThemeProvider>
                );
                
                document.body.appendChild(datasetDialog);
              }}
            >
              Change Dataset
            </Button>
          </Box>
          
          {/* Chat Messages Area */}
          <Box sx={{ 
            flex: 1, 
            overflowY: 'auto', 
            p: 3, 
            pt: 8, // Add padding to top to account for dataset selector
            display: 'flex',
            flexDirection: 'column',
          }}>
            {messages.length === 0 ? (
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                justifyContent: 'center', 
                height: '100%',
                textAlign: 'center',
                px: 2
              }}>
                <Box sx={{ 
                  width: 64, 
                  height: 64, 
                  borderRadius: '50%', 
                  bgcolor: 'primary.light', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  mb: 3,
                }}>
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 11.5C21.0034 12.8199 20.6951 14.1219 20.1 15.3C19.3944 16.7118 18.3098 17.8992 16.9674 18.7293C15.6251 19.5594 14.0782 19.9994 12.5 20C11.1801 20.0035 9.87812 19.6951 8.7 19.1L3 21L4.9 15.3C4.30493 14.1219 3.99656 12.8199 4 11.5C4.00061 9.92179 4.44061 8.37488 5.27072 7.03258C6.10083 5.69028 7.28825 4.6056 8.7 3.90003C9.87812 3.30496 11.1801 2.99659 12.5 3.00003H13C15.0843 3.11502 17.053 3.99479 18.5291 5.47089C20.0052 6.94699 20.885 8.91568 21 11V11.5Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </Box>
                <Typography variant="h4" sx={{ mb: 2, fontWeight: 600, color: 'text.primary' }}>
                  Welcome to IntelliAssistant
                </Typography>
                <Typography variant="body1" sx={{ mb: 4, maxWidth: 600, color: 'text.secondary' }}>
                  Select a dataset and ask me anything about your data! I can help you analyze trends, visualize information, and extract insights.
                </Typography>
                
                <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600, color: 'text.primary' }}>
                  Try these example queries:
                </Typography>
                
                <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 1 }}>
                  <Button 
                    variant="outlined" 
                    size="medium"
                    onClick={() => handleSuggestedQuery("Summarize this dataset. Please include a visualization of the results.")}
                    sx={{ 
                      borderColor: 'rgba(0, 0, 0, 0.12)', 
                      color: 'text.primary',
                      '&:hover': {
                        borderColor: 'primary.main',
                        bgcolor: 'rgba(37, 99, 235, 0.04)',
                      }
                    }}
                  >
                    Summarize this dataset
                  </Button>
                  <Button 
                    variant="outlined" 
                    size="medium"
                    onClick={() => handleSuggestedQuery("What are the top 5 trends in this data?")}
                    sx={{ 
                      borderColor: 'rgba(0, 0, 0, 0.12)', 
                      color: 'text.primary',
                      '&:hover': {
                        borderColor: 'primary.main',
                        bgcolor: 'rgba(37, 99, 235, 0.04)',
                      }
                    }}
                  >
                    Top 5 trends
                  </Button>
                  <Button 
                    variant="outlined" 
                    size="medium"
                    onClick={() => handleSuggestedQuery("Create a visualization showing the relationship between key variables.")}
                    sx={{ 
                      borderColor: 'rgba(0, 0, 0, 0.12)', 
                      color: 'text.primary',
                      '&:hover': {
                        borderColor: 'primary.main',
                        bgcolor: 'rgba(37, 99, 235, 0.04)',
                      }
                    }}
                  >
                    Visualize relationships
                  </Button>
                </Box>
              </Box>
            ) : (
              messages.map((message, index) => (
                <ChatMessage 
                  key={index} 
                  message={message} 
                  isLoading={index === messages.length - 1 && isLoading} 
                />
              ))
            )}
            <div ref={messagesEndRef} />
          </Box>
          
          {/* Message Input */}
          <Box sx={{ 
            p: 2, 
            borderTop: '1px solid rgba(0, 0, 0, 0.08)', 
            bgcolor: 'background.paper',
            width: '100%',
            boxSizing: 'border-box'
          }}>
            <Paper
              elevation={0}
              sx={{
                display: 'flex',
                alignItems: 'center',
                p: 1,
                pl: 2,
                borderRadius: 2,
                border: '1px solid rgba(0, 0, 0, 0.1)',
                '&:focus-within': {
                  borderColor: 'primary.main',
                  boxShadow: '0 0 0 2px rgba(37, 99, 235, 0.15)'
                }
              }}
            >
              <TextField
                fullWidth
                variant="standard"
                placeholder={selectedDataset ? "Ask me about your data..." : "Select a dataset to get started"}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                disabled={!selectedDataset || isLoading}
                InputProps={{
                  disableUnderline: true,
                }}
                sx={{
                  '& .MuiInputBase-input': {
                    py: 1,
                  }
                }}
              />
              <IconButton 
                color="primary"
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || !selectedDataset || isLoading}
                sx={{
                  bgcolor: inputValue.trim() && selectedDataset && !isLoading ? 'primary.main' : 'action.disabledBackground',
                  color: inputValue.trim() && selectedDataset && !isLoading ? 'white' : 'text.disabled',
                  '&:hover': {
                    bgcolor: inputValue.trim() && selectedDataset && !isLoading ? 'primary.dark' : 'action.disabledBackground',
                  },
                  '&.Mui-disabled': {
                    bgcolor: 'action.disabledBackground',
                    color: 'text.disabled',
                  },
                  width: 36,
                  height: 36,
                  mr: 0.5
                }}
              >
                <SendIcon fontSize="small" />
              </IconButton>
            </Paper>
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default ChatPage;
