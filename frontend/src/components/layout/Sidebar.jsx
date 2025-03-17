import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { 
  BarChart3, 
  MessageSquare, 
  Settings, 
  Upload, 
  PanelLeft,
  Database,
  Globe,
  Moon,
  Sun
} from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

export default function Sidebar() {
  const { darkMode, toggleDarkMode } = useTheme();
  
  // Initialize collapsed by default
  const [expanded, setExpanded] = useState(() => {
    const saved = localStorage.getItem('sidebarExpanded');
    // Always return false for initial state (collapsed)
    return false;
  });

  // Save expanded state to localStorage
  useEffect(() => {
    localStorage.setItem('sidebarExpanded', JSON.stringify(expanded));
  }, [expanded]);

  const navigation = [
    { name: 'Chat', href: '/', icon: MessageSquare },
    { name: 'Data Analysis', href: '/data', icon: BarChart3 },
    { name: 'Datasets', href: '/datasets', icon: Database },
    { name: 'Upload', href: '/upload', icon: Upload },
    { name: 'External APIs', href: '/api-data', icon: Globe },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div 
      className={cn(
        "h-full flex flex-col bg-background/80 transition-all duration-300 relative",
        expanded ? "w-52" : "w-16"
      )}
    >
      <div className="flex items-center justify-center h-16 relative group">
        {expanded ? (
          <h1 className="text-xl font-medium text-foreground truncate">
            IntelliAssistant
          </h1>
        ) : (
          <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
            <span className="text-secondary-foreground font-medium">IA</span>
            <span className="absolute left-full ml-2 p-2 rounded-md shadow-md text-xs font-medium bg-gray-900 text-gray-100 dark:bg-gray-800 dark:text-gray-100 invisible group-hover:visible z-[100] whitespace-nowrap">
              IntelliAssistant
            </span>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-visible py-2">
        <nav className="space-y-1 px-2">
          {/* Main navigation links */}
          {navigation.map((item) => (
            <div key={item.name} className="relative group">
              <NavLink
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    "flex items-center px-2 py-2 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "bg-secondary text-foreground"
                      : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground",
                    !expanded && "justify-center"
                  )
                }
              >
                <item.icon className={cn("h-5 w-5 flex-shrink-0", expanded && "mr-3")} />
                {expanded && <span>{item.name}</span>}
              </NavLink>
              {!expanded && (
                <span className="absolute left-full ml-2 p-2 rounded-md shadow-md text-xs font-medium bg-gray-900 text-gray-100 dark:bg-gray-800 dark:text-gray-100 invisible group-hover:visible z-[100] whitespace-nowrap">
                  {item.name}
                </span>
              )}
            </div>
          ))}
          
          {/* Theme toggle button - styled like a nav item */}
          <div className="relative group">
            <button
              onClick={toggleDarkMode}
              className={cn(
                "w-full flex items-center px-2 py-2 rounded-md text-sm font-medium transition-colors",
                "text-muted-foreground hover:bg-secondary/50 hover:text-foreground",
                !expanded && "justify-center"
              )}
              aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
            >
              {darkMode ? (
                <>
                  <Sun className={cn("h-5 w-5 flex-shrink-0", expanded && "mr-3")} />
                  {expanded && <span>Light Mode</span>}
                </>
              ) : (
                <>
                  <Moon className={cn("h-5 w-5 flex-shrink-0", expanded && "mr-3")} />
                  {expanded && <span>Dark Mode</span>}
                </>
              )}
            </button>
            {!expanded && (
              <span className="absolute left-full ml-2 p-2 rounded-md shadow-md text-xs font-medium bg-gray-900 text-gray-100 dark:bg-gray-800 dark:text-gray-100 invisible group-hover:visible z-[100] whitespace-nowrap">
                {darkMode ? "Light Mode" : "Dark Mode"}
              </span>
            )}
          </div>
          
          {/* Sidebar collapse toggle - styled like a nav item */}
          <div className="relative group">
            <button 
              onClick={() => setExpanded(!expanded)}
              className={cn(
                "w-full flex items-center px-2 py-2 rounded-md text-sm font-medium transition-colors",
                "text-muted-foreground hover:bg-secondary/50 hover:text-foreground",
                !expanded && "justify-center"
              )}
            >
              <PanelLeft className={cn(
                "h-5 w-5 flex-shrink-0 transition-transform",
                !expanded && "rotate-180",
                expanded && "mr-3"
              )} />
              {expanded && <span>Collapse</span>}
            </button>
            {!expanded && (
              <span className="absolute left-full ml-2 p-2 rounded-md shadow-md text-xs font-medium bg-gray-900 text-gray-100 dark:bg-gray-800 dark:text-gray-100 invisible group-hover:visible z-[100] whitespace-nowrap">
                Expand
              </span>
            )}
          </div>
        </nav>
      </div>
    </div>
  );
}