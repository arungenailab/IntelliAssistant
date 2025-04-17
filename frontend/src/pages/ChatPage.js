import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Button, CircularProgress, useMediaQuery } from '@mui/material';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import { sendMessage, getConversationHistory, getConversationMessages, getDatasets, convertNaturalLanguageToSql } from '../api/chatApi';
import { useTheme } from '../contexts/ThemeContext';
import { useTheme as useMuiTheme, createTheme } from '@mui/material/styles';

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
  const [currentUser, setCurrentUser] = useState({ name: 'User', email: 'user@example.com' });
  const [suggestedQueries, setSuggestedQueries] = useState([
    {
      icon: "📊",
      title: "Sales Analysis",
      text: "Show total sales by country"
    },
    {
      icon: "🔄",
      title: "Product Comparison",
      text: "Compare sales across different products"
    },
    {
      icon: "📈",
      title: "Trend Analysis",
      text: "Analyze sales trends over time"
    },
    {
      icon: "🏆",
      title: "Top Customers",
      text: "Show top 5 customers by amount"
    }
  ]);
  
  const [datasetDialogOpen, setDatasetDialogOpen] = useState(false);
  const [availableDatasets, setAvailableDatasets] = useState([]);
  const [awaitingDatasetSelection, setAwaitingDatasetSelection] = useState(false);
  const [pendingQuery, setPendingQuery] = useState(null);
  const [currentTheme, setCurrentTheme] = useState(document.documentElement.classList.contains('dark') ? 'dark' : 'light');
  
  const [hasShownInitialDatasetPrompt, setHasShownInitialDatasetPrompt] = useState(false);
  
  const messagesEndRef = useRef(null);
  const [lastProcessedMessageId, setLastProcessedMessageId] = useState(null);

  // SQL-related state
  const [sqlCredentials, setSqlCredentials] = useState(null);
  const [isSqlMode, setIsSqlMode] = useState(false);
  const [databaseContext, setDatabaseContext] = useState([]);

  // Check if we're on a mobile screen
  const { darkMode } = useTheme();
  const muiTheme = useMuiTheme();
  const isMobile = useMediaQuery(muiTheme.breakpoints.down('md'));

  // Style constants for a cleaner layout
  const mainBgColor = darkMode ? 'hsl(0, 0%, 8%)' : 'hsl(0, 0%, 100%)';
  const borderColor = darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';

  // Check if the query specifically mentions any database tables
  const referencesStoredTable = (query) => {
    try {
      const storedDDL = localStorage.getItem('sqlDatabaseDDL');
      if (!storedDDL) {
        console.log('No stored DDL found in localStorage');
        return false;
      }
      
      const ddlObj = JSON.parse(storedDDL);
      if (!ddlObj || !ddlObj.tables) {
        console.log('No tables found in DDL structure');
        return false;
      }
      
      const availableTables = Object.keys(ddlObj.tables);
      const queryLower = query.toLowerCase();
      
      // Check if the query specifically mentions any table name
      const matchedTables = availableTables.filter(table => 
        queryLower.includes(table.toLowerCase())
      );
      
      if (matchedTables.length > 0) {
        console.log(`Query references database tables: ${matchedTables.join(', ')}`);
        return true;
      }
      
      console.log('No specific table references found in query. Available tables:', availableTables.join(', '));
      return false;
    } catch (e) {
      console.error('Error checking stored tables:', e);
      return false;
    }
  };

  // Improved isPotentiallySqlQuery function
  const isPotentiallySqlQuery = (message) => {
    // If the message specifically references a database table, it's very likely an SQL query
    if (referencesStoredTable(message)) {
      console.log('Query references a specific database table, treating as SQL query');
      return true;
    }
    
    const sqlKeywords = [
      'database', 'sql', 'query', 'table', 'select', 'show', 'find', 
      'rows', 'data from', 'report', 'count', 'total', 'average', 
      'how many', 'list all', 'what is the', 'what are the'
    ];
    
    const lowerMessage = message.toLowerCase();
    
    // Check if message contains SQL-related keywords
    return sqlKeywords.some(keyword => lowerMessage.includes(keyword)) && 
           // And appears to be asking for data
           (lowerMessage.includes('?') || 
            lowerMessage.startsWith('show') || 
            lowerMessage.startsWith('list') || 
            lowerMessage.startsWith('get') || 
            lowerMessage.startsWith('find'));
  };

  // Execute a SQL query from natural language
  const executeSqlQuery = async (query, conversationId, credentials, databaseContext = []) => {
    try {
      // Create loading message
      const loadingMessageId = Date.now().toString();
      const loadingMessage = {
        id: loadingMessageId,
        role: 'assistant',
        content: 'Converting your question to SQL and fetching results...',
        timestamp: new Date().toISOString(),
        is_loading: true
      };
      
      setMessages(msgs => [...msgs, loadingMessage]);
      
      // Get conversation history for context
      const conversationHistory = messages
        .filter(msg => !msg.is_loading)
        .slice(-6)  // Use last 6 messages for context
        .map(msg => ({
          role: msg.role,
          content: msg.content
        }));
      
      // Always double-check DDL for improved table context - this is critical for proper grounding
      let availableTables = [];
      let dbStructure = null;
      try {
        console.log('Checking for stored DDL before SQL generation...');
        const storedDDL = localStorage.getItem('sqlDatabaseDDL');
        if (storedDDL) {
          console.log('Found stored DDL, parsing...');
          try {
            dbStructure = JSON.parse(storedDDL);
            if (dbStructure?.tables) {
              availableTables = Object.keys(dbStructure.tables);
              console.log(`Available database tables: ${availableTables.join(', ')}`);
              
              // Debug: Print the actual column names for the Clients table
              if (dbStructure.tables['Clients']) {
                const clientColumns = dbStructure.tables['Clients'].map(col => col.column_name);
                console.log(`Clients table columns: ${clientColumns.join(', ')}`);
                
                // Print detailed info about each column for better debugging
                console.log('Detailed Clients table schema:');
                dbStructure.tables['Clients'].forEach(col => {
                  console.log(`- ${col.column_name} (${col.data_type}${col.is_primary_key === 'YES' ? ', PRIMARY KEY' : ''})`);
                });
              } else {
                console.warn('Clients table not found in schema');
              }
              
              // Debug the structure
              console.log('Loaded DDL structure details:', {
                tablesCount: availableTables.length,
                relationshipsCount: dbStructure.relationships?.length || 0,
                indexesCount: dbStructure.indexes?.length || 0,
                firstTableExample: availableTables.length > 0 ? 
                  dbStructure.tables[availableTables[0]][0] : null
              });
              
              // Always override database context with available tables
              if (availableTables.length > 0) {
                console.log('Overriding database context with tables from DDL');
                databaseContext = availableTables;
              }
            } else {
              console.warn('No tables found in DDL structure');
            }
          } catch (parseError) {
            console.error('Error parsing stored DDL:', parseError);
          }
        } else {
          console.warn('No DDL stored in localStorage');
        }
      } catch (e) {
        console.error("Error accessing stored DDL:", e);
      }
      
      // If we still have no table context, inform the user
      if ((!databaseContext || databaseContext.length === 0) && (!dbStructure || !dbStructure.tables)) {
        // Update the loading message with a warning
        const errorMessage = {
          id: loadingMessageId,
          role: 'assistant',
          content: 'I need to know what tables exist in your database to convert your question to SQL. Please save your database connection with schema information first.',
          timestamp: new Date().toISOString(),
        };
        
        setMessages(msgs => 
          msgs.map(msg => 
            msg.id === loadingMessageId ? errorMessage : msg
          )
        );
        return null;
      }
      
      // Log what context we're sending to the API
      console.log('Sending SQL query with database context:', databaseContext);
      
      // Call the API to convert natural language to SQL
      const response = await convertNaturalLanguageToSql(
        query,
        credentials,
        databaseContext,
        conversationHistory,
        true,  // Execute the query
        1000   // Limit to 1000 rows
      );
      
      // If SQL generation failed with an invalid table error, show available tables
      if (response.error && response.error.includes("Invalid object name") && availableTables.length > 0) {
        const errorMessage = {
          id: loadingMessageId,
          role: 'assistant',
          content: `I couldn't find the table mentioned in your query. Here are the tables available in your database: ${availableTables.join(', ')}. Please try again with one of these tables.`,
          timestamp: new Date().toISOString(),
        };
        
        setMessages(msgs => 
          msgs.map(msg => 
            msg.id === loadingMessageId ? errorMessage : msg
          )
        );
        return null;
      }
      
      // Create response message with SQL results
      const sqlContent = displaySQLResults({
        sql: response.sql,
        explanation: response.explanation,
        result: response.result,
        confidence: response.confidence || 0
      });
      
      const responseMessage = {
        id: loadingMessageId,
        role: 'assistant',
        content: sqlContent || 'No results found for your query.',
        timestamp: new Date().toISOString(),
        sql_result: {
          sql: response.sql,
          explanation: response.explanation,
          results: response.result,
          error: response.error,
          confidence: response.confidence || 0,
          visualization: response.visualization
        }
      };
      
      // Update the loading message with the response
      setMessages(msgs => 
        msgs.map(msg => 
          msg.id === loadingMessageId ? responseMessage : msg
        )
      );
      
      return responseMessage;
    } catch (error) {
      console.error('Error executing SQL query:', error);
      
      // Update loading message with error
      const errorMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `I encountered an error while processing your SQL query: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      
      setMessages(msgs => 
        msgs.filter(msg => !msg.is_loading).concat([errorMessage])
      );
      
      return null;
    }
  };

  // Process a natural language query as SQL
  const processNaturalLanguageAsSql = async (query, conversationId) => {
    try {
      // If SQL credentials are not set, ask for them
      if (!sqlCredentials) {
        const defaultCredentials = {
          server: localStorage.getItem('sqlServer') || '',
          database: localStorage.getItem('sqlDatabase') || '',
          username: localStorage.getItem('sqlUsername') || '',
          password: localStorage.getItem('sqlPassword') || '',
          encrypt: true
        };
        
        // For demo purposes, use saved credentials if available
        if (defaultCredentials.server && defaultCredentials.database) {
          setSqlCredentials(defaultCredentials);
          
          // Get the database context if available (tables to include for schema)
          let databaseContext = [];
          
          // Use DDL if stored during connection save
          try {
            const storedDDL = localStorage.getItem('sqlDatabaseDDL');
            if (storedDDL) {
              const ddlObj = JSON.parse(storedDDL);
              // Extract table names from the DDL
              if (ddlObj && ddlObj.tables) {
                databaseContext = Object.keys(ddlObj.tables);
              }
            }
          } catch (e) {
            console.warn('Error parsing stored DDL:', e);
          }
          
          return await executeSqlQuery(query, conversationId, defaultCredentials, databaseContext);
        }
        
        // Otherwise, show a prompt asking for connection info
        const newMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: 'To execute SQL queries, I need database connection details. Please provide your SQL Server connection information.',
          timestamp: new Date().toISOString()
        };
        
        setMessages(msgs => [...msgs, newMessage]);
        return { success: false, error: 'SQL credentials not set' };
      }
      
      // Execute with existing credentials
      return await executeSqlQuery(query, conversationId, sqlCredentials);
    } catch (error) {
      console.error('Error processing natural language as SQL:', error);
      return { success: false, error: error.message || 'Error processing SQL query' };
    }
  };

  // Load database schema on component mount
  useEffect(() => {
    try {
      const storedDDL = localStorage.getItem('sqlDatabaseDDL');
      if (storedDDL) {
        const ddlObj = JSON.parse(storedDDL);
        if (ddlObj?.tables) {
          const tableNames = Object.keys(ddlObj.tables);
          console.log(`Found ${tableNames.length} tables in localStorage: ${tableNames.join(', ')}`);
          
          // Set database context for use in queries
          setDatabaseContext(tableNames);
        } else {
          console.warn('No tables found in stored DDL');
        }
      } else {
        console.warn('No sqlDatabaseDDL found in localStorage');
      }
    } catch (error) {
      console.error('Error parsing sqlDatabaseDDL:', error);
    }
  }, []);

  useEffect(() => {
    // Load conversation history when component mounts
    const loadHistory = async () => {
      try {
        const history = await getConversationHistory();
        if (history && history.length > 0) {
          setConversationHistory(history);
        }
      } catch (error) {
        console.error('Error loading conversation history:', error);
      }
    };
    
    // Try to load previously selected dataset from localStorage
    try {
      const savedDataset = localStorage.getItem('selectedDataset');
      if (savedDataset) {
        const parsedDataset = JSON.parse(savedDataset);
        console.log('Loaded previously selected dataset from localStorage:', parsedDataset);
        setSelectedDataset(parsedDataset);
      }
    } catch (error) {
      console.error('Error loading dataset from localStorage:', error);
    }
    
    // Load available datasets
    const loadDatasets = async () => {
      try {
        console.log('Fetching datasets from API...');
        const datasetsData = await getDatasets();
        console.log('Raw datasets response:', datasetsData);
        
        if (datasetsData && Object.keys(datasetsData).length > 0) {
          // Transform the datasets object into an array format for the UI
          const datasetsArray = Object.entries(datasetsData).map(([id, dataset]) => {
            console.log(`Processing dataset ${id}:`, dataset);
            return {
              id,
              name: dataset.name || id,
              description: dataset.description || 'Dataset', // Keep description clean without row count
              rows: dataset.rows || null
            };
          });
          console.log('Transformed datasets array:', datasetsArray);
          setAvailableDatasets(datasetsArray);
        } else {
          // If no datasets are returned from the API, populate with test data
          console.warn('No datasets returned from API, using test datasets');
          const testDatasets = [
            { id: 'msft', name: 'MSFT', description: 'Microsoft financial data', rows: null },
            { id: 'sales_data', name: 'Sales Data', description: 'Product sales across regions and time periods', rows: null },
          ];
          console.log('Using test datasets:', testDatasets);
          setAvailableDatasets(testDatasets);
        }
      } catch (error) {
        console.error('Error loading datasets:', error);
        // Populate with test data in case of error
        const testDatasets = [
          { id: 'msft', name: 'MSFT', description: 'Microsoft financial data', rows: null },
          { id: 'sales_data', name: 'Sales Data', description: 'Product sales across regions and time periods', rows: null },
        ];
        console.log('Using test datasets due to error:', testDatasets);
        setAvailableDatasets(testDatasets);
      }
    };
    
    loadHistory();
    loadDatasets();
  }, []);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    // Show dataset prompt when datasets are loaded and none is selected
    // This code is now disabled to prevent auto-loading the dataset selection prompt
    // The prompt will only be shown when user specifically asks about data
    
    /* Original code removed:
    if (availableDatasets.length > 0 && !selectedDataset && !hasShownInitialDatasetPrompt) {
      console.log('Showing initial dataset prompt');
      setHasShownInitialDatasetPrompt(true);
      
      const datasetPromptMessage = {
        id: Date.now(),
        role: 'assistant',
        content: `Before we begin, please select a dataset to work with:
        
${availableDatasets.map((dataset, index) => formatDatasetInfo(dataset)).join('\n\n')}

Please reply with the dataset name or number you'd like to use.`,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, datasetPromptMessage]);
      setAwaitingDatasetSelection(true);
    }
    */
  }, [availableDatasets, selectedDataset, hasShownInitialDatasetPrompt]);

  const handleDatasetSelect = (dataset) => {
    console.log('Dataset selected:', dataset);
    setSelectedDataset(dataset);
    setAwaitingDatasetSelection(false);
    
    // Store the selected dataset in localStorage to persist across page refreshes
    try {
      localStorage.setItem('selectedDataset', JSON.stringify(dataset));
    } catch (error) {
      console.error('Error storing dataset in localStorage:', error);
    }
    
    // Add a message to confirm dataset selection
    const confirmationMessage = {
      id: Date.now(),
      role: 'assistant',
      content: `I'll use the "${dataset.name}" dataset for your query.`,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, confirmationMessage]);
    
    if (pendingQuery) {
      // Wait a moment before sending the actual query to allow the UI to update
      setTimeout(() => {
        // Create a new query that doesn't mention the dataset to avoid loops
        const cleanedQuery = pendingQuery.replace(new RegExp(dataset.name, 'i'), '')
                                       .replace(new RegExp(dataset.id, 'i'), '')
                                       .trim();
        
        // Only proceed if we have a valid query after cleaning
        if (cleanedQuery) {
          handleSendMessage(cleanedQuery, dataset.id);
        } else {
          // If query becomes empty after removing dataset references, use a generic query
          handleSendMessage("Please provide an overview of this dataset", dataset.id);
        }
        setPendingQuery(null);
      }, 100);
    }
  };

  const handleSendMessage = async (message, specificDatasetId = null) => {
    if (!message) return;
    
    // Create user message object
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    
    // Always add the user message to the state first
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    
    // If we're awaiting dataset selection, don't process this as a normal message
    // Let the dataset selection effect handler take care of it
    if (awaitingDatasetSelection) {
      console.log('Not processing as normal message - awaiting dataset selection');
      return;
    }
    
    // Enhanced data terms list with more specific patterns
    const dataTerms = ['chart', 'plot', 'graph', 'data', 'dataset', 'analyze', 'visualize', 
                      'visualization', 'trend', 'compare', 'comparison', 'sales', 'metrics', 
                      'statistics', 'figures', 'numbers', 'total', 'average', 'sum', 'count', 
                      'by country', 'by region', 'by product', 'top', 'customers', 'amount',
                      'highest', 'lowest', 'most', 'least', 'best', 'worst', 'ranking', 'rank',
                      'performance', 'revenue', 'profit'];
    
    // Enhanced detection for specific queries about sales by location
    const salesByLocationPattern = /show\s+(total\s+)?sales\s+by\s+(country|region|location)/i;
    const isSalesByLocation = salesByLocationPattern.test(message);
    
    // Add conversational intent detection
    const greetingPatterns = [
      /^(hi|hello|hey|greetings|howdy)(\s|$|\W)/i,
      /^good\s+(morning|afternoon|evening|day)/i,
      /^what'?s?\s+up/i,
      /^how\s+are\s+you/i
    ];
    
    const isGreeting = greetingPatterns.some(pattern => pattern.test(message.trim()));
    
    // Handle small talk patterns
    const smallTalkPatterns = {
      thanks: /^(thanks|thank\s+you|thx)/i,
      bye: /^(goodbye|bye|see\s+you|cya|ttyl)/i,
      help: /^(help|assist|support|how\s+do\s+you\s+work)/i,
      capabilities: /^(what\s+can\s+you\s+do|abilities|functions|features|capabilities)/i,
      identity: /^(who\s+are\s+you|what\s+are\s+you|your\s+name)/i
    };
    
    // Check if the message matches any small talk pattern
    const smallTalkIntent = Object.keys(smallTalkPatterns).find(intent => 
      smallTalkPatterns[intent].test(message.trim())
    );
    
    // Debug: Log intent detection
    console.log('Intent detection:', {
      message,
      isGreeting,
      smallTalkIntent,
      requiresDataset: dataTerms.some(term => message.toLowerCase().includes(term)),
      isSalesByLocation
    });
    
    // Handle conversational intents first, before any data processing
    if (isGreeting || smallTalkIntent) {
      console.log('Handling conversational intent');
      setIsLoading(true);
      
      // Create a temporary loading message
      const loadingMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: '...',
        timestamp: new Date().toISOString(),
        isLoading: true
      };
      
      setMessages(prev => [...prev, loadingMessage]);
      
      // Wait a short moment to simulate thinking (optional)
      setTimeout(() => {
        // Remove the loading message
        setMessages(prev => prev.filter(msg => !msg.isLoading));
        
        let response = '';
        
        if (isGreeting) {
          const greetingResponses = [
            "Hello! How can I help with your data questions today?",
            "Hi there! I'm ready to assist with analyzing your data.",
            "Hey! What would you like to know about your data today?",
            "Greetings! I'm here to help with data analysis and insights."
          ];
          response = greetingResponses[Math.floor(Math.random() * greetingResponses.length)];
        } else if (smallTalkIntent) {
          switch (smallTalkIntent) {
            case 'thanks':
              response = "You're welcome! Let me know if you need anything else.";
              break;
            case 'bye':
              response = "Goodbye! Feel free to return anytime you need data insights.";
              break;
            case 'help':
              response = "I can help you analyze data, create visualizations, and extract insights. Try asking questions like 'Show sales by region' or 'What are the top customers by revenue?'";
              break;
            case 'capabilities':
              response = "I can analyze data, generate visualizations, identify trends, and answer questions about your datasets. Just ask me anything about your data in plain language.";
              break;
            case 'identity':
              response = "I'm IntelliAssistant, your intelligent data analysis companion. I'm designed to help you understand and visualize your data.";
              break;
            default:
              response = "I'm here to help with your data questions. What would you like to analyze today?";
          }
        }
        
        const conversationalMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: response,
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, conversationalMessage]);
        setIsLoading(false);
      }, 500);
      
      return;
    }
    
    // Debug: Log current dataset state
    console.log('Current dataset state:', {
      selectedDataset,
      awaitingDatasetSelection,
      pendingQuery,
      messageRequiresDataset: dataTerms.some(term => message.toLowerCase().includes(term)),
      isSalesByLocation,
      availableDatasets: availableDatasets.length
    });
    
    // Improved follow-up query detection for more natural conversations
    const followUpPatterns = [
      /^(what|how) about/i,           // "What about..."
      /^show me/i,                    // "Show me..."
      /^tell me/i,                    // "Tell me..."
      /^can you (show|tell|give)/i,   // "Can you show/tell/give..."
      /^list/i,                       // "List..."
      /^give me/i,                    // "Give me..."
      /^and/i,                        // "And..."
      /^also/i,                       // "Also..."
      /^what if/i,                    // "What if..."
      /^now/i,                        // "Now..."
      /^(how|what) many/i,            // "How many..."/"What many..."
      /^which/i                       // "Which..."
    ];
    
    // Check if any follow-up pattern matches
    const isFollowUpQuery = followUpPatterns.some(pattern => pattern.test(message.trim())) || 
                           message.split(' ').length <= 5;  // Short queries are likely follow-ups
    
    // Always use selectedDataset if available
    let isForceDatasetQuery = selectedDataset !== null;
    
    // If this is specifically a follow-up query and we have a previously selected dataset, log it
    if (isFollowUpQuery && selectedDataset) {
      console.log('Detected follow-up query, will reuse dataset:', selectedDataset.name);
      isForceDatasetQuery = true;
    }
    
    // Combined check for if the query requires a dataset
    // Check for SQL first - if it's a SQL query, it shouldn't go through the dataset path
    if (isPotentiallySqlQuery(message)) {
      console.log('Detected SQL query:', message);
      setIsLoading(true);
      const response = await processNaturalLanguageAsSql(message, activeConversation);
      setIsLoading(false);
      return;
    }
    
    // Only check for dataset requirements if it's not an SQL query
    const requiresDataset = isForceDatasetQuery || 
                         isSalesByLocation ||
                         dataTerms.some(term => message.toLowerCase().includes(term));
    
    // If a specific dataset ID was provided, use it directly without detection
    let datasetToUse = specificDatasetId;
    
    // If we have a selected dataset, always use it for data queries
    if (selectedDataset && requiresDataset) {
      console.log('Using selected dataset for data query:', selectedDataset.name);
      datasetToUse = selectedDataset.id;
    }
    
    // Only prompt for dataset selection if no specific dataset was provided
    // and no dataset is selected, but the query requires one
    if (!specificDatasetId && !selectedDataset && requiresDataset) {
      console.log('Query requires dataset but none selected, prompting for selection', {
        requiresDataset,
        isSalesByLocation,
        message,
        availableDatasets: availableDatasets.length
      });
      
      if (availableDatasets.length > 0) {
        setIsLoading(false);
        setAwaitingDatasetSelection(true);
        setPendingQuery(message);
        
        // Format datasets for display with more information
        const datasetOptions = availableDatasets.map((dataset, index) => formatDatasetInfo(dataset)).join('\n\n');
        
        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: `Your query about "${getTopicFromQuery(message)}" requires a dataset. Please choose one:

${datasetOptions}

Please type the number or name of the dataset you want to use.`,
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        return;
      } else {
        // If query requires a dataset but no datasets are available
        setIsLoading(false);
        
        const noDatasetMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: `I cannot process your query about "${getTopicFromQuery(message)}" because it requires data analysis, but no datasets are available in the system. Please contact your administrator to set up datasets.`,
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, noDatasetMessage]);
        return;
      }
    }

    // Create a temporary loading message
    const loadingMessage = {
      id: Date.now() + 1,
      role: 'assistant',
      content: 'Analyzing your request...',
      timestamp: new Date().toISOString(),
      isLoading: true
    };
    
    setMessages(prev => [...prev, loadingMessage]);
    setIsLoading(true);
    
    try {
      // Enhance query with visualization request if needed
      let enhancedQuery = message;
      
      // Check if query is about data but doesn't mention visualization
      const visualizationTerms = ['chart', 'graph', 'plot', 'visualize', 'visualization'];
      
      const mentionsVisualization = visualizationTerms.some(term => message.toLowerCase().includes(term));
      
      // Only enhance with visualization if we have a dataset
      if (requiresDataset && datasetToUse) {
        enhancedQuery = `${message}. Please include a visualization of the results.`;
      }
      
      console.log('Sending message to API:', {
        message: enhancedQuery,
        conversationId: activeConversation,
        datasetId: datasetToUse,
        useCache: true
      });
      
      const response = await sendMessage(
        enhancedQuery, 
        activeConversation,
        datasetToUse,
        'gemini-2.0-flash',
        true
      );
      
      console.log('API response:', response);
      
      // Remove the loading message
      setMessages(prev => prev.filter(msg => !msg.isLoading));
      
      // Process visualization data only if the API call was successful
      let visualizationData = null;
      if (response && !response.error && response.visualization) {
        try {
          // If visualization is a string, parse it
          if (typeof response.visualization === 'string') {
            visualizationData = JSON.parse(response.visualization);
          } else {
            visualizationData = response.visualization;
          }
        } catch (error) {
          console.error('Error parsing visualization data:', error);
          // Don't generate sample visualization if we hit an error parsing
          visualizationData = null;
        }
      }
      
      // If there was an API error but the query required a dataset and none was selected,
      // direct the user to select a dataset first
      if (response.error && (requiresDataset || isSalesByLocation) && !datasetToUse && availableDatasets.length > 0) {
        console.log('API error with dataset query but no dataset selected', {
          error: response.error,
          requiresDataset,
          isSalesByLocation,
          datasetToUse,
          availableDatasets: availableDatasets.length
        });
        const errorMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: `I couldn't complete your query about "${getTopicFromQuery(message)}" because it requires a dataset. Please select one of the available datasets first:
            
${availableDatasets.map(dataset => formatDatasetInfo(dataset)).join('\n')}

Which dataset would you like to use?`,
          timestamp: new Date().toISOString(),
          // Don't include visualization data for dataset selection prompts
          error: null
        };
        
        setMessages(prev => [...prev, errorMessage]);
        setAwaitingDatasetSelection(true);
        setPendingQuery(message);
      } else {
        // Normal response processing
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
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Remove the loading message
      setMessages(prev => prev.filter(msg => !msg.isLoading));
      
      // If the query required a dataset and none was selected, prompt for dataset selection
      if (requiresDataset && !datasetToUse && availableDatasets.length > 0) {
        console.log('Query requires dataset but no dataset selected, prompting for selection', {
          requiresDataset,
          isSalesByLocation,
          message,
          availableDatasets: availableDatasets.length
        });
        const errorMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: `I couldn't process your query about "${getTopicFromQuery(message)}" because it requires a dataset. Please select one of these datasets:
          
${availableDatasets.map(dataset => formatDatasetInfo(dataset)).join('\n')}

Which one would you like to use?`,
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, errorMessage]);
      } else {
        // Generic error message for other types of errors
        const errorMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your request. Please try again.',
          timestamp: new Date().toISOString(),
          error: error.message,
          // Don't include visualization for error messages
          visualization: null
        };
        
        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedQuery = (query) => {
    setInputValue(query);
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
      queries.push({
        icon: "📊",
        title: "Data Analysis",
        text: `Show total ${numericColumns[0]} by ${categoryColumns[0] || 'category'}`
      });
      
      if (timeColumns.length > 0) {
        queries.push({
          icon: "📈",
          title: "Trend Analysis",
          text: `Analyze ${numericColumns[0]} trends over time`
        });
      }
    }
    
    if (categoryColumns.length > 0) {
      queries.push({
        icon: "🔄",
        title: "Category Comparison",
        text: `Compare data across different ${categoryColumns[0]}`
      });
    }
    
    // Add some general analysis queries
    queries.push({
      icon: "💡",
      title: "Key Insights",
      text: "Show key insights from the data"
    });
    
    queries.push({
      icon: "📊",
      title: "Visualizations",
      text: "Create a visualization showing relationships between variables"
    });
    
    return queries;
  };

  // Add a function to handle SQL queries
  const handleSqlQuery = (query) => {
    console.log('SQL Query:', query);
    // Here you would typically execute the query
    // For now we just log it
  };

  // Helper function to extract potential dataset name from a message
  function extractDatasetName(msg) {
    // Common patterns for dataset mentions
    const patterns = [
      /use\s+(?:the\s+)?([a-z0-9\s]+)\s+(?:data|dataset)/i,
      /(?:the\s+)?([a-z0-9\s]+)\s+(?:data|dataset)/i,
      /([a-z0-9\s]+)\s+sales/i,
      /([a-z0-9\s]+)\s+inventory/i,
      /([a-z0-9\s]+)\s+customers/i,
      /([a-z0-9\s]+)\s+marketing/i
    ];
    
    for (const pattern of patterns) {
      const match = msg.match(pattern);
      if (match && match[1]) {
        // Only extract if it's not an empty string or common filler words
        const candidate = match[1].trim().toLowerCase();
        if (candidate && !['about', 'for', 'on', 'from', 'me', 'the'].includes(candidate)) {
          return match[1].trim();
        }
      }
    }
    
    return null;
  }
  
  // Helper function to check if a dataset name is in our available datasets
  function isInAvailableDatasets(name) {
    if (!name || name.trim() === '') return false;
    
    // Normalize the name for comparison
    const normalizedName = name.toLowerCase();
    
    // Check for exact matches first
    const exactMatch = availableDatasets.some(dataset => 
      dataset.name.toLowerCase() === normalizedName || 
      dataset.id.toLowerCase() === normalizedName
    );
    
    if (exactMatch) return true;
    
    // If no exact match, check for partial matches with high confidence
    // Require the dataset name to be at least 4 characters for partial matching
    // to avoid false positives with short words
    if (normalizedName.length >= 4) {
      return availableDatasets.some(dataset => 
        (dataset.name.toLowerCase().includes(normalizedName) && normalizedName.length > 3) || 
        (normalizedName.includes(dataset.name.toLowerCase()) && dataset.name.toLowerCase().length > 3) ||
        (dataset.id.toLowerCase().includes(normalizedName) && normalizedName.length > 3) ||
        (normalizedName.includes(dataset.id.toLowerCase()) && dataset.id.toLowerCase().length > 3)
      );
    }
    
    return false;
  }
  
  // Helper function to extract the main topic from a query
  function getTopicFromQuery(query) {
    const keywords = query.toLowerCase().split(/\s+/).filter(word => 
      word.length > 3 && 
      !['what', 'show', 'tell', 'give', 'how', 'where', 'when', 'which', 'find', 'about', 'with'].includes(word)
    );
    
    return keywords.length > 0 ? keywords.slice(0, 3).join(' ') : 'this topic';
  }
  
  // Helper function to get the most relevant dataset suggestion based on query
  function getRelevantDatasetSuggestion(query, datasets) {
    if (!datasets || datasets.length === 0) return '';
    
    // Default to the first dataset if no match
    let relevantDataset = datasets[0].name;
    
    // Simple keyword matching - this could be enhanced with more sophisticated matching
    const queryLower = query.toLowerCase();
    
    // Look for exact dataset name mentions first - direct match takes priority
    const directMatch = datasets.find(dataset => 
      queryLower.includes(dataset.name.toLowerCase()) || 
      queryLower.includes(dataset.id.toLowerCase())
    );
    
    if (directMatch) {
      return directMatch.name;
    }
    
    // Otherwise, look for keyword matches
    if (queryLower.includes('sales') || queryLower.includes('revenue') || queryLower.includes('profit')) {
      const salesDataset = datasets.find(d => 
        d.name.toLowerCase().includes('sales') || 
        d.id.toLowerCase().includes('sales')
      );
      if (salesDataset) return salesDataset.name;
    }
    
    if (queryLower.includes('customer') || queryLower.includes('client') || queryLower.includes('user')) {
      const customerDataset = datasets.find(d => 
        d.name.toLowerCase().includes('customer') || 
        d.id.toLowerCase().includes('customer') ||
        d.name.toLowerCase().includes('client') || 
        d.id.toLowerCase().includes('client')
      );
      if (customerDataset) return customerDataset.name;
    }
    
    // Return the first dataset as a fallback
    return datasets[0].name;
  }
  
  // Helper function to format available datasets for display
  function formatDatasetInfo(dataset) {
    if (!dataset) return '';
    
    // Show row count only if it exists
    const rowsInfo = dataset.rows ? ` (${dataset.rows.toLocaleString()} rows)` : '';
    
    return `• **${dataset.name}**: ${dataset.description || ''}${rowsInfo}`;
  }

  // Helper function to format available datasets for display
  function formatAvailableDatasets(datasets) {
    if (!datasets || datasets.length === 0) return 'No datasets available';
    
    return datasets.map(dataset => formatDatasetInfo(dataset)).join('\n\n');
  }

  // Handle dataset selection separate from normal message processing
  useEffect(() => {
    // Skip if not awaiting dataset selection or no messages
    if (!awaitingDatasetSelection || !messages.length) return;
    
    // Get the most recent user message
    const userMessages = messages.filter(msg => msg.role === 'user');
    if (!userMessages.length) return;
    
    const lastUserMessage = userMessages[userMessages.length - 1];
    
    // Skip if we've already processed this message
    if (lastUserMessage.id === lastProcessedMessageId) {
      console.log('Skipping already processed message for dataset selection');
      return;
    }
    
    console.log('Processing user message for dataset selection:', lastUserMessage.content);
    
    // Handle numeric dataset selection
    const numMatch = lastUserMessage.content.match(/^(\d+)$/);
    if (numMatch) {
      const datasetIndex = parseInt(numMatch[1], 10) - 1;
      if (datasetIndex >= 0 && datasetIndex < availableDatasets.length) {
        console.log(`Numeric selection: Found dataset at index ${datasetIndex}:`, availableDatasets[datasetIndex]);
        handleDatasetSelect(availableDatasets[datasetIndex]);
        setLastProcessedMessageId(lastUserMessage.id);
        return;
      }
    }
    
    // Look for dataset name matches
    for (const dataset of availableDatasets) {
      if (lastUserMessage.content.toLowerCase().includes(dataset.name.toLowerCase()) ||
          lastUserMessage.content.toLowerCase().includes(dataset.id.toLowerCase())) {
        console.log('Text selection: Found dataset match:', dataset);
        handleDatasetSelect(dataset);
        setLastProcessedMessageId(lastUserMessage.id);
        return;
      }
    }
    
    // Cancel selection if requested
    if (lastUserMessage.content.toLowerCase() === 'cancel' || 
        lastUserMessage.content.toLowerCase().includes('nevermind') || 
        lastUserMessage.content.toLowerCase().includes('never mind')) {
      console.log('Dataset selection canceled by user');
      setAwaitingDatasetSelection(false);
      setPendingQuery(null);
      
      const cancelMessage = {
        id: Date.now(),
        role: 'assistant',
        content: 'Dataset selection canceled. How else can I assist you?',
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, cancelMessage]);
      setLastProcessedMessageId(lastUserMessage.id);
      return;
    }
    
    // If we get here, the message didn't match any dataset
    // Only respond if we haven't already processed this message
    if (lastUserMessage.id !== lastProcessedMessageId) {
      // User's response didn't match any dataset, send clearer instructions
      const retryMessage = {
        id: Date.now(),
        role: 'assistant',
        content: `I didn't recognize that as a dataset. Please choose one by typing its number or name:

${formatAvailableDatasets(availableDatasets)}

Or type "cancel" to abandon this query.`,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, retryMessage]);
      setLastProcessedMessageId(lastUserMessage.id);
    }
  }, [messages, awaitingDatasetSelection, availableDatasets, pendingQuery, lastProcessedMessageId]);

  // Process and display SQL query results in chat
  const displaySQLResults = (sqlData) => {
    if (!sqlData || !sqlData.sql) return null;
    
    // Return the special marker that tells the ChatMessage component to use the SQLResultView
    return '__SQL_RESULT_VIEW__';
  };
  
  // Format query results as a table
  const formatResultsTable = (results) => {
    if (!results || results.length === 0) return "No records";
    
    try {
      // Get column names from the first row
      const columns = Object.keys(results[0]);
      
      // For clients table, use a specific order of columns
      const orderedColumns = results[0].hasOwnProperty('ClientID') ? 
        ['ClientID', 'ClientName', 'ContactPerson', 'Email', 'Phone', 'CreatedDate'] :
        columns;
      
      // Create the header row
      let table = orderedColumns.join(" | ") + "\n";
      table += orderedColumns.map(() => "---").join(" | ") + "\n";
      
      // Add data rows
      results.forEach(row => {
        const rowValues = orderedColumns.map(col => {
          const value = row[col];
          return value !== null && value !== undefined ? String(value) : "";
        });
        table += rowValues.join(" | ") + "\n";
      });
      
      return "```\n" + table + "```";
    } catch (error) {
      console.error("Error formatting results table:", error);
      return "Error formatting results";
    }
  };

  // Render the chat interface without redundant sidebar
  return (
    <Box 
      sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        height: '100%',
        width: '100%',
        position: 'relative',
        bgcolor: mainBgColor,
        overflow: 'hidden',
      }}
    >
      {/* Main chat area */}
      <Box 
        sx={{ 
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          paddingBottom: '120px', // Increased to accommodate the input area smoothly
        }}
      >
        {/* Messages content */}
        <Box 
          ref={messagesEndRef}
          sx={{ 
            flexGrow: 1, 
            overflow: 'auto',
            display: 'flex',
            justifyContent: 'center',
            width: '100%',
          }}
        >
          <Box sx={{ 
            width: '100%', 
            maxWidth: '48rem', 
            px: { xs: 2, sm: 4 },
            pt: { xs: 2, sm: 3 },
          }}>
            {/* Empty state with centered content */}
            {messages.length === 0 && !isLoading && (
              <Box 
                sx={{ 
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  textAlign: 'center',
                  pt: { xs: 4, sm: 6 },
                  pb: { xs: 6, sm: 10 }
                }}
              >
                <Typography 
                  variant="h4" 
                  component="h1" 
                  sx={{ 
                    fontWeight: 600,
                    fontSize: { xs: '1.5rem', sm: '1.75rem' },
                    mb: 1.5,
                    color: darkMode ? 'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.87)',
                  }}
                >
                  IntelliAssistant
                </Typography>
                
                <Typography 
                  variant="subtitle1" 
                  sx={{ 
                    mb: 3,
                    opacity: 0.8,
                    fontSize: '0.95rem',
                    maxWidth: '36rem',
                  }}
                >
                  Your intelligent data assistant. Ask anything about your data.
                </Typography>
              </Box>
            )}

            {/* Message display */}
            {messages.map((msg, index) => (
              <ChatMessage
                key={index}
                message={msg}
                isUser={msg.role === 'user'}
                isLoading={false}
                onSqlQuery={handleSqlQuery}
              />
            ))}
            
            {/* Thinking indicator */}
            {isLoading && (
              <ChatMessage
                message={{ 
                  role: 'assistant', 
                  content: '', 
                  timestamp: new Date().toISOString() 
                }}
                isUser={false}
                isLoading={true}
                onSqlQuery={handleSqlQuery}
              />
            )}
          </Box>
        </Box>
      </Box>
      
      {/* Unified input area without borders */}
      <Box 
        sx={{ 
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: 10,
          display: 'flex',
          justifyContent: 'center',
          pb: { xs: 1.5, sm: 2 },
          pt: { xs: 2, sm: 2.5 },
          bgcolor: mainBgColor,
          background: darkMode 
            ? `linear-gradient(to bottom, rgba(0, 0, 0, 0), ${mainBgColor} 15%)`
            : `linear-gradient(to bottom, rgba(255, 255, 255, 0), ${mainBgColor} 15%)`,
          boxShadow: '0 -2px 15px rgba(0,0,0,0.03)',
        }}
      >
        <Box sx={{ 
          width: '100%',
          maxWidth: '48rem',
          px: { xs: 2, sm: 4 },
        }}>
          {/* Suggested queries above input only when no messages */}
          {messages.length === 0 && !isLoading && (
            <Box sx={{ 
              display: 'flex', 
              flexWrap: 'wrap',
              gap: 1,
              mb: 1.5,
              justifyContent: 'center',
            }}>
              {suggestedQueries.slice(0, 4).map((query, index) => (
                <Button
                  key={index}
                  size="small"
                  variant="outlined"
                  onClick={() => handleSuggestedQuery(query.text)}
                  sx={{
                    minWidth: 'auto',
                    py: 0.5,
                    px: 1.5,
                    borderRadius: '16px',
                    borderColor: darkMode ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.1)',
                    fontSize: '0.8rem',
                    color: 'text.secondary',
                    '&:hover': {
                      borderColor: 'primary.main',
                      bgcolor: darkMode ? 'rgba(37, 99, 235, 0.1)' : 'rgba(37, 99, 235, 0.05)',
                    },
                    transition: 'all 0.2s ease',
                  }}
                >
                  {query.text}
                </Button>
              ))}
            </Box>
          )}

          <ChatInput
            message={inputValue}
            setMessage={setInputValue}
            handleSend={handleSendMessage}
            disabled={isLoading}
            isLoading={isLoading}
            placeholder={messages.length === 0 ? "Ask me anything about your data..." : "Type your message..."}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default ChatPage;
