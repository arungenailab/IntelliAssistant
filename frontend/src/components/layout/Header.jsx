import { Bell, Search } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { useTheme } from "../../contexts/ThemeContext";

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
        
        <Button 
          variant="outline" 
          size="icon" 
          onClick={toggleDarkMode}
          className="rounded-full"
        >
          {darkMode ? '☀️' : '🌙'}
        </Button>
        
        <Button variant="ghost" size="icon" className="relative rounded-full">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1.5 top-1.5 h-2.5 w-2.5 rounded-full bg-destructive animate-pulse"></span>
        </Button>
      </div>
    </header>
  );
} 