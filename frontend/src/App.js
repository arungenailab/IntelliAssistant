import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { 
  CssBaseline, 
  AppBar, 
  Toolbar, 
  Typography, 
  Box, 
  Button, 
  Container,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  IconButton
} from '@mui/material';
import { 
  Chat as ChatIcon, 
  BarChart as BarChartIcon,
  Home as HomeIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon
} from '@mui/icons-material';
import ChatPage from './pages/ChatPage';
import DataPage from './pages/DataPage';
import './App.css';

// Create a theme
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

// Drawer width
const drawerWidth = 240;

function App() {
  const [drawerOpen, setDrawerOpen] = useState(true);

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', height: '100vh' }}>
          {/* Sidebar */}
          <Drawer
            variant="permanent"
            open={drawerOpen}
            sx={{
              width: drawerOpen ? drawerWidth : 0,
              flexShrink: 0,
              transition: theme => theme.transitions.create('width', {
                easing: theme.transitions.easing.sharp,
                duration: theme.transitions.duration.enteringScreen,
              }),
              '& .MuiDrawer-paper': {
                width: drawerWidth,
                boxSizing: 'border-box',
                overflowX: 'hidden',
                transition: theme => theme.transitions.create('width', {
                  easing: theme.transitions.easing.sharp,
                  duration: theme.transitions.duration.enteringScreen,
                }),
                width: drawerOpen ? drawerWidth : 60,
                whiteSpace: 'nowrap',
              },
            }}
          >
            <Toolbar sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              px: [1]
            }}>
              <Typography variant="h6" noWrap component="div" sx={{ 
                opacity: drawerOpen ? 1 : 0,
                transition: 'opacity 0.2s'
              }}>
                IntelliAssistant
              </Typography>
              <IconButton onClick={toggleDrawer}>
                {drawerOpen ? <ChevronLeftIcon /> : <MenuIcon />}
              </IconButton>
            </Toolbar>
            <Divider />
            <List>
              <ListItem button component={Link} to="/" sx={{ 
                px: drawerOpen ? 2 : 1,
                justifyContent: drawerOpen ? 'initial' : 'center'
              }}>
                <ListItemIcon sx={{ 
                  minWidth: drawerOpen ? 36 : 'auto',
                  mr: drawerOpen ? 3 : 'auto'
                }}>
                  <HomeIcon />
                </ListItemIcon>
                <ListItemText primary="Home" sx={{ opacity: drawerOpen ? 1 : 0 }} />
              </ListItem>
              <ListItem button component={Link} to="/chat" sx={{ 
                px: drawerOpen ? 2 : 1,
                justifyContent: drawerOpen ? 'initial' : 'center'
              }}>
                <ListItemIcon sx={{ 
                  minWidth: drawerOpen ? 36 : 'auto',
                  mr: drawerOpen ? 3 : 'auto'
                }}>
                  <ChatIcon />
                </ListItemIcon>
                <ListItemText primary="Chat" sx={{ opacity: drawerOpen ? 1 : 0 }} />
              </ListItem>
              <ListItem button component={Link} to="/data" sx={{ 
                px: drawerOpen ? 2 : 1,
                justifyContent: drawerOpen ? 'initial' : 'center'
              }}>
                <ListItemIcon sx={{ 
                  minWidth: drawerOpen ? 36 : 'auto',
                  mr: drawerOpen ? 3 : 'auto'
                }}>
                  <BarChartIcon />
                </ListItemIcon>
                <ListItemText primary="Data Analysis" sx={{ opacity: drawerOpen ? 1 : 0 }} />
              </ListItem>
              <ListItem button component={Link} to="/settings" sx={{ 
                px: drawerOpen ? 2 : 1,
                justifyContent: drawerOpen ? 'initial' : 'center'
              }}>
                <ListItemIcon sx={{ 
                  minWidth: drawerOpen ? 36 : 'auto',
                  mr: drawerOpen ? 3 : 'auto'
                }}>
                  <SettingsIcon />
                </ListItemIcon>
                <ListItemText primary="Settings" sx={{ opacity: drawerOpen ? 1 : 0 }} />
              </ListItem>
            </List>
          </Drawer>

          {/* Main content */}
          <Box
            component="main"
            sx={{ 
              flexGrow: 1, 
              bgcolor: 'background.default', 
              p: 0,
              height: '100vh',
              overflow: 'auto'
            }}
          >
            {/* Toggle button for small screens */}
            <AppBar 
              position="fixed" 
              color="default" 
              elevation={0}
              sx={{ 
                display: { sm: 'none' },
                borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
                zIndex: theme => theme.zIndex.drawer + 1
              }}
            >
              <Toolbar>
                <IconButton
                  color="inherit"
                  aria-label="open drawer"
                  edge="start"
                  onClick={toggleDrawer}
                  sx={{ mr: 2 }}
                >
                  <MenuIcon />
                </IconButton>
                <Typography variant="h6" noWrap component="div">
                  IntelliAssistant
                </Typography>
              </Toolbar>
            </AppBar>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/data" element={<DataPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

// Simple HomePage component
const HomePage = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          height: 'calc(100vh - 64px)',
          textAlign: 'center'
        }}
      >
        <Typography variant="h2" gutterBottom>
          Welcome to IntelliAssistant
        </Typography>
        <Typography variant="h5" gutterBottom color="textSecondary">
          Your AI-powered data analysis companion
        </Typography>
        <Box sx={{ mt: 4, display: 'flex', gap: 2 }}>
          <Button 
            variant="contained" 
            size="large" 
            startIcon={<ChatIcon />}
            component={Link}
            to="/chat"
          >
            Start Chatting
          </Button>
          <Button 
            variant="outlined" 
            size="large" 
            startIcon={<BarChartIcon />}
            component={Link}
            to="/data"
          >
            Analyze Data
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

// Simple SettingsPage component
const SettingsPage = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1">
        Settings page is under construction.
      </Typography>
    </Container>
  );
};

export default App;
