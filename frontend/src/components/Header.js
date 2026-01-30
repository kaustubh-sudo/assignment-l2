import React from 'react';
import { Sparkles, LogOut, User, FolderOpen, PenTool, Menu } from 'lucide-react';
import { Button } from './ui/button';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'sonner';

const Header = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  const isOnEditor = location.pathname === '/editor' || location.pathname.startsWith('/diagrams/');
  const isOnDiagrams = location.pathname === '/' || location.pathname === '/diagrams';

  return (
    <header className="border-b border-slate-200 bg-white/95 backdrop-blur-sm sticky top-0 z-50 shadow-sm">
      <div className="flex items-center justify-between h-14 sm:h-16 px-3 sm:px-4 md:px-6 max-w-[1800px] mx-auto">
        <div className="flex items-center gap-2 sm:gap-6">
          <div 
            className="flex items-center gap-2 sm:gap-3 cursor-pointer"
            onClick={() => navigate('/')}
          >
            <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 text-blue-500" />
            <h1 className="text-lg sm:text-xl md:text-2xl font-bold bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-transparent">
              Diagram Maker
            </h1>
          </div>
          
          {/* Desktop Navigation */}
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

        <div className="flex items-center gap-2 sm:gap-3">
          {isAuthenticated && user && (
            <div className="hidden sm:flex items-center gap-2 text-sm text-slate-500">
              <User className="w-4 h-4" />
              <span className="hidden lg:inline max-w-[150px] truncate">{user.email}</span>
            </div>
          )}
          
          {/* Mobile Menu Button */}
          {isAuthenticated && (
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              <Menu className="w-5 h-5" />
            </Button>
          )}
          
          {isAuthenticated && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="hidden sm:flex items-center gap-2 text-slate-500 hover:text-slate-700"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden lg:inline">Logout</span>
            </Button>
          )}
        </div>
      </div>
      
      {/* Mobile Menu */}
      {isAuthenticated && mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-3 py-2 space-y-1">
          <Button
            variant={isOnDiagrams ? "secondary" : "ghost"}
            size="sm"
            onClick={() => { navigate('/'); setMobileMenuOpen(false); }}
            className="w-full justify-start"
          >
            <FolderOpen className="w-4 h-4 mr-2" />
            My Diagrams
          </Button>
          <Button
            variant={isOnEditor ? "secondary" : "ghost"}
            size="sm"
            onClick={() => { navigate('/editor'); setMobileMenuOpen(false); }}
            className="w-full justify-start"
          >
            <PenTool className="w-4 h-4 mr-2" />
            Editor
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="w-full justify-start text-slate-500"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Logout
          </Button>
        </div>
      )}
    </header>
  );
};

export default Header;