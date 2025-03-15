import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Box, IconButton, Tooltip, useTheme } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

/**
 * A syntax highlighting component for code blocks
 * @param {string} code - The code to highlight
 * @param {string} language - The programming language of the code
 * @param {boolean} showLineNumbers - Whether to show line numbers
 * @param {boolean} wrapLongLines - Whether to wrap long lines
 * @returns {JSX.Element}
 */
const CodeBlock = ({ 
  code, 
  language = 'sql', 
  showLineNumbers = false,
  wrapLongLines = true
}) => {
  const theme = useTheme();
  const isDarkMode = theme.palette.mode === 'dark';
  
  const handleCopy = () => {
    navigator.clipboard.writeText(code)
      .then(() => {
        console.log('Code copied to clipboard');
      })
      .catch(err => {
        console.error('Failed to copy: ', err);
      });
  };

  return (
    <Box sx={{ position: 'relative', my: 1.5, borderRadius: '6px', overflow: 'hidden' }}>
      <SyntaxHighlighter
        language={language}
        style={isDarkMode ? vscDarkPlus : oneLight}
        showLineNumbers={showLineNumbers}
        wrapLongLines={wrapLongLines}
        customStyle={{
          borderRadius: '6px',
          fontSize: '0.9rem',
          margin: 0,
          padding: '1rem',
          maxHeight: '400px',
          overflow: 'auto'
        }}
      >
        {code}
      </SyntaxHighlighter>
      <Tooltip title="Copy to clipboard">
        <IconButton
          onClick={handleCopy}
          size="small"
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            color: isDarkMode ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)',
            bgcolor: isDarkMode ? 'rgba(30, 30, 30, 0.5)' : 'rgba(255, 255, 255, 0.5)',
            backdropFilter: 'blur(2px)',
            '&:hover': {
              bgcolor: isDarkMode ? 'rgba(50, 50, 50, 0.7)' : 'rgba(240, 240, 240, 0.7)',
            }
          }}
        >
          <ContentCopyIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Box>
  );
};

export default CodeBlock; 