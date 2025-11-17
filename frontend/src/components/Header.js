import React from 'react';
import { Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import ThemeToggle from './ThemeToggle';

const Header = () => {
  return (
    <header className="border-b border-border/40 bg-background sticky top-0 z-50">
      <div className="container mx-auto px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-gradient-to-b from-blue-500 to-teal-500 w-1 h-6 rounded-full" />
            <div className="bg-gradient-to-br from-blue-500 to-teal-500 p-1 rounded">
              <Sparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <h1 className="text-sm font-medium">
              Diagram Maker
            </h1>
          </div>

          <ThemeToggle />
        </div>
      </div>
    </header>
  );
};

export default Header;