import React from 'react';
import { List, ListItem, ListItemText, ListItemButton } from '@mui/material';

const ChatHistory = ({ conversations, activeConversation, onSelectConversation }) => {
  if (!conversations || conversations.length === 0) {
    return null;
  }

  return (
    <List sx={{ p: 0 }}>
      {conversations.map((conversation) => (
        <ListItem 
          key={conversation.id} 
          disablePadding
          sx={{ mb: 0.5 }}
        >
          <ListItemButton
            selected={activeConversation === conversation.id}
            onClick={() => onSelectConversation(conversation.id)}
            sx={{ 
              borderRadius: 1,
              bgcolor: activeConversation === conversation.id ? 'rgba(51, 102, 255, 0.08)' : 'transparent',
              '&:hover': {
                bgcolor: activeConversation === conversation.id ? 'rgba(51, 102, 255, 0.12)' : 'rgba(0, 0, 0, 0.04)'
              }
            }}
          >
            <ListItemText 
              primary={conversation.title} 
              primaryTypographyProps={{
                noWrap: true,
                sx: { 
                  fontWeight: activeConversation === conversation.id ? 600 : 400,
                  color: activeConversation === conversation.id ? 'primary.main' : 'text.primary'
                }
              }}
            />
          </ListItemButton>
        </ListItem>
      ))}
    </List>
  );
};

export default ChatHistory;
