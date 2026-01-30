import React, { useState, useEffect } from 'react';
import { X, Save, Folder } from 'lucide-react';
import { Button } from './ui/button';

const SaveDiagramModal = ({ 
  isOpen, 
  onClose, 
  onSave, 
  isLoading, 
  existingTitle = '', 
  existingDescription = '',
  existingFolderId = null,
  folders = []
}) => {
  const [title, setTitle] = useState(existingTitle);
  const [description, setDescription] = useState(existingDescription);
  const [folderId, setFolderId] = useState(existingFolderId);
  const [error, setError] = useState('');

  // Update state when existing values change
  useEffect(() => {
    setTitle(existingTitle);
    setDescription(existingDescription);
    setFolderId(existingFolderId);
  }, [existingTitle, existingDescription, existingFolderId]);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!title.trim()) {
      setError('Title is required');
      return;
    }
    
    if (title.length > 200) {
      setError('Title must be less than 200 characters');
      return;
    }
    
    setError('');
    onSave({ 
      title: title.trim(), 
      description: description.trim(),
      folder_id: folderId || null
    });
  };

  const handleClose = () => {
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div className="relative bg-white border border-slate-200 rounded-xl shadow-xl w-full max-w-md p-6 animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
            <Save className="w-5 h-5 text-blue-500" />
            {existingTitle ? 'Update Diagram' : 'Save Diagram'}
          </h2>
          <button
            onClick={handleClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="diagram-title" className="block text-sm font-medium text-slate-600 mb-2">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              id="diagram-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter diagram title"
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              disabled={isLoading}
              autoFocus
              data-testid="diagram-title-input"
            />
            {error && (
              <p className="mt-1 text-sm text-red-500">{error}</p>
            )}
          </div>
          
          <div>
            <label htmlFor="diagram-description" className="block text-sm font-medium text-slate-600 mb-2">
              Description <span className="text-slate-400">(optional)</span>
            </label>
            <textarea
              id="diagram-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Enter a brief description"
              rows={3}
              maxLength={1000}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
              disabled={isLoading}
              data-testid="diagram-description-input"
            />
            <p className="mt-1 text-xs text-slate-400 text-right">
              {description.length}/1000
            </p>
          </div>
          
          {/* Folder Selection */}
          <div>
            <label htmlFor="diagram-folder" className="block text-sm font-medium text-slate-600 mb-2">
              <Folder className="w-4 h-4 inline mr-1" />
              Folder <span className="text-slate-400">(optional)</span>
            </label>
            <select
              id="diagram-folder"
              value={folderId || ''}
              onChange={(e) => setFolderId(e.target.value || null)}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              disabled={isLoading}
              data-testid="diagram-folder-select"
            >
              <option value="">No Folder</option>
              {folders.map((folder) => (
                <option key={folder.id} value={folder.id}>
                  {folder.name}
                </option>
              ))}
            </select>
          </div>
          
          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isLoading}
              className="flex-1 border-slate-200"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isLoading || !title.trim()}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
              data-testid="save-diagram-submit"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  {existingTitle ? 'Update' : 'Save'}
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SaveDiagramModal;
