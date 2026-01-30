import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, FolderOpen, RefreshCw, Search, X } from 'lucide-react';
import Header from '../components/Header';
import DiagramCard from '../components/DiagramCard';
import DeleteConfirmModal from '../components/DeleteConfirmModal';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

// Custom hook for debouncing
const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

const DiagramsList = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const [diagrams, setDiagrams] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearchQuery = useDebounce(searchQuery, 300);
  
  // Delete state
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Filter diagrams based on search query (case-insensitive)
  const filteredDiagrams = useMemo(() => {
    if (!debouncedSearchQuery.trim()) {
      return diagrams;
    }
    
    const query = debouncedSearchQuery.toLowerCase().trim();
    return diagrams.filter(diagram => 
      diagram.title.toLowerCase().includes(query) ||
      (diagram.description && diagram.description.toLowerCase().includes(query))
    );
  }, [diagrams, debouncedSearchQuery]);

  // Clear search
  const handleClearSearch = () => {
    setSearchQuery('');
  };

  // Fetch diagrams
  const fetchDiagrams = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/diagrams`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch diagrams');
      }

      setDiagrams(data);
    } catch (err) {
      setError(err.message);
      toast.error('Failed to load diagrams');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagrams();
  }, [token]);

  // Handle edit - navigate to editor with diagram data
  const handleEdit = (diagram) => {
    navigate('/editor', { state: { diagram } });
  };

  // Handle delete
  const handleDeleteClick = (diagram) => {
    setDeleteTarget(diagram);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;

    setIsDeleting(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/diagrams/${deleteTarget.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok && response.status !== 204) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to delete diagram');
      }

      // Remove from local state
      setDiagrams(diagrams.filter(d => d.id !== deleteTarget.id));
      toast.success('Diagram deleted successfully');
      setDeleteTarget(null);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  // Create new diagram
  const handleCreateNew = () => {
    navigate('/editor');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <Header />
      
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Header Section */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">My Diagrams</h1>
            <p className="text-gray-400">
              {isLoading ? 'Loading...' : `${diagrams.length} diagram${diagrams.length !== 1 ? 's' : ''}`}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              onClick={fetchDiagrams}
              variant="outline"
              size="sm"
              disabled={isLoading}
              className="border-gray-600 hover:bg-gray-700"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button
              onClick={handleCreateNew}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Diagram
            </Button>
          </div>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-4">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
              <p className="text-gray-400">Loading your diagrams...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <p className="text-red-400 mb-4">{error}</p>
              <Button onClick={fetchDiagrams} variant="outline">
                Try Again
              </Button>
            </div>
          </div>
        ) : diagrams.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20 px-4">
            <div className="p-6 bg-gray-800/50 rounded-full mb-6">
              <FolderOpen className="w-16 h-16 text-gray-500" />
            </div>
            <h2 className="text-2xl font-semibold text-white mb-2">No diagrams yet</h2>
            <p className="text-gray-400 text-center max-w-md mb-8">
              You haven't created any diagrams yet. Start by creating your first diagram to visualize your ideas.
            </p>
            <Button
              onClick={handleCreateNew}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Diagram
            </Button>
          </div>
        ) : (
          /* Diagrams Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {diagrams.map((diagram) => (
              <DiagramCard
                key={diagram.id}
                diagram={diagram}
                onEdit={handleEdit}
                onDelete={handleDeleteClick}
              />
            ))}
          </div>
        )}
      </main>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteConfirm}
        isLoading={isDeleting}
        diagramTitle={deleteTarget?.title || ''}
      />
    </div>
  );
};

export default DiagramsList;
