import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, FolderOpen, RefreshCw, Search, X, FolderPlus, Folder, Trash2 } from 'lucide-react';
import Header from '../components/Header';
import DiagramCard from '../components/DiagramCard';
import DeleteConfirmModal from '../components/DeleteConfirmModal';
import CreateFolderModal from '../components/CreateFolderModal';
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
  
  // Folder state
  const [folders, setFolders] = useState([]);
  const [selectedFolderId, setSelectedFolderId] = useState(null); // null = All, 'none' = No Folder
  const [showCreateFolderModal, setShowCreateFolderModal] = useState(false);
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [deleteFolderTarget, setDeleteFolderTarget] = useState(null);
  const [isDeletingFolder, setIsDeletingFolder] = useState(false);
  
  // Delete state
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Create folder map for quick lookup
  const folderMap = useMemo(() => {
    return folders.reduce((acc, folder) => {
      acc[folder.id] = folder.name;
      return acc;
    }, {});
  }, [folders]);

  // Filter diagrams based on search query and selected folder
  const filteredDiagrams = useMemo(() => {
    let result = diagrams;
    
    // Filter by folder
    if (selectedFolderId === 'none') {
      result = result.filter(d => !d.folder_id);
    } else if (selectedFolderId) {
      result = result.filter(d => d.folder_id === selectedFolderId);
    }
    
    // Filter by search query
    if (debouncedSearchQuery.trim()) {
      const query = debouncedSearchQuery.toLowerCase().trim();
      result = result.filter(diagram => 
        diagram.title.toLowerCase().includes(query) ||
        (diagram.description && diagram.description.toLowerCase().includes(query))
      );
    }
    
    return result;
  }, [diagrams, debouncedSearchQuery, selectedFolderId]);

  // Clear search
  const handleClearSearch = () => {
    setSearchQuery('');
  };

  // Fetch folders
  const fetchFolders = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/folders`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setFolders(data.folders || []);
      }
    } catch (err) {
      console.error('Failed to fetch folders:', err);
    }
  };

  // Create folder
  const handleCreateFolder = async (name) => {
    setIsCreatingFolder(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/folders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create folder');
      }
      
      setFolders([...folders, data].sort((a, b) => a.name.localeCompare(b.name)));
      setShowCreateFolderModal(false);
      toast.success(`Folder "${name}" created`);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsCreatingFolder(false);
    }
  };

  // Delete folder
  const handleDeleteFolder = async () => {
    if (!deleteFolderTarget) return;
    
    setIsDeletingFolder(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/folders/${deleteFolderTarget.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok && response.status !== 204) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to delete folder');
      }
      
      // Update local state
      setFolders(folders.filter(f => f.id !== deleteFolderTarget.id));
      
      // Clear folder_id from diagrams in this folder
      setDiagrams(diagrams.map(d => 
        d.folder_id === deleteFolderTarget.id ? { ...d, folder_id: null } : d
      ));
      
      // Reset selection if this folder was selected
      if (selectedFolderId === deleteFolderTarget.id) {
        setSelectedFolderId(null);
      }
      
      toast.success(`Folder "${deleteFolderTarget.name}" deleted`);
      setDeleteFolderTarget(null);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsDeletingFolder(false);
    }
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
    fetchFolders();
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
      
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Header Section */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">My Diagrams</h1>
            <p className="text-gray-400">
              {isLoading ? 'Loading...' : `${diagrams.length} diagram${diagrams.length !== 1 ? 's' : ''}`}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              onClick={() => setShowCreateFolderModal(true)}
              variant="outline"
              size="sm"
              className="border-gray-600 hover:bg-gray-700"
              data-testid="new-folder-btn"
            >
              <FolderPlus className="w-4 h-4 mr-2" />
              New Folder
            </Button>
            <Button
              onClick={() => { fetchDiagrams(); fetchFolders(); }}
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
              data-testid="new-diagram-btn"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Diagram
            </Button>
          </div>
        </div>

        <div className="flex gap-6">
          {/* Folder Sidebar */}
          <div className="w-56 flex-shrink-0">
            <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-3">Folders</h3>
              <div className="space-y-1">
                {/* All Diagrams */}
                <button
                  onClick={() => setSelectedFolderId(null)}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-colors ${
                    selectedFolderId === null 
                      ? 'bg-blue-500/20 text-blue-400' 
                      : 'text-gray-300 hover:bg-gray-700/50'
                  }`}
                  data-testid="folder-filter-all"
                >
                  <FolderOpen className="w-4 h-4" />
                  <span className="flex-1">All Diagrams</span>
                  <span className="text-xs text-gray-500">{diagrams.length}</span>
                </button>
                
                {/* No Folder */}
                <button
                  onClick={() => setSelectedFolderId('none')}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-colors ${
                    selectedFolderId === 'none' 
                      ? 'bg-blue-500/20 text-blue-400' 
                      : 'text-gray-300 hover:bg-gray-700/50'
                  }`}
                  data-testid="folder-filter-none"
                >
                  <FolderOpen className="w-4 h-4" />
                  <span className="flex-1">No Folder</span>
                  <span className="text-xs text-gray-500">
                    {diagrams.filter(d => !d.folder_id).length}
                  </span>
                </button>
                
                {/* Folder List */}
                {folders.map((folder) => (
                  <div key={folder.id} className="group flex items-center">
                    <button
                      onClick={() => setSelectedFolderId(folder.id)}
                      className={`flex-1 flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-colors ${
                        selectedFolderId === folder.id 
                          ? 'bg-blue-500/20 text-blue-400' 
                          : 'text-gray-300 hover:bg-gray-700/50'
                      }`}
                      data-testid={`folder-filter-${folder.id}`}
                    >
                      <Folder className="w-4 h-4" />
                      <span className="flex-1 truncate">{folder.name}</span>
                      <span className="text-xs text-gray-500">
                        {diagrams.filter(d => d.folder_id === folder.id).length}
                      </span>
                    </button>
                    <button
                      onClick={() => setDeleteFolderTarget(folder)}
                      className="p-1 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                      title="Delete folder"
                      data-testid={`folder-delete-${folder.id}`}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
                
                {/* Add Folder Button */}
                <button
                  onClick={() => setShowCreateFolderModal(true)}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700/50 transition-colors"
                  data-testid="add-folder-sidebar-btn"
                >
                  <FolderPlus className="w-4 h-4" />
                  <span>Add Folder</span>
                </button>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {/* Search Section */}
            {diagrams.length > 0 && (
              <div className="mb-6">
                <div className="relative max-w-md">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    type="text"
                    placeholder="Search diagrams by title or description..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-10 bg-gray-800/50 border-gray-700 text-white placeholder-gray-500 focus:border-blue-500 focus:ring-blue-500"
                    data-testid="search-input"
                  />
                  {searchQuery && (
                    <button
                      onClick={handleClearSearch}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                      data-testid="search-clear-button"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
                {(debouncedSearchQuery || selectedFolderId) && (
                  <p className="text-sm text-gray-400 mt-2">
                    {filteredDiagrams.length === 0 
                      ? 'No diagrams found' 
                      : `Showing ${filteredDiagrams.length} diagram${filteredDiagrams.length !== 1 ? 's' : ''}`
                    }
                    {selectedFolderId && selectedFolderId !== 'none' && folderMap[selectedFolderId] && (
                      <span> in <span className="text-amber-400">{folderMap[selectedFolderId]}</span></span>
                    )}
                    {selectedFolderId === 'none' && (
                      <span> with <span className="text-amber-400">no folder</span></span>
                    )}
                  </p>
                )}
              </div>
            )}

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
              /* Empty State - No diagrams at all */
              <div className="flex flex-col items-center justify-center py-20 px-4">
                <div className="p-6 bg-gray-800/50 rounded-full mb-6">
                  <FolderOpen className="w-16 h-16 text-gray-500" />
                </div>
                <h2 className="text-2xl font-semibold text-white mb-2">No diagrams yet</h2>
                <p className="text-gray-400 text-center max-w-md mb-8">
                  You have not created any diagrams yet. Start by creating your first diagram to visualize your ideas.
                </p>
                <Button
                  onClick={handleCreateNew}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Your First Diagram
                </Button>
              </div>
            ) : filteredDiagrams.length === 0 ? (
              /* No Search/Filter Results */
              <div className="flex flex-col items-center justify-center py-20 px-4" data-testid="no-results-state">
                <div className="p-6 bg-gray-800/50 rounded-full mb-6">
                  <Search className="w-16 h-16 text-gray-500" />
                </div>
                <h2 className="text-2xl font-semibold text-white mb-2">No results found</h2>
                <p className="text-gray-400 text-center max-w-md mb-6">
                  {debouncedSearchQuery ? (
                    <>No diagrams match &quot;<span className="text-white font-medium">{debouncedSearchQuery}</span>&quot;</>
                  ) : (
                    <>No diagrams in this folder</>
                  )}
                </p>
                <div className="flex gap-3">
                  {debouncedSearchQuery && (
                    <Button
                      onClick={handleClearSearch}
                      variant="outline"
                      className="border-gray-600 hover:bg-gray-700"
                    >
                      <X className="w-4 h-4 mr-2" />
                      Clear Search
                    </Button>
                  )}
                  {selectedFolderId && (
                    <Button
                      onClick={() => setSelectedFolderId(null)}
                      variant="outline"
                      className="border-gray-600 hover:bg-gray-700"
                    >
                      View All
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              /* Diagrams Grid */
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5" data-testid="diagrams-grid">
                {filteredDiagrams.map((diagram) => (
                  <DiagramCard
                    key={diagram.id}
                    diagram={diagram}
                    onEdit={handleEdit}
                    onDelete={handleDeleteClick}
                    folderName={diagram.folder_id ? folderMap[diagram.folder_id] : null}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteConfirm}
        isLoading={isDeleting}
        diagramTitle={deleteTarget?.title || ''}
      />

      {/* Create Folder Modal */}
      <CreateFolderModal
        isOpen={showCreateFolderModal}
        onClose={() => setShowCreateFolderModal(false)}
        onCreate={handleCreateFolder}
        isLoading={isCreatingFolder}
      />

      {/* Delete Folder Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={!!deleteFolderTarget}
        onClose={() => setDeleteFolderTarget(null)}
        onConfirm={handleDeleteFolder}
        isLoading={isDeletingFolder}
        diagramTitle={deleteFolderTarget?.name || ''}
        customTitle="Delete Folder"
        customMessage={`Are you sure you want to delete the folder "${deleteFolderTarget?.name}"? Diagrams in this folder will be moved to "No Folder".`}
      />
    </div>
  );
};

export default DiagramsList;
