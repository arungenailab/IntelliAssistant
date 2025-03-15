import { Bell, Search } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { useTheme } from "../../contexts/ThemeContext";
import { Switch, Tooltip, Box, Typography } from "@mui/material";
import DarkModeIcon from '@mui/icons-material/DarkMode';
import LightModeIcon from '@mui/icons-material/LightMode';

export default function Header({ title }) {
  const { darkMode, toggleDarkMode } = useTheme();

  return (
    <header className="sticky top-0 z-30 border-b border-border backdrop-blur-md bg-background/70 px-6 py-4 flex items-center justify-between shadow-sm">
      <h1 className="text-xl font-semibold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">{title || 'IntelliAssistant'}</h1>
      
      <div className="flex items-center gap-4">
        <div className="relative w-64">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            type="search" 
            placeholder="Search..." 
            className="pl-8 w-full"
          />
        </div>
        
        <Tooltip title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}>
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'center',
              bgcolor: darkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
              borderRadius: 2,
              p: '4px 8px',
              ml: 1,
            }}
          >
            <LightModeIcon 
              sx={{ 
                fontSize: '1.2rem', 
                color: darkMode ? 'text.disabled' : '#ff9800',
                mr: 0.5,
                transition: 'color 0.3s ease',
              }} 
            />
            <Switch
              checked={darkMode}
              onChange={toggleDarkMode}
              color="primary"
              size="small"
              inputProps={{ 'aria-label': 'Theme toggle' }}
              sx={{
                '& .MuiSwitch-switchBase.Mui-checked': {
                  color: darkMode ? '#90caf9' : '#1976d2',
                },
                '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                  backgroundColor: darkMode ? '#90caf9' : '#1976d2',
                },
              }}
            />
            <DarkModeIcon 
              sx={{ 
                fontSize: '1.2rem', 
                color: darkMode ? '#90caf9' : 'text.disabled',
                ml: 0.5,
                transition: 'color 0.3s ease',
              }} 
            />
            <Typography 
              variant="caption" 
              sx={{ 
                ml: 0.5, 
                userSelect: 'none',
                color: 'text.secondary',
                fontWeight: 500,
              }}
            >
              {darkMode ? 'Dark' : 'Light'}
            </Typography>
          </Box>
        </Tooltip>
        
        <Button variant="ghost" size="icon" className="relative rounded-full">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1.5 top-1.5 h-2.5 w-2.5 rounded-full bg-destructive animate-pulse"></span>
        </Button>
      </div>
    </header>
  );
} 