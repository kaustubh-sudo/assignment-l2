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
  }, [token]); // eslint-disable-line

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
      setDiagrams(prevDiagrams => prevDiagrams.filter(d => d.id !== deleteTarget.id));
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Header />
      
      <main className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 py-4 sm:py-6 md:py-8">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-800 mb-1">My Diagrams</h1>
            <p className="text-slate-500 text-sm sm:text-base">
              {isLoading ? 'Loading...' : `${diagrams.length} diagram${diagrams.length !== 1 ? 's' : ''}`}
            </p>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
            <Button
              onClick={() => setShowCreateFolderModal(true)}
              variant="outline"
              size="sm"
              className="border-slate-300 hover:bg-slate-100 text-slate-600"
              data-testid="new-folder-btn"
            >
              <FolderPlus className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">New Folder</span>
            </Button>
            <Button
              onClick={() => { fetchDiagrams(); fetchFolders(); }}
              variant="outline"
              size="sm"
              disabled={isLoading}
              className="border-slate-300 hover:bg-slate-100 text-slate-600"
            >
              <RefreshCw className={`w-4 h-4 sm:mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
            <Button
              onClick={handleCreateNew}
              className="bg-blue-600 hover:bg-blue-700"
              data-testid="new-diagram-btn"
            >
              <Plus className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">New Diagram</span>
            </Button>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-4 lg:gap-6">
          {/* Folder Sidebar - Collapsible on mobile */}
          <div className="w-full lg:w-56 flex-shrink-0">
            <div className="bg-white border border-slate-200 rounded-xl p-3 sm:p-4 shadow-sm">
              <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-3">Folders</h3>
              <div className="flex lg:flex-col gap-1 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
                {/* All Diagrams */}
                <button
                  onClick={() => setSelectedFolderId(null)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-colors whitespace-nowrap ${
                    selectedFolderId === null 
                      ? 'bg-blue-50 text-blue-600 border border-blue-200' 
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                  data-testid="folder-filter-all"
                >
                  <FolderOpen className="w-4 h-4 flex-shrink-0" />
                  <span className="flex-1">All Diagrams</span>
                  <span className="text-xs text-slate-400">{diagrams.length}</span>
                </button>
                
                {/* No Folder */}
                <button
                  onClick={() => setSelectedFolderId('none')}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-colors whitespace-nowrap ${
                    selectedFolderId === 'none' 
                      ? 'bg-blue-50 text-blue-600 border border-blue-200' 
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                  data-testid="folder-filter-none"
                >
                  <FolderOpen className="w-4 h-4 flex-shrink-0" />
                  <span className="flex-1">No Folder</span>
                  <span className="text-xs text-slate-400">
                    {diagrams.filter(d => !d.folder_id).length}
                  </span>
                </button>
                
                {/* Folder List */}
                {folders.map((folder) => (
                  <div key={folder.id} className="group flex items-center">
                    <button
                      onClick={() => setSelectedFolderId(folder.id)}
                      className={`flex-1 flex items-center gap-2 px-3 py-2 rounded-lg text-left transition-colors whitespace-nowrap ${
                        selectedFolderId === folder.id 
                          ? 'bg-blue-50 text-blue-600 border border-blue-200' 
                          : 'text-slate-600 hover:bg-slate-50'
                      }`}
                      data-testid={`folder-filter-${folder.id}`}
                    >
                      <Folder className="w-4 h-4 flex-shrink-0" />
                      <span className="flex-1 truncate">{folder.name}</span>
                      <span className="text-xs text-slate-400">
                        {diagrams.filter(d => d.folder_id === folder.id).length}
                      </span>
                    </button>
                    <button
                      onClick={() => setDeleteFolderTarget(folder)}
                      className="p-1 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all hidden lg:block"
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
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-colors whitespace-nowrap"
                  data-testid="add-folder-sidebar-btn"
                >
                  <FolderPlus className="w-4 h-4 flex-shrink-0" />
                  <span>Add Folder</span>
                </button>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {/* Search Section */}
            {diagrams.length > 0 && (
              <div className="mb-4 sm:mb-6">
                <div className="relative max-w-md">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    type="text"
                    placeholder="Search diagrams..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-10 bg-white border-slate-200 text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:ring-blue-500"
                    data-testid="search-input"
                  />
                  {searchQuery && (
                    <button
                      onClick={handleClearSearch}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                      data-testid="search-clear-button"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
                {(debouncedSearchQuery || selectedFolderId) && (
                  <p className="text-sm text-slate-500 mt-2">
                    {filteredDiagrams.length === 0 
                      ? 'No diagrams found' 
                      : `Showing ${filteredDiagrams.length} diagram${filteredDiagrams.length !== 1 ? 's' : ''}`
                    }
                    {selectedFolderId && selectedFolderId !== 'none' && folderMap[selectedFolderId] && (
                      <span> in <span className="text-blue-600 font-medium">{folderMap[selectedFolderId]}</span></span>
                    )}
                    {selectedFolderId === 'none' && (
                      <span> with <span className="text-blue-600 font-medium">no folder</span></span>
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
                  <p className="text-slate-500">Loading your diagrams...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center py-20">
                <div className="text-center">
                  <p className="text-red-500 mb-4">{error}</p>
                  <Button onClick={fetchDiagrams} variant="outline">
                    Try Again
                  </Button>
                </div>
              </div>
            ) : diagrams.length === 0 ? (
              /* Empty State - No diagrams at all */
              <div className="flex flex-col items-center justify-center py-16 sm:py-20 px-4">
                <div className="p-6 bg-slate-100 rounded-full mb-6">
                  <FolderOpen className="w-12 h-12 sm:w-16 sm:h-16 text-slate-400" />
                </div>
                <h2 className="text-xl sm:text-2xl font-semibold text-slate-800 mb-2">No diagrams yet</h2>
                <p className="text-slate-500 text-center max-w-md mb-8 text-sm sm:text-base">
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
              <div className="flex flex-col items-center justify-center py-16 sm:py-20 px-4" data-testid="no-results-state">
                <div className="p-6 bg-slate-100 rounded-full mb-6">
                  <Search className="w-12 h-12 sm:w-16 sm:h-16 text-slate-400" />
                </div>
                <h2 className="text-xl sm:text-2xl font-semibold text-slate-800 mb-2">No results found</h2>
                <p className="text-slate-500 text-center max-w-md mb-6 text-sm sm:text-base">
                  {debouncedSearchQuery ? (
                    <>No diagrams match &quot;<span className="text-slate-700 font-medium">{debouncedSearchQuery}</span>&quot;</>
                  ) : (
                    <>No diagrams in this folder</>
                  )}
                </p>
                <div className="flex gap-3 flex-wrap justify-center">
                  {debouncedSearchQuery && (
                    <Button
                      onClick={handleClearSearch}
                      variant="outline"
                      className="border-slate-300 hover:bg-slate-100"
                    >
                      <X className="w-4 h-4 mr-2" />
                      Clear Search
                    </Button>
                  )}
                  {selectedFolderId && (
                    <Button
                      onClick={() => setSelectedFolderId(null)}
                      variant="outline"
                      className="border-slate-300 hover:bg-slate-100"
                    >
                      View All
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              /* Diagrams Grid */
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-5" data-testid="diagrams-grid">
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
