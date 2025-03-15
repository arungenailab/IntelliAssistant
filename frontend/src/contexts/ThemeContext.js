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
    'Inter',
    'Segoe UI',
    'Roboto', 
    'Helvetica',
    'Arial',
    'sans-serif',
  ].join(',');

  // Create the MUI theme based on dark mode state
  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        // Modern blue from sequel.sh
        main: '#3366FF',
        light: '#6C8EFF',
        dark: '#2952CC',
        contrastText: '#ffffff',
      },
      secondary: {
        // Updated secondary colors
        main: darkMode ? '#8468F5' : '#7B61FF',
        light: darkMode ? '#A68BFF' : '#9F8AFF',
        dark: darkMode ? '#6A4FD9' : '#5E48CC',
        contrastText: '#ffffff',
      },
      background: {
        default: darkMode ? '#0F0F1A' : '#F8FAFC',
        paper: darkMode ? '#1A1A2E' : '#FFFFFF',
      },
      text: {
        primary: darkMode ? '#E2E8F0' : '#1E293B',
        secondary: darkMode ? '#94A3B8' : '#64748B',
      },
      success: {
        main: '#10B981',
        light: '#34D399',
        dark: '#059669',
      },
      error: {
        main: '#EF4444',
        light: '#F87171',
        dark: '#DC2626',
      },
      warning: {
        main: '#F59E0B',
        light: '#FBBF24',
        dark: '#D97706',
      },
      info: {
        main: '#3B82F6',
        light: '#60A5FA',
        dark: '#2563EB',
      },
      grey: {
        50: '#F8FAFC',
        100: '#F1F5F9',
        200: '#E2E8F0',
        300: '#CBD5E1',
        400: '#94A3B8',
        500: '#64748B',
        600: '#475569',
        700: '#334155',
        800: '#1E293B',
        900: '#0F172A',
      },
    },
    typography: {
      fontFamily,
      h1: {
        fontWeight: 700,
        fontSize: '2.5rem',
        lineHeight: 1.2,
        letterSpacing: '-0.02em',
      },
      h2: {
        fontWeight: 700,
        fontSize: '2rem',
        lineHeight: 1.2,
        letterSpacing: '-0.01em',
      },
      h3: {
        fontWeight: 600,
        fontSize: '1.5rem',
        lineHeight: 1.3,
        letterSpacing: '-0.01em',
      },
      h4: {
        fontWeight: 600,
        fontSize: '1.25rem',
        lineHeight: 1.4,
        letterSpacing: '-0.01em',
      },
      h5: {
        fontWeight: 600,
        fontSize: '1.125rem',
        lineHeight: 1.4,
      },
      h6: {
        fontWeight: 600,
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
        lineHeight: 1.57,
      },
      body1: {
        fontSize: '1rem',
        lineHeight: 1.5,
      },
      body2: {
        fontSize: '0.875rem',
        lineHeight: 1.57,
      },
      button: {
        fontWeight: 600,
        fontSize: '0.875rem',
        textTransform: 'none',
        letterSpacing: '0.02em',
      },
      caption: {
        fontSize: '0.75rem',
        lineHeight: 1.66,
      },
      overline: {
        fontWeight: 600,
        fontSize: '0.75rem',
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
      },
    },
    shape: {
      borderRadius: 8,
    },
    shadows: [
      'none',
      '0px 2px 4px rgba(0, 0, 0, 0.05)',
      '0px 4px 6px rgba(0, 0, 0, 0.07)',
      '0px 6px 12px rgba(0, 0, 0, 0.08)',
      '0px 8px 16px rgba(0, 0, 0, 0.09)',
      '0px 12px 24px rgba(0, 0, 0, 0.11)',
      // ... keep the rest of the shadows as default
    ],
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            scrollbarWidth: 'thin',
            '&::-webkit-scrollbar': {
              width: '6px',
              height: '6px',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.2)',
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
            borderRadius: 8,
            boxShadow: 'none',
            padding: '8px 16px',
            fontWeight: 600,
            '&:hover': {
              boxShadow: 'none',
              transform: 'translateY(-1px)',
              transition: 'transform 0.2s ease-in-out',
            },
          },
          contained: {
            '&:hover': {
              boxShadow: 'none',
            },
          },
          containedPrimary: {
            background: 'linear-gradient(90deg, #3366FF 0%, #5E48CC 100%)',
            '&:hover': {
              background: 'linear-gradient(90deg, #2952CC 0%, #4C39A8 100%)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            boxShadow: 'none',
            border: `1px solid ${darkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)'}`,
          },
          elevation1: {
            boxShadow: darkMode 
              ? '0px 4px 8px rgba(0, 0, 0, 0.5)' 
              : '0px 2px 4px rgba(0, 0, 0, 0.05), 0px 4px 6px rgba(0, 0, 0, 0.03)',
            border: `1px solid ${darkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.03)'}`,
          },
          elevation3: {
            boxShadow: darkMode 
              ? '0px 8px 16px rgba(0, 0, 0, 0.6)' 
              : '0px 4px 8px rgba(0, 0, 0, 0.06), 0px 8px 16px rgba(0, 0, 0, 0.04)',
            border: `1px solid ${darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)'}`,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            overflow: 'hidden', 
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              transform: 'translateY(-3px)',
              boxShadow: darkMode 
                ? '0px 8px 20px rgba(0, 0, 0, 0.6)' 
                : '0px 8px 20px rgba(0, 0, 0, 0.08)',
            },
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 8,
              transition: 'border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
              '&.Mui-focused': {
                boxShadow: `0 0 0 3px ${darkMode ? 'rgba(99, 102, 241, 0.2)' : 'rgba(99, 102, 241, 0.15)'}`,
              },
            },
          },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            transition: 'background-color 0.2s ease-in-out, transform 0.2s ease-in-out',
            '&:hover': {
              backgroundColor: darkMode ? 'rgba(255, 255, 255, 0.08)' : 'rgba(51, 102, 255, 0.08)',
              transform: 'translateY(-1px)',
            },
          },
        },
      },
      MuiInputBase: {
        styleOverrides: {
          root: {
            fontSize: '0.9375rem',
          },
        },
      },
      MuiMenuItem: {
        styleOverrides: {
          root: {
            fontSize: '0.9375rem',
            minHeight: 42,
          },
        },
      },
      MuiListItemButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            '&.Mui-selected': {
              backgroundColor: darkMode ? 'rgba(99, 102, 241, 0.16)' : 'rgba(99, 102, 241, 0.08)',
              '&:hover': {
                backgroundColor: darkMode ? 'rgba(99, 102, 241, 0.24)' : 'rgba(99, 102, 241, 0.16)',
              },
            },
          },
        },
      },
    },
  });

  // Listen for changes to the 'dark' class on the document element
  useEffect(() => {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          setDarkMode(document.documentElement.classList.contains('dark'));
        }
      });
    });

    observer.observe(document.documentElement, { attributes: true });

    return () => {
      observer.disconnect();
    };
  }, []);

  // Toggle dark mode function
  const toggleDarkMode = () => {
    const newDarkMode = !darkMode;
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
    setDarkMode(newDarkMode);
  };

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