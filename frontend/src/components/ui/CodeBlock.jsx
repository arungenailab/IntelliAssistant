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

/**
 * Modern code block with enhanced syntax highlighting
 */
const CodeBlock = ({ language = 'javascript', code = '', showLineNumbers = true }) => {
  const codeRef = useRef(null);
  const theme = useTheme();
  const [copied, setCopied] = useState(false);
  const isDarkMode = theme.palette.mode === 'dark';
  
  // Normalize language name
  const normalizedLanguage = language.toLowerCase().replace(/^\s*\{?\.?(\w+).*\}?$/, '$1');
  
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
  };
  
  const prismLanguage = languageMap[normalizedLanguage] || 'javascript';
  
  useEffect(() => {
    if (codeRef.current) {
      Prism.highlightElement(codeRef.current);
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
        borderRadius: theme.shape.borderRadius,
        background: isDarkMode ? 'rgba(30, 30, 30, 0.95)' : 'rgba(245, 245, 245, 0.95)',
        border: `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)'}`,
        mb: 2,
        overflow: 'hidden',
        boxShadow: isDarkMode 
          ? '0 4px 8px rgba(0, 0, 0, 0.4)' 
          : '0 2px 4px rgba(0, 0, 0, 0.05)',
        transition: 'box-shadow 0.3s ease, transform 0.3s ease',
        '&:hover': {
          boxShadow: isDarkMode 
            ? '0 5px 10px rgba(0, 0, 0, 0.5)' 
            : '0 4px 8px rgba(0, 0, 0, 0.1)',
          transform: 'translateY(-1px)',
        }
      }}
    >
      {/* Language label and copy button */}
      <Box
        sx={{
          position: 'absolute',
          top: '8px',
          right: '8px',
          zIndex: 10,
          display: 'flex',
          gap: '4px',
        }}
      >
        <Box
          sx={{
            fontSize: '0.7rem',
            textTransform: 'uppercase',
            fontWeight: 500,
            color: isDarkMode ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)',
            letterSpacing: '0.05em',
            padding: '3px 8px',
            borderRadius: '4px',
            background: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)',
            backdropFilter: 'blur(10px)',
          }}
        >
          {normalizedLanguage}
        </Box>
        
        <Tooltip title={copied ? "Copied!" : "Copy code"}>
          <IconButton
            size="small"
            onClick={handleCopyCode}
            sx={{
              padding: '3px',
              color: isDarkMode ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)',
              background: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)',
              backdropFilter: 'blur(10px)',
              '&:hover': {
                backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.1)',
                color: theme.palette.primary.main,
              },
            }}
          >
            {copied ? <CheckIcon sx={{ fontSize: '0.9rem' }} /> : <ContentCopyIcon sx={{ fontSize: '0.9rem' }} />}
          </IconButton>
        </Tooltip>
      </Box>
      
      <Box
        sx={{
          pt: 3.5,
          pb: 2.5,
          px: 2,
          overflow: 'auto',
          maxHeight: '400px',
          
          // Styling for line numbers
          ...(showLineNumbers && {
            counterReset: 'line',
            '& .token-line': {
              position: 'relative',
              paddingLeft: '3.5em',
              '&::before': {
                content: 'counter(line)',
                counterIncrement: 'line',
                position: 'absolute',
                left: 0,
                textAlign: 'right',
                width: '2.5em',
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
      
      {/* Copy notification */}
      <Snackbar 
        open={copied} 
        autoHideDuration={2000} 
        onClose={() => setCopied(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="success" variant="filled" sx={{ width: '100%' }}>
          Code copied to clipboard
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CodeBlock; 