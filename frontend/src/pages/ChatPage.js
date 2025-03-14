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
    <ThemeProvider theme={theme}>
      <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.default' }}>
        {/* Sidebar */}
        <Box
          sx={{
            width: sidebarOpen ? 300 : 0,
            flexShrink: 0,
            transition: 'width 0.2s',
            overflow: 'hidden',
            borderRight: '1px solid rgba(0, 0, 0, 0.12)',
            bgcolor: 'background.paper'
          }}
        >
          {/* Dataset Selection Button */}
          <Box sx={{ p: 2 }}>
            <Button
              fullWidth
              variant="outlined"
              onClick={() => setDatasetDialogOpen(true)}
              startIcon={<AttachFileIcon />}
              sx={{
                justifyContent: 'flex-start',
                mb: 2,
                borderColor: 'rgba(0, 0, 0, 0.12)',
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: 'rgba(37, 99, 235, 0.08)'
                }
              }}
            >
              {selectedDataset ? `Dataset: ${selectedDataset.name}` : 'Select Dataset'}
            </Button>
          </Box>
          
          {/* Rest of the sidebar content */}
          <ChatHistory 
            conversations={conversationHistory}
            activeConversation={activeConversation}
            onConversationSelect={handleConversationSelect}
          />
        </Box>

        {/* Main chat area */}
        <Box sx={{ flexGrow: 1, height: '100vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {/* Chat header */}
          <Box sx={{ 
            p: 2, 
            borderBottom: '1px solid rgba(0, 0, 0, 0.12)', 
            bgcolor: 'background.paper',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <Typography variant="h6" component="div">
              {activeConversation ? activeConversation.title : 'New Chat'}
            </Typography>
            <Box>
              <IconButton onClick={toggleSidebar} size="small">
                {sidebarOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
              </IconButton>
            </Box>
          </Box>

          {/* Messages area */}
          <Box sx={{ 
            flexGrow: 1, 
            overflowY: 'auto',
            p: 2,
            display: 'flex',
            flexDirection: 'column',
            gap: 2
          }}>
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                isLoading={message.isLoading}
              />
            ))}
            <div ref={messagesEndRef} />
          </Box>

          {/* Suggested queries */}
          {suggestedQueries.length > 0 && messages.length === 0 && (
            <Box sx={{ p: 2, borderTop: '1px solid rgba(0, 0, 0, 0.12)' }}>
              <Typography variant="subtitle2" sx={{ mb: 1, color: 'text.secondary' }}>
                Suggested queries:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {suggestedQueries.map((query, index) => (
                  <Button
                    key={index}
                    variant="outlined"
                    size="small"
                    onClick={() => {
                      setInputValue(query);
                      handleSendMessage(query);
                    }}
                    sx={{
                      borderColor: 'rgba(0, 0, 0, 0.12)',
                      color: 'text.primary',
                      '&:hover': {
                        borderColor: 'primary.main',
                        bgcolor: 'rgba(37, 99, 235, 0.08)'
                      }
                    }}
                  >
                    {query}
                  </Button>
                ))}
              </Box>
            </Box>
          )}

          {/* Input area */}
          <Box sx={{ 
            p: 2, 
            borderTop: '1px solid rgba(0, 0, 0, 0.12)', 
            bgcolor: 'background.paper'
          }}>
            <ChatInput
              onSendMessage={handleSendMessage}
              disabled={isLoading}
              placeholder="Ask a question about your data..."
            />
          </Box>
        </Box>

        {/* Dataset Selection Dialog */}
        <Dialog
          open={datasetDialogOpen}
          onClose={() => setDatasetDialogOpen(false)}
          maxWidth="md"
          fullWidth
          sx={{
            '& .MuiDialog-paper': {
              borderRadius: 2,
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
            }
          }}
        >
          <DialogTitle sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
            pb: 2
          }}>
            <Typography variant="h6" component="div">
              Select Dataset
            </Typography>
            <IconButton
              aria-label="close"
              onClick={() => setDatasetDialogOpen(false)}
              sx={{
                color: 'text.secondary',
                '&:hover': {
                  color: 'text.primary',
                  bgcolor: 'rgba(0, 0, 0, 0.04)'
                }
              }}
            >
              <CloseIcon />
            </IconButton>
          </DialogTitle>
          <DialogContent sx={{ pt: 2 }}>
            <DatasetSelector onDatasetSelect={handleDatasetSelect} />
          </DialogContent>
        </Dialog>
      </Box>
    </ThemeProvider>
  );
};

export default ChatPage;
