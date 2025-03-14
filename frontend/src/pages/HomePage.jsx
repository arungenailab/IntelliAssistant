import React from 'react';
import { Link } from 'react-router-dom';
import { 
  BarChart3, 
  MessageSquare, 
  Upload,
  ArrowRight 
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../components/ui/card';

export default function HomePage() {
  const stats = [
    { title: 'Datasets', value: '12', description: 'Active datasets' },
    { title: 'Analyses', value: '87', description: 'Completed analyses' },
    { title: 'Conversations', value: '24', description: 'Total conversations' },
  ];

  const actions = [
    { 
      title: 'Start a conversation', 
      description: 'Chat with your data using natural language', 
      icon: MessageSquare, 
      href: '/chat',
      color: 'bg-blue-100 text-blue-700'
    },
    { 
      title: 'Analyze data', 
      description: 'Get insights and visualizations from your datasets', 
      icon: BarChart3, 
      href: '/data',
      color: 'bg-purple-100 text-purple-700'
    },
    { 
      title: 'Upload new data', 
      description: 'Import CSV, Excel or JSON files to analyze', 
      icon: Upload, 
      href: '/upload',
      color: 'bg-emerald-100 text-emerald-700'
    }
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Welcome to IntelliAssistant</h1>
        <p className="text-muted-foreground mt-2">Your AI-powered data analysis companion</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {stats.map((stat, index) => (
          <Card key={index}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground mt-1">{stat.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <h2 className="text-xl font-semibold mt-6">Quick Actions</h2>
      
      <div className="grid gap-4 md:grid-cols-3">
        {actions.map((action, index) => (
          <Card key={index} className="overflow-hidden">
            <CardHeader className="pb-2">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${action.color} mb-2`}>
                <action.icon className="h-4 w-4" />
              </div>
              <CardTitle>{action.title}</CardTitle>
              <CardDescription>{action.description}</CardDescription>
            </CardHeader>
            <CardFooter className="pt-2">
              <Button asChild variant="ghost" className="p-0 h-auto font-normal text-primary">
                <Link to={action.href} className="flex items-center">
                  Get started <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      <div className="mt-6">
        <Card className="bg-primary/5 border-primary/10">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold">Ready to analyze your data?</h3>
                <p className="text-muted-foreground mt-1">
                  Start a conversation or upload new datasets to gain valuable insights.
                </p>
              </div>
              <Button asChild>
                <Link to="/chat">Start analyzing</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 