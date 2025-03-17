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
        main: '#202123',
        light: '#343541',
        dark: '#000000',
        contrastText: '#ffffff',
      },
      secondary: { 
        main: '#f5f5f5',
        light: '#ffffff',
        dark: '#e1e1e1',
        contrastText: '#202123',
      },
      background: { 
        default: '#ffffff', 
        paper: '#f7f7f8',
        chat: '#f7f7f8',
      },
      text: {
        primary: '#202123',
        secondary: '#6e6e80',
      },
      success: {
        main: '#10a37f',
        light: '#34d399',
        dark: '#047857',
      },
      error: {
        main: '#ef4444',
        light: '#f87171',
        dark: '#b91c1c',
      },
      warning: {
        main: '#f59e0b',
        light: '#fbbf24',
        dark: '#d97706',
      },
      info: {
        main: '#0ea5e9',
        light: '#38bdf8',
        dark: '#0284c7',
      },
      grey: {
        50: '#f9fafb',
        100: '#f3f4f6',
        200: '#e5e7eb',
        300: '#d1d5db',
        400: '#9ca3af',
        500: '#6b7280',
        600: '#4b5563',
        700: '#374151',
        800: '#1f2937',
        900: '#111827',
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
        main: '#f5f5f5',
        light: '#ffffff',
        dark: '#e1e1e1',
        contrastText: '#202123',
      },
      secondary: { 
        main: '#343541',
        light: '#444654',
        dark: '#202123',
        contrastText: '#f5f5f5',
      },
      background: { 
        default: '#202123', 
        paper: '#343541',
        chat: '#343541',
      },
      text: {
        primary: '#f5f5f5',
        secondary: '#acacbe',
      },
      success: {
        main: '#10a37f',
        light: '#34d399',
        dark: '#047857',
      },
      error: {
        main: '#ef4444',
        light: '#f87171',
        dark: '#b91c1c',
      },
      warning: {
        main: '#f59e0b',
        light: '#fbbf24',
        dark: '#d97706',
      },
      info: {
        main: '#0ea5e9',
        light: '#38bdf8',
        dark: '#0284c7',
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