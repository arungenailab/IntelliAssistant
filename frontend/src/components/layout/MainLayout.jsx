import React from 'react';
import Sidebar from './Sidebar';

export default function MainLayout({ children }) {
  return (
    <div className="flex h-screen bg-background/95">
      <Sidebar />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-auto px-0 py-0 md:p-4">
          {children}
        </main>
      </div>
    </div>
  );
} 