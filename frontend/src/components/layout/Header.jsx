import { Bell, Search } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";

export default function Header({ title }) {
  return (
    <header className="border-b border-border bg-card px-4 py-3 flex items-center justify-between">
      <h1 className="text-xl font-semibold">{title || 'IntelliAssistant'}</h1>
      
      <div className="flex items-center gap-3">
        <div className="relative w-64">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            type="search" 
            placeholder="Search..." 
            className="pl-8 w-full"
          />
        </div>
        
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-destructive"></span>
        </Button>
      </div>
    </header>
  );
} 