import React, { createContext, useState, useEffect, useContext } from 'react';
import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Create the context
export const ThemeContext = createContext({
  darkMode: false,
  toggleDarkMode: () => {},
});

// Custom hook to use the theme context
export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider = ({ children }) => {
  const [darkMode, setDarkMode] = useState(document.documentElement.classList.contains('dark'));

  // Define font configuration
  const fontFamily = [
    'Roboto',
    'Segoe UI',
    'Helvetica',
    'Arial',
    'sans-serif',
  ].join(',');

  // Create the light theme
  const lightTheme = createTheme({
    palette: {
      mode: 'light',
      primary: { 
        main: '#1976d2',
        light: '#4791db',
        dark: '#115293',
        contrastText: '#ffffff',
      },
      secondary: { 
        main: '#757575',
        light: '#919191',
        dark: '#5c5c5c',
        contrastText: '#ffffff',
      },
      background: { 
        default: '#ffffff', 
        paper: '#f5f5f5',
        chat: '#f8f8f8',
      },
      text: {
        primary: '#212121',
        secondary: '#757575',
      },
      success: {
        main: '#4caf50',
        light: '#81c784',
        dark: '#388e3c',
      },
      error: {
        main: '#f44336',
        light: '#e57373',
        dark: '#d32f2f',
      },
      warning: {
        main: '#ff9800',
        light: '#ffb74d',
        dark: '#f57c00',
      },
      info: {
        main: '#2196f3',
        light: '#64b5f6',
        dark: '#1976d2',
      },
      grey: {
        50: '#fafafa',
        100: '#f5f5f5',
        200: '#eeeeee',
        300: '#e0e0e0',
        400: '#bdbdbd',
        500: '#9e9e9e',
        600: '#757575',
        700: '#616161',
        800: '#424242',
        900: '#212121',
      },
    },
    typography: {
      fontFamily,
      h1: {
        fontWeight: 500,
        fontSize: '2.5rem',
        lineHeight: 1.5,
      },
      h2: {
        fontWeight: 500,
        fontSize: '2rem',
        lineHeight: 1.5,
      },
      h3: {
        fontWeight: 500,
        fontSize: '1.75rem',
        lineHeight: 1.5,
      },
      h4: {
        fontWeight: 500,
        fontSize: '1.5rem',
        lineHeight: 1.5,
      },
      h5: {
        fontWeight: 500,
        fontSize: '1.25rem',
        lineHeight: 1.5,
      },
      h6: {
        fontWeight: 500,
        fontSize: '1rem',
        lineHeight: 1.5,
      },
      subtitle1: {
        fontSize: '1rem',
        fontWeight: 500,
        lineHeight: 1.5,
      },
      subtitle2: {
        fontSize: '0.875rem',
        fontWeight: 500,
        lineHeight: 1.5,
      },
      body1: {
        fontSize: '1rem',
        fontWeight: 400,
        lineHeight: 1.5,
      },
      body2: {
        fontSize: '0.875rem',
        fontWeight: 400,
        lineHeight: 1.5,
      },
      button: {
        fontWeight: 500,
        fontSize: '0.875rem',
        textTransform: 'none',
        lineHeight: 1.5,
      },
      caption: {
        fontSize: '0.75rem',
        fontWeight: 400,
        lineHeight: 1.5,
      },
      overline: {
        fontWeight: 400,
        fontSize: '0.75rem',
        textTransform: 'uppercase',
        lineHeight: 1.5,
      },
    },
    shape: {
      borderRadius: 4,
    },
  });

  // Create the dark theme
  const darkTheme = createTheme({
    palette: {
      mode: 'dark',
      primary: { 
        main: '#90caf9',
        light: '#b3d9ff',
        dark: '#648dae',
        contrastText: '#121212',
      },
      secondary: { 
        main: '#bdbdbd',
        light: '#e6e6e6',
        dark: '#8d8d8d',
        contrastText: '#121212',
      },
      background: { 
        default: '#121212', 
        paper: '#1d1d1d',
        chat: '#1e1e1e',
      },
      text: {
        primary: '#ffffff',
        secondary: '#b0b0b0',
      },
      success: {
        main: '#6fba6f',
        light: '#98d598',
        dark: '#4a934a',
      },
      error: {
        main: '#f77066',
        light: '#ff9c91',
        dark: '#d32f2f',
      },
      warning: {
        main: '#ffb74d',
        light: '#ffc77d',
        dark: '#c68a00',
      },
      info: {
        main: '#64b5f6',
        light: '#8dcbfa',
        dark: '#4387c7',
      },
      grey: lightTheme.palette.grey,
    },
    typography: lightTheme.typography,
    shape: lightTheme.shape,
  });

  // Select the appropriate theme based on dark mode state
  const theme = darkMode ? darkTheme : lightTheme;

  // Add component customizations to the theme
  theme.components = {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          scrollbarWidth: 'thin',
          '&::-webkit-scrollbar': {
            width: '6px',
            height: '6px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)',
            borderRadius: '3px',
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: 'transparent',
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          boxShadow: 'none',
          padding: '6px 16px',
          fontWeight: 500,
          textTransform: 'none',
          '&:hover': {
            boxShadow: 'none',
          },
        },
        contained: {
          boxShadow: '0px 1px 5px rgba(0, 0, 0, 0.2)',
          '&:hover': {
            boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.25)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          boxShadow: 'none',
        },
        elevation1: {
          boxShadow: darkMode 
            ? '0px 2px 4px rgba(0, 0, 0, 0.5)' 
            : '0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24)',
        },
        elevation2: {
          boxShadow: darkMode 
            ? '0px 4px 5px rgba(0, 0, 0, 0.5)' 
            : '0px 3px 6px rgba(0, 0, 0, 0.15), 0px 2px 4px rgba(0, 0, 0, 0.12)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: darkMode 
            ? '0px 2px 4px rgba(0, 0, 0, 0.5)' 
            : '0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 4,
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          overflow: 'hidden',
          boxShadow: darkMode 
            ? '0px 2px 4px rgba(0, 0, 0, 0.5)' 
            : '0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.24)',
        },
      },
    },
    MuiSwitch: {
      styleOverrides: {
        root: {
          padding: 8,
          '& .MuiSwitch-track': {
            borderRadius: 22 / 2,
          },
          '& .MuiSwitch-thumb': {
            boxShadow: 'none',
          },
        },
      },
    },
  };
  
  // Toggle dark mode
  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };
  
  // Effect to sync dark mode with HTML class (for potential CSS styling)
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      document.documentElement.style.colorScheme = 'dark';
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.style.colorScheme = 'light';
    }
  }, [darkMode]);
  
  return (
    <ThemeContext.Provider value={{ darkMode, toggleDarkMode }}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};

export default ThemeProvider; 