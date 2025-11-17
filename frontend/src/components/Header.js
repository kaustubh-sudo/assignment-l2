import React from 'react';
import { Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import ThemeToggle from './ThemeToggle';

const Header = () => {
  return (
    <header className="border-b border-border/40 bg-background/95 backdrop-blur-sm sticky top-0 z-50">
      <div className="flex items-center justify-between h-16 px-4 md:px-5 lg:px-6 max-w-[1800px] mx-auto">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-blue-500 to-teal-500 p-2 rounded-xl">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl md:text-2xl font-bold bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-transparent">
            Diagram Maker
          </h1>
        </div>

        <ThemeToggle />
      </div>
    </header>
  );
};

export default Header;