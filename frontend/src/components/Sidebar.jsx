import React, { useState } from 'react';
import { Box, Typography, Divider, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Avatar, IconButton, Tooltip } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { Brightness4, Brightness7, Settings, Message, Storage, CloudUpload, Api, Dashboard, Add, Menu as MenuIcon, ChevronLeft } from '@mui/icons-material';

const Sidebar = ({ isMobile, toggleSidebar }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isDarkMode, toggleTheme } = useTheme();
  const [isExpanded, setIsExpanded] = useState(true);

  const menuItems = [
    { text: 'Chat', icon: <Message />, path: '/' },
    { text: 'Data', icon: <Dashboard />, path: '/data' },
    { text: 'Datasets', icon: <Storage />, path: '/datasets' },
    { text: 'Upload', icon: <CloudUpload />, path: '/upload' },
    { text: 'API Data', icon: <Api />, path: '/api-data' },
    { text: 'Settings', icon: <Settings />, path: '/settings' },
  ];

  const handleNavigation = (path) => {
    navigate(path);
    if (isMobile) {
      toggleSidebar();
    }
  };

  // Colors for the active item indicator
  const activeIndicatorColor = isDarkMode ? 'rgba(0, 166, 126, 0.2)' : 'rgba(0, 166, 126, 0.1)';
  const hoverColor = isDarkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)';

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        bgcolor: isDarkMode ? 'hsl(0, 0%, 10%)' : 'hsl(0, 0%, 98%)',
        borderRight: '1px solid',
        borderColor: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
        width: isMobile ? '100%' : '260px',
        transition: 'all 0.3s ease',
      }}
    >
      {/* Header with title and mobile close button */}
      <Box 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          p: 2,
          borderBottom: '1px solid',
          borderColor: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
        }}
      >
        <Typography variant="h6" sx={{ 
          fontWeight: 600, 
          fontSize: '1.1rem',
          color: isDarkMode ? 'hsl(0, 0%, 95%)' : 'hsl(0, 0%, 20%)',
        }}>
          IntelliAssistant
        </Typography>
        
        {isMobile && (
          <IconButton onClick={toggleSidebar} size="small">
            <ChevronLeft />
          </IconButton>
        )}
      </Box>

      {/* New conversation button */}
      <Box sx={{ p: 2 }}>
        <ListItemButton
          onClick={() => handleNavigation('/')}
          sx={{
            border: '1px solid',
            borderColor: isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.15)',
            borderRadius: '8px',
            py: 1,
            '&:hover': {
              bgcolor: activeIndicatorColor,
            },
            transition: 'all 0.2s',
          }}
        >
          <ListItemIcon sx={{ minWidth: '36px', color: 'primary.main' }}>
            <Add sx={{ fontSize: '1.2rem' }} />
          </ListItemIcon>
          <ListItemText 
            primary="New Chat" 
            primaryTypographyProps={{ 
              sx: { 
                fontSize: '0.9rem',
                fontWeight: 500,
              }
            }} 
          />
        </ListItemButton>
      </Box>

      {/* Main navigation */}
      <List sx={{ flexGrow: 1, px: 1, pt: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
              sx={{
                borderRadius: '6px',
                py: 1,
                bgcolor: location.pathname === item.path ? activeIndicatorColor : 'transparent',
                '&:hover': {
                  bgcolor: location.pathname === item.path ? activeIndicatorColor : hoverColor,
                },
                '&.Mui-selected': {
                  bgcolor: activeIndicatorColor,
                  '&:hover': {
                    bgcolor: activeIndicatorColor,
                  }
                }
              }}
            >
              <ListItemIcon 
                sx={{ 
                  minWidth: '36px',
                  color: location.pathname === item.path ? 'primary.main' : 'text.secondary',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text} 
                primaryTypographyProps={{ 
                  sx: { 
                    fontSize: '0.9rem',
                    fontWeight: location.pathname === item.path ? 500 : 400,
                  }
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* Footer with theme toggle and user profile */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderTop: '1px solid',
          borderColor: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Avatar 
            sx={{ 
              width: 32, 
              height: 32,
              bgcolor: 'primary.main',
              fontSize: '0.9rem',
            }}
          >
            U
          </Avatar>
          <Typography 
            variant="body2" 
            sx={{ 
              ml: 1.5,
              fontSize: '0.85rem',
              fontWeight: 500,
            }}
          >
            User
          </Typography>
        </Box>
        
        <Tooltip title={isDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}>
          <IconButton onClick={toggleTheme} color="inherit">
            {isDarkMode ? <Brightness7 fontSize="small" /> : <Brightness4 fontSize="small" />}
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
};

export default Sidebar; 