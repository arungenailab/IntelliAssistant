import React, { useState, useEffect, useRef } from 'react';
import { Box, Grid, Typography, Paper, IconButton, TextField, Button, Divider, List, ListItem, ListItemText, Avatar, CircularProgress, Alert, Dialog, DialogTitle, DialogContent } from '@mui/material';
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
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import { useTheme } from '../contexts/ThemeContext';
import ChatInput from '../components/ChatInput';

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
  const [datasetDialogOpen, setDatasetDialogOpen] = useState(false);
  const [currentTheme, setCurrentTheme] = useState(document.documentElement.classList.contains('dark') ? 'dark' : 'light');
  
  const messagesEndRef = useRef(null);

  // Listen for theme changes
  useEffect(() => {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          const newTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
          setCurrentTheme(newTheme);
        }
      });
    });

    observer.observe(document.documentElement, { attributes: true });

    return () => {
      observer.disconnect();
    };
  }, []);

  // Update theme when currentTheme changes
  useEffect(() => {
    theme.palette.mode = currentTheme;
    theme.palette.background.default = currentTheme === 'dark' ? '#121212' : '#f9fafb';
    theme.palette.background.paper = currentTheme === 'dark' ? '#1e1e1e' : '#ffffff';
    theme.palette.text.primary = currentTheme === 'dark' ? '#e0e0e0' : '#111827';
    theme.palette.text.secondary = currentTheme === 'dark' ? '#a0a0a0' : '#6b7280';
  }, [currentTheme]);

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

  const handleSendMessage = async (message, modelId = 'gemini-2.0-flash', useCache = true) => {
    if (!message.trim()) return;
    
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
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
      let enhancedQuery = message;
      
      // Check if query is about data but doesn't mention visualization
      const dataTerms = ['data', 'analyze', 'show', 'display', 'chart', 'graph'];
      const visualizationTerms = ['chart', 'graph', 'plot', 'visualize', 'visualization'];
      
      const isDataQuery = dataTerms.some(term => message.toLowerCase().includes(term));
      const mentionsVisualization = visualizationTerms.some(term => message.toLowerCase().includes(term));
      
      if (isDataQuery && !mentionsVisualization && selectedDataset) {
        enhancedQuery = `${message}. Please include a visualization of the results.`;
      }
      
      const response = await sendMessage(
        enhancedQuery, 
        activeConversation,
        selectedDataset?.name,
        modelId,
        useCache
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
        error: response.error,
        model_used: response.model_used,
        model_version: response.model_version,
        is_fallback: response.is_fallback
      };
      
      setMessages(prev => [...prev, botMessage]);
      
      // If this is a new conversation, update the active conversation
      if (!activeConversation && response.conversationId) {
        setActiveConversation(response.conversationId);
        // Update conversation history
        setConversationHistory(prev => [
          { 
            id: response.conversationId, 
            title: message, 
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

  const handleConversationSelect = async (conversation) => {
    try {
      setActiveConversation(conversation);
      const messages = await getConversationMessages(conversation.id);
      setMessages(messages);
    } catch (error) {
      console.error('Error loading conversation messages:', error);
    }
  };

  const handleNewChat = () => {
    setActiveConversation(null);
    setMessages([]);
  };

  const handleSuggestedQuery = (query) => {
    setInputValue(query);
  };

  const handleDatasetSelect = (datasetName, details) => {
    setSelectedDataset({ name: datasetName, ...details });
    setDatasetDialogOpen(false);
    
    // Update suggested queries based on dataset columns
    if (details && details.columns) {
      const newQueries = generateQueriesFromColumns(details.columns);
      setSuggestedQueries(newQueries);
    }
  };

  const generateQueriesFromColumns = (columns) => {
    const queries = [];
    const numericColumns = columns.filter(col => 
      col.toLowerCase().includes('amount') || 
      col.toLowerCase().includes('price') || 
      col.toLowerCase().includes('quantity') ||
      col.toLowerCase().includes('sales')
    );
    
    const timeColumns = columns.filter(col => 
      col.toLowerCase().includes('date') || 
      col.toLowerCase().includes('time') || 
      col.toLowerCase().includes('year')
    );
    
    const categoryColumns = columns.filter(col => 
      col.toLowerCase().includes('category') || 
      col.toLowerCase().includes('type') || 
      col.toLowerCase().includes('region') ||
      col.toLowerCase().includes('country')
    );
    
    if (numericColumns.length > 0) {
      queries.push(`Show total ${numericColumns[0]} by ${categoryColumns[0] || 'category'}`);
      if (timeColumns.length > 0) {
        queries.push(`Analyze ${numericColumns[0]} trends over time`);
      }
    }
    
    if (categoryColumns.length > 0) {
      queries.push(`Compare data across different ${categoryColumns[0]}`);
    }
    
    // Add some general analysis queries
    queries.push("Show key insights from the data");
    queries.push("Create a visualization showing relationships between variables");
    
    return queries;
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        overflow: 'hidden',
        bgcolor: (theme) => theme.palette.background.default,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          height: '100%',
          overflow: 'hidden',
        }}
      >
        {/* Sidebar */}
        <Box
          sx={{
            width: { 
              xs: sidebarOpen ? '260px' : '0px', 
              md: sidebarOpen ? '260px' : '72px' 
            },
            flexShrink: 0,
            transition: 'width 0.2s ease-in-out',
            height: '100%',
            borderRight: (theme) => `1px solid ${theme.palette.divider}`,
            bgcolor: (theme) => theme.palette.background.paper,
            boxShadow: 'none',
            zIndex: 10,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Sidebar Header */}
          <Box
            sx={{
              p: { xs: 2, md: sidebarOpen ? 2 : 1 },
              display: 'flex',
              alignItems: 'center',
              justifyContent: sidebarOpen ? 'space-between' : 'center',
              borderBottom: (theme) => `1px solid ${theme.palette.divider}`,
              minHeight: '64px',
            }}
          >
            {sidebarOpen ? (
              <>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  <span style={{ color: (theme) => theme.palette.primary.main }}>Intelli</span>Assistant
                </Typography>
                
                <Button
                  variant="contained"
                  size="small"
                  sx={{
                    borderRadius: '8px',
                    textTransform: 'none',
                    py: 0.5,
                    px: 1.5,
                    fontWeight: 600,
                    minWidth: 0,
                  }}
                  startIcon={<AddIcon fontSize="small" />}
                  onClick={() => handleNewChat()}
                >
                  New Chat
                </Button>
              </>
            ) : (
              <IconButton
                size="small"
                color="primary"
                onClick={() => handleNewChat()}
                sx={{ 
                  bgcolor: (theme) => theme.palette.primary.main + '20',
                  '&:hover': {
                    bgcolor: (theme) => theme.palette.primary.main + '30',
                  }
                }}
              >
                <AddIcon fontSize="small" />
              </IconButton>
            )}
          </Box>
          
          {/* Conversations List */}
          <Box 
            sx={{ 
              flex: 1, 
              overflow: 'auto', 
              p: sidebarOpen ? 1.5 : 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: sidebarOpen ? 'stretch' : 'center',
            }}
          >
            {sidebarOpen ? (
              <ChatHistory
                conversations={conversationHistory}
                selectedConversation={activeConversation}
                onSelect={handleConversationSelect}
              />
            ) : (
              /* Minimized sidebar conversation indicators */
              conversationHistory.slice(0, 10).map((conversation, index) => (
                <Box 
                  key={index}
                  onClick={() => handleConversationSelect(conversation.id)}
                  sx={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: conversation.id === activeConversation ? 
                      (theme) => theme.palette.primary.main + '20' : 
                      'transparent',
                    color: conversation.id === activeConversation ?
                      (theme) => theme.palette.primary.main :
                      (theme) => theme.palette.text.secondary,
                    cursor: 'pointer',
                    mb: 1,
                    transition: 'all 0.2s',
                    '&:hover': {
                      backgroundColor: (theme) => theme.palette.primary.main + '10',
                    }
                  }}
                >
                  {index + 1}
                </Box>
              ))
            )}
          </Box>
          
          {/* Settings panel at bottom of sidebar */}
          <Box
            sx={{
              p: sidebarOpen ? 1.5 : 1,
              borderTop: (theme) => `1px solid ${theme.palette.divider}`,
              display: 'flex',
              justifyContent: sidebarOpen ? 'space-between' : 'center',
              alignItems: 'center',
              bgcolor: (theme) => 
                theme.palette.mode === 'dark' 
                  ? 'rgba(255, 255, 255, 0.05)' 
                  : 'rgba(0, 0, 0, 0.02)',
              minHeight: '56px',
            }}
          >
            {sidebarOpen ? (
              <DatasetSelector
                datasets={[]}
                selectedDataset={selectedDataset}
                onDatasetChange={handleDatasetSelect}
                sx={{ m: 0 }}
              />
            ) : (
              <IconButton
                size="small"
                color="inherit"
                onClick={() => setSidebarOpen(true)}
              >
                <ChevronRightIcon fontSize="small" />
              </IconButton>
            )}
          </Box>
        </Box>
        
        {/* Sidebar toggle button for mobile and desktop */}
        <IconButton
          onClick={() => setSidebarOpen(!sidebarOpen)}
          sx={{
            position: 'absolute',
            top: '12px',
            left: { 
              xs: sidebarOpen ? '220px' : '12px',
              md: sidebarOpen ? '220px' : '60px'
            },
            transition: 'left 0.2s ease-in-out',
            zIndex: 20,
            bgcolor: (theme) => theme.palette.background.paper,
            boxShadow: 1,
            width: '32px',
            height: '32px',
            '&:hover': {
              bgcolor: (theme) => theme.palette.background.paper,
            },
          }}
        >
          {sidebarOpen ? <ChevronLeftIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
        </IconButton>
        
        {/* Main content area */}
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            height: '100%',
            position: 'relative',
            overflow: 'hidden',
            ml: { xs: 0, md: 0 },
          }}
        >
          <Box
            sx={{
              borderBottom: (theme) => `1px solid ${theme.palette.divider}`,
              py: 1.5,
              px: 2,
              minHeight: '48px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              bgcolor: (theme) => theme.palette.background.paper,
              zIndex: 5,
              pl: { xs: sidebarOpen ? 2 : 6, md: 2 },
            }}
          >
            <Typography variant="subtitle1" sx={{ fontWeight: 500, color: 'text.primary' }}>
              {selectedDataset && `Dataset: ${selectedDataset}`}
            </Typography>
          </Box>
          
          {/* Messages area */}
          <Box
            sx={{
              flex: 1,
              overflow: 'auto',
              px: { xs: 0.5, sm: 1, md: 1.5 },
              py: 1,
              bgcolor: (theme) => theme.palette.background.default,
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <Box sx={{ 
              width: '100%', 
              maxWidth: '1000px', 
              mx: 'auto', 
              height: '100%',
              px: { xs: 0.5, sm: 1 },
            }}>
              {/* Welcome message */}
              {messages.length === 0 && (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    textAlign: 'center',
                    mt: { xs: 4, sm: 6, md: 8 },
                    mb: 2,
                    px: 1,
                  }}
                >
                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 600,
                      mb: 2,
                      background: (theme) => 
                        theme.palette.mode === 'dark'
                          ? 'linear-gradient(90deg, #60A5FA 0%, #8B5CF6 100%)'
                          : 'linear-gradient(90deg, #3B82F6 0%, #6366F1 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                    }}
                  >
                    Welcome to IntelliAssistant
                  </Typography>
                  
                  <Typography
                    variant="body1"
                    color="text.secondary"
                    sx={{ mb: 3, maxWidth: '600px' }}
                  >
                    Ask me anything about your data or explore insights with simple questions.
                  </Typography>
                  
                  <Box
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: { 
                        xs: '1fr', 
                        sm: 'repeat(2, 1fr)',
                        md: 'repeat(auto-fill, minmax(220px, 1fr))'
                      },
                      gap: 1.5,
                      width: '100%',
                      maxWidth: '900px',
                    }}
                  >
                    {suggestedQueries.map((query, index) => (
                      <Box
                        key={index}
                        onClick={() => handleSuggestedQuery(query)}
                        sx={{
                          p: 1.5,
                          borderRadius: 1.5,
                          border: (theme) => `1px solid ${theme.palette.divider}`,
                          bgcolor: (theme) => theme.palette.background.paper,
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: 1,
                            borderColor: 'primary.main',
                          },
                        }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {query}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </Box>
              )}
              
              {/* Messages */}
              <Box sx={{ 
                flexGrow: 1, 
                display: 'flex', 
                flexDirection: 'column', 
                justifyContent: messages.length > 0 ? 'flex-start' : 'flex-end',
                py: 1,
                mt: messages.length > 0 ? 1 : 0,
              }}>
                {messages.map((message, index) => (
                  <ChatMessage
                    key={index}
                    message={message}
                    isLoading={index === messages.length - 1 && isLoading}
                  />
                ))}
              
                {/* Auto-scroll anchor */}
                <div ref={messagesEndRef} />
              </Box>
            </Box>
          </Box>
          
          {/* Input area */}
          <Box
            sx={{
              p: { xs: 1, sm: 1.5 },
              bgcolor: (theme) => theme.palette.background.paper,
              borderTop: (theme) => `1px solid ${theme.palette.divider}`,
              zIndex: 5,
            }}
          >
            <ChatInput
              message={inputValue}
              setMessage={setInputValue}
              handleSend={handleSendMessage}
              isLoading={isLoading}
              placeholder={
                isLoading
                  ? "Generating response..."
                  : "Ask IntelliAssistant anything..."
              }
              disabled={isLoading}
              selectedModel={null}
              onModelChange={() => {}}
              useCache={true}
              onCacheToggle={() => {}}
            />
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default ChatPage;
