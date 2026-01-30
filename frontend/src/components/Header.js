import React from 'react';
import { Sparkles, LogOut, User, FolderOpen, PenTool } from 'lucide-react';
import { Button } from './ui/button';
import ThemeToggle from './ThemeToggle';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'sonner';

const Header = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  const isOnEditor = location.pathname === '/editor';
  const isOnDiagrams = location.pathname === '/' || location.pathname === '/diagrams';

  return (
    <header className="border-b border-border/40 bg-background/95 backdrop-blur-sm sticky top-0 z-50">
      <div className="flex items-center justify-between h-16 px-4 md:px-5 lg:px-6 max-w-[1800px] mx-auto">
        <div className="flex items-center gap-6">
          <div 
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => navigate('/')}
          >
            <Sparkles className="w-6 h-6 text-blue-500" />
            <h1 className="text-xl md:text-2xl font-bold bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-transparent">
              Diagram Maker
            </h1>
          </div>
          
          {/* Navigation */}
          {isAuthenticated && (
            <nav className="hidden md:flex items-center gap-1">
              <Button
                variant={isOnDiagrams ? "secondary" : "ghost"}
                size="sm"
                onClick={() => navigate('/')}
                className="flex items-center gap-2"
              >
                <FolderOpen className="w-4 h-4" />
                My Diagrams
              </Button>
              <Button
                variant={isOnEditor ? "secondary" : "ghost"}
                size="sm"
                onClick={() => navigate('/editor')}
                className="flex items-center gap-2"
              >
                <PenTool className="w-4 h-4" />
                Editor
              </Button>
            </nav>
          )}
        </div>

        <div className="flex items-center gap-3">
          {isAuthenticated && user && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <User className="w-4 h-4" />
              <span className="hidden sm:inline">{user.email}</span>
            </div>
          )}
          <ThemeToggle />
          {isAuthenticated && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;