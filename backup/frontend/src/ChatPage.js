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

// Create a theme for the dialog
const theme = createTheme({
  palette: {
    primary: {
      main: '#3366ff',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#f5f7fa',
    },
  },
  typography: {
    fontFamily: [
      'Segoe UI',
      'Roboto',
      'Helvetica',
      'Arial',
      'sans-serif',
    ].join(','),
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8,
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
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Left Sidebar - Conversation History */}
      <Box sx={{ 
        width: sidebarOpen ? 280 : 0, 
        borderRight: '1px solid #e0e0e0', 
        p: sidebarOpen ? 2 : 0,
        bgcolor: '#fff',
        overflow: 'hidden',
        transition: 'width 0.3s, padding 0.3s',
        position: 'relative',
        flexShrink: 0 // Prevent sidebar from shrinking
      }}>
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          mb: 2
        }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
            Data Analysis Assistant
          </Typography>
        </Box>
        
        <Button 
          variant="contained" 
          fullWidth 
          sx={{ mb: 3 }}
          onClick={handleNewChat}
        >
          New Chat
        </Button>
        
        <ChatHistory 
          conversations={conversationHistory}
          activeConversation={activeConversation}
          onSelectConversation={handleSelectConversation}
        />
      </Box>
      
      {/* Toggle button for sidebar */}
      <Box sx={{ 
        position: 'absolute', 
        left: sidebarOpen ? 280 : 0, 
        top: '50%',
        zIndex: 10,
        transition: 'left 0.3s',
        transform: 'translateY(-50%)'
      }}>
        <IconButton 
          onClick={toggleSidebar}
          sx={{ 
            bgcolor: 'white', 
            boxShadow: 2,
            '&:hover': { bgcolor: 'white' }
          }}
          size="small"
        >
          {sidebarOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
        </IconButton>
      </Box>
      
      {/* Main Chat Area */}
      <Box sx={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column', 
        height: '100%',
        width: `calc(100% - ${sidebarOpen ? 280 : 0}px)`, // Adjust width based on sidebar state
        marginLeft: sidebarOpen ? 0 : '40px', // Add margin when sidebar is collapsed to account for toggle button
        transition: 'width 0.3s, margin-left 0.3s',
        position: 'relative' // Ensure proper positioning of children
      }}>
        {/* Dataset Selector - Hidden but still functional */}
        <Box sx={{ 
          position: 'absolute', 
          top: 0, 
          right: 0, 
          zIndex: 5, 
          p: 1,
          display: 'flex',
          alignItems: 'center',
          bgcolor: 'rgba(255, 255, 255, 0.9)',
          borderRadius: '0 0 0 8px',
          boxShadow: 1
        }}>
          <Typography variant="body2" sx={{ mr: 2, fontWeight: 'medium' }}>
            Selected Dataset: {selectedDataset ? selectedDataset.name : 'None'}
          </Typography>
          <Button 
            variant="outlined" 
            size="small"
            onClick={() => {
              // Open a dialog to select dataset
              const datasetDialog = document.createElement('div');
              datasetDialog.style.position = 'fixed';
              datasetDialog.style.top = '50%';
              datasetDialog.style.left = '50%';
              datasetDialog.style.transform = 'translate(-50%, -50%)';
              datasetDialog.style.zIndex = '1000';
              datasetDialog.style.backgroundColor = 'white';
              datasetDialog.style.padding = '20px';
              datasetDialog.style.borderRadius = '8px';
              datasetDialog.style.boxShadow = '0 4px 20px rgba(0,0,0,0.1)';
              datasetDialog.style.width = '500px';
              datasetDialog.style.maxHeight = '80vh';
              datasetDialog.style.overflow = 'auto';
              
              // Render the DatasetSelector in the dialog
              const root = ReactDOM.createRoot(datasetDialog);
              root.render(
                <ThemeProvider theme={theme}>
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6">Select Dataset</Typography>
                      <IconButton onClick={() => {
                        document.body.removeChild(datasetDialog);
                      }}>
                        <CloseIcon />
                      </IconButton>
                    </Box>
                    <DatasetSelector onDatasetSelect={(name, info) => {
                      handleDatasetSelect(name, info);
                      document.body.removeChild(datasetDialog);
                    }} />
                  </Box>
                </ThemeProvider>
              );
              
              document.body.appendChild(datasetDialog);
            }}
          >
            Change Dataset
          </Button>
        </Box>
        
        {/* Chat Messages */}
        <Box sx={{ 
          flex: 1, 
          p: 3, 
          pt: 6, // Add padding to top to account for the dataset selector
          overflowY: 'auto', 
          bgcolor: '#f5f7fa', 
          height: 'calc(100% - 70px)', // Adjust height to account for input area
          width: '100%', // Ensure full width
          boxSizing: 'border-box' // Include padding in width calculation
        }}>
          {messages.length === 0 ? (
            // Welcome screen with example queries
            <Box sx={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
              color: 'text.secondary'
            }}>
              <Typography variant="h4" sx={{ mb: 2, fontWeight: 'bold' }}>
                Welcome to IntelliAssistant
              </Typography>
              <Typography variant="body1" sx={{ mb: 4 }}>
                Select a dataset and ask me anything about your data!
              </Typography>
              
              <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
                Try these example queries:
              </Typography>
              
              <Grid container spacing={2} sx={{ maxWidth: 600 }}>
                {suggestedQueries.map((query, index) => (
                  <Grid item xs={12} sm={6} key={index}>
                    <Paper
                      sx={{
                        p: 2,
                        cursor: 'pointer',
                        '&:hover': {
                          bgcolor: 'action.hover'
                        }
                      }}
                      onClick={() => handleSuggestedQuery(query)}
                    >
                      <Typography variant="body2">{query}</Typography>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </Box>
          ) : (
            // Chat messages
            <>
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  isLoading={isLoading && message.id === messages[messages.length - 1].id}
                />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </Box>
        
        {/* Message Input */}
        <Box sx={{ 
          p: 2, 
          borderTop: '1px solid #e0e0e0', 
          bgcolor: '#fff',
          width: '100%',
          boxSizing: 'border-box'
        }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Ask me about your data..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                disabled={!selectedDataset || isLoading}
              />
            </Grid>
            <Grid item>
              <IconButton 
                color="primary"
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || !selectedDataset || isLoading}
              >
                <SendIcon />
              </IconButton>
            </Grid>
          </Grid>
        </Box>
      </Box>
    </Box>
  );
};

export default ChatPage;
