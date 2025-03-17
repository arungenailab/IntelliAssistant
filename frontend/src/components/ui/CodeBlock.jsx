import React, { useEffect, useRef, useState } from 'react';
import { Box, IconButton, Tooltip, useTheme, Snackbar, Alert } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import Prism from 'prismjs';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-jsx';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-tsx';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-scss';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-markdown';
import 'prismjs/components/prism-yaml';
import 'prismjs/components/prism-rust';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-csharp';
import 'prismjs/components/prism-go';
import 'prismjs/components/prism-php';
import 'prismjs/components/prism-ruby';
import 'prismjs/components/prism-r';
import './prism-material-theme.css';

// Register plain text language for fallback
Prism.languages.text = Prism.languages.plain = {
  'text': /[\s\S]+/
};

/**
 * Modern code block with enhanced syntax highlighting
 */
const CodeBlock = ({ language = 'javascript', code = '', showLineNumbers = true }) => {
  const codeRef = useRef(null);
  const theme = useTheme();
  const [copied, setCopied] = useState(false);
  const isDarkMode = theme.palette.mode === 'dark';
  
  // Normalize language name
  const normalizedLanguage = language ? language.toLowerCase().replace(/^\s*\{?\.?(\w+).*\}?$/, '$1') : 'text';
  
  // Map language to Prism language
  const languageMap = {
    js: 'javascript',
    jsx: 'jsx',
    ts: 'typescript',
    tsx: 'tsx',
    css: 'css',
    scss: 'scss',
    py: 'python',
    python: 'python',
    json: 'json',
    sql: 'sql',
    bash: 'bash',
    sh: 'bash',
    shell: 'bash',
    md: 'markdown',
    yaml: 'yaml',
    yml: 'yaml',
    rust: 'rust',
    java: 'java',
    c: 'c',
    cpp: 'cpp',
    cs: 'csharp',
    go: 'go',
    php: 'php',
    rb: 'ruby',
    ruby: 'ruby',
    r: 'r',
    text: 'text',
    '': 'text',
    plain: 'text'
  };
  
  // Get the Prism language with a fallback to plain text
  const prismLanguage = (languageMap[normalizedLanguage] && Prism.languages[languageMap[normalizedLanguage]]) 
    ? languageMap[normalizedLanguage] 
    : 'text';
  
  useEffect(() => {
    if (codeRef.current) {
      try {
        Prism.highlightElement(codeRef.current);
      } catch (error) {
        console.error("Error highlighting code:", error);
      }
    }
  }, [code, prismLanguage]);
  
  const handleCopyCode = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  
  return (
    <Box
      sx={{
        position: 'relative',
        fontFamily: '"Roboto Mono", monospace',
        fontSize: '0.85rem',
        borderRadius: '6px',
        background: isDarkMode ? 'rgba(34, 34, 34, 0.95)' : 'rgba(247, 247, 248, 0.95)',
        border: `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'}`,
        mb: 2,
        overflow: 'hidden',
        boxShadow: 'none',
        transition: 'border-color 0.2s ease',
        '&:hover': {
          borderColor: isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)',
        }
      }}
    >
      {/* Language label and copy button */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '8px 12px',
          borderBottom: `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'}`,
          background: isDarkMode ? 'rgba(0, 0, 0, 0.2)' : 'rgba(0, 0, 0, 0.03)',
        }}
      >
        <Box
          sx={{
            fontSize: '0.75rem',
            fontWeight: 500,
            color: isDarkMode ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)',
            letterSpacing: '0.02em',
          }}
        >
          {normalizedLanguage}
        </Box>
        
        <Tooltip title={copied ? "Copied!" : "Copy code"}>
          <IconButton
            size="small"
            onClick={handleCopyCode}
            sx={{
              padding: '4px',
              color: isDarkMode ? 'rgba(255, 255, 255, 0.5)' : 'rgba(0, 0, 0, 0.5)',
              '&:hover': {
                backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)',
                color: '#10a37f',
              },
            }}
          >
            {copied ? <CheckIcon sx={{ fontSize: '1rem' }} /> : <ContentCopyIcon sx={{ fontSize: '1rem' }} />}
          </IconButton>
        </Tooltip>
      </Box>
      
      <Box
        sx={{
          pt: 2,
          pb: 2,
          px: 3,
          overflow: 'auto',
          maxHeight: '500px',
          
          // Styling for line numbers
          ...(showLineNumbers && {
            counterReset: 'line',
            '& .token-line': {
              position: 'relative',
              paddingLeft: '3em',
              '&::before': {
                content: 'counter(line)',
                counterIncrement: 'line',
                position: 'absolute',
                left: 0,
                textAlign: 'right',
                width: '2em',
                paddingRight: '1em',
                color: isDarkMode ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 0, 0, 0.3)',
                fontSize: '0.8em',
                userSelect: 'none',
              }
            }
          })
        }}
      >
        <pre className={`language-${prismLanguage} token-line`} style={{ margin: 0 }}>
          <code ref={codeRef} className={`language-${prismLanguage}`}>
            {code}
          </code>
        </pre>
      </Box>
      
      {/* Remove Snackbar for a cleaner notification system */}
      <Snackbar 
        open={copied} 
        autoHideDuration={2000} 
        onClose={() => setCopied(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          severity="success" 
          variant="filled" 
          sx={{ 
            bgcolor: '#10a37f',
            color: 'white',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
          }}
        >
          Code copied to clipboard
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CodeBlock; 