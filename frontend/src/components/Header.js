import React from 'react';
import { Code2, Zap } from 'lucide-react';
import { Button } from './ui/button';
import ThemeToggle from './ThemeToggle';

const Header = () => {
  return (
    <header className="border-b border-border bg-card/80 backdrop-blur-md sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-accent/20 blur-xl rounded-full" />
              <div className="relative bg-gradient-to-br from-primary to-secondary p-2.5 rounded-lg">
                <Code2 className="w-6 h-6 text-primary-foreground" />
              </div>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                Kroki <span className="gradient-text">Renderer</span>
              </h1>
              <p className="text-xs text-muted-foreground">Diagram-as-Code Visualization</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              className="hidden sm:flex items-center gap-2 text-muted-foreground hover:text-foreground"
              onClick={() => window.open('https://kroki.io', '_blank')}
            >
              <Zap className="w-4 h-4" />
              <span>Powered by Kroki</span>
            </Button>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;