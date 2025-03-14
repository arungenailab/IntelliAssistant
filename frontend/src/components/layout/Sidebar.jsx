import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { 
  BarChart3, 
  Home, 
  MessageSquare, 
  Settings, 
  Upload, 
  ChevronLeft, 
  ChevronRight,
  Database,
  Globe
} from 'lucide-react';
import { Button } from '../ui/button';

export default function Sidebar() {
  const [expanded, setExpanded] = useState(true);

  const navigation = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Chat', href: '/chat', icon: MessageSquare },
    { name: 'Data Analysis', href: '/data', icon: BarChart3 },
    { name: 'Datasets', href: '/datasets', icon: Database },
    { name: 'Upload', href: '/upload', icon: Upload },
    { name: 'External APIs', href: '/api-data', icon: Globe },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div 
      className={cn(
        "h-full flex flex-col border-r border-border bg-card transition-all duration-300",
        expanded ? "w-64" : "w-16"
      )}
    >
      <div className="p-4 flex justify-between items-center">
        {expanded && (
          <h1 className="text-xl font-semibold text-primary truncate">
            IntelliAssistant
          </h1>
        )}
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => setExpanded(!expanded)}
          className="rounded-full"
        >
          {expanded ? (
            <ChevronLeft className="h-5 w-5" />
          ) : (
            <ChevronRight className="h-5 w-5" />
          )}
        </Button>
      </div>

      <div className="flex-1 overflow-auto py-2">
        <nav className="space-y-1 px-2">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  "flex items-center px-2 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  !expanded && "justify-center"
                )
              }
            >
              <item.icon className={cn("h-5 w-5 flex-shrink-0", expanded && "mr-3")} />
              {expanded && <span>{item.name}</span>}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground">
            <span className="text-sm font-medium">U</span>
          </div>
          {expanded && (
            <div className="truncate">
              <p className="text-sm font-medium">User</p>
              <p className="text-xs text-muted-foreground">user@example.com</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 