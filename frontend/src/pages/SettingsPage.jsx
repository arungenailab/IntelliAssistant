import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { useTheme } from '../contexts/ThemeContext';

export default function SettingsPage() {
  // Use the theme context instead of managing dark mode locally
  const { darkMode, toggleDarkMode } = useTheme();
  
  const [settings, setSettings] = useState({
    apiKey: '',
    modelType: 'gemini-2.0-flash',
    maxTokens: 4096,
    temperature: 0.2
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setSettings(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Save settings implementation
    alert('Settings saved!');
  };

  // We no longer need the toggleDarkMode function here as it's provided by the ThemeContext

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Settings</h2>
        <p className="text-muted-foreground">
          Configure your IntelliAssistant experience
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>API Configuration</CardTitle>
            <CardDescription>
              Configure your API settings for Gemini
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <label className="text-sm font-medium" htmlFor="apiKey">
                API Key
              </label>
              <Input
                id="apiKey"
                name="apiKey"
                type="password"
                value={settings.apiKey}
                onChange={handleChange}
                placeholder="Enter your Gemini API key"
              />
              <p className="text-xs text-muted-foreground">
                Your API key is stored locally and never sent to our servers
              </p>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium" htmlFor="modelType">
                Model Type
              </label>
              <Input
                id="modelType"
                name="modelType"
                value={settings.modelType}
                onChange={handleChange}
                placeholder="e.g., gemini-2.0-flash"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-sm font-medium" htmlFor="maxTokens">
                  Max Tokens
                </label>
                <Input
                  id="maxTokens"
                  name="maxTokens"
                  type="number"
                  value={settings.maxTokens}
                  onChange={handleChange}
                />
              </div>
              <div className="space-y-1">
                <label className="text-sm font-medium" htmlFor="temperature">
                  Temperature
                </label>
                <Input
                  id="temperature"
                  name="temperature"
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.temperature}
                  onChange={handleChange}
                />
              </div>
            </div>

            <Button type="submit">Save API Settings</Button>
          </CardContent>
        </Card>
      </form>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>
            Customize the application appearance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium">Dark Mode</h3>
              <p className="text-xs text-muted-foreground">
                Toggle between light and dark mode
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={darkMode} 
                  onChange={toggleDarkMode} 
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 