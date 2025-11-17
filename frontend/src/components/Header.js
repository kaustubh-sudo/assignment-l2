import React from 'react';
import { Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import ThemeToggle from './ThemeToggle';

const Header = () => {
  return (
    <header className="border-b border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
      <div className="container mx-auto px-4 md:px-6 py-2.5 md:py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="relative flex items-center">
              <div className="bg-gradient-to-br from-primary to-accent p-1.5 rounded-md">
                <Sparkles className="w-4 h-4 md:w-5 md:h-5 text-primary-foreground" />
              </div>
            </div>
            <div>
              <h1 className="text-base md:text-lg font-semibold tracking-tight">
                Diagram Maker
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;