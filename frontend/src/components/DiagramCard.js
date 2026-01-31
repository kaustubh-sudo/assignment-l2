import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Trash2, Edit, Calendar, ExternalLink, Folder } from 'lucide-react';
import { Button } from './ui/button';

const DIAGRAM_TYPE_LABELS = {
  graphviz: { label: 'GraphViz', emoji: '🔷', color: 'bg-blue-100 text-blue-600' },
  mermaid: { label: 'Mermaid', emoji: '🧜', color: 'bg-teal-100 text-teal-600' },
  plantuml: { label: 'PlantUML', emoji: '🌱', color: 'bg-green-100 text-green-600' },
  d2: { label: 'D2', emoji: '📊', color: 'bg-purple-100 text-purple-600' },
  blockdiag: { label: 'BlockDiag', emoji: '📦', color: 'bg-orange-100 text-orange-600' },
  pikchr: { label: 'Pikchr', emoji: '✏️', color: 'bg-pink-100 text-pink-600' },
};

const DiagramCard = ({ diagram, onDelete, folderName }) => {
  const navigate = useNavigate();
  
  const typeInfo = DIAGRAM_TYPE_LABELS[diagram.diagram_type] || {
    label: diagram.diagram_type,
    emoji: '📄',
    color: 'bg-slate-100 text-slate-600'
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  // Navigate to /diagrams/{id} to edit
  const handleCardClick = () => {
    navigate(`/diagrams/${diagram.id}`);
  };

  const handleEditClick = (e) => {
    e.stopPropagation(); // Prevent card click
    navigate(`/diagrams/${diagram.id}`);
  };

  const handleDeleteClick = (e) => {
    e.stopPropagation(); // Prevent card click
    onDelete(diagram);
  };

  return (
    <div 
      onClick={handleCardClick}
      className="group bg-white border border-slate-200 rounded-xl p-4 sm:p-5 hover:border-blue-300 hover:shadow-md transition-all duration-200 cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-base sm:text-lg font-semibold text-slate-800 truncate group-hover:text-blue-600 transition-colors flex items-center gap-2">
            {diagram.title}
            <ExternalLink className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-blue-500" />
          </h3>
          {diagram.description && (
            <p className="text-sm text-slate-500 mt-1 line-clamp-2">
              {diagram.description}
            </p>
          )}
        </div>
      </div>

      {/* Meta info */}
      <div className="flex items-center flex-wrap gap-2 mb-4">
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${typeInfo.color}`}>
          <span>{typeInfo.emoji}</span>
          {typeInfo.label}
        </span>
        {folderName && (
          <span 
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700"
            data-testid={`diagram-folder-badge-${diagram.id}`}
          >
            <Folder className="w-3 h-3" />
            {folderName}
          </span>
        )}
        <span className="flex items-center gap-1.5 text-xs text-slate-400">
          <Calendar className="w-3.5 h-3.5" />
          {formatDate(diagram.created_at)}
        </span>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-3 border-t border-slate-100">
        <Button
          onClick={handleEditClick}
          variant="ghost"
          size="sm"
          className="flex-1 h-9 text-slate-600 hover:text-blue-600 hover:bg-blue-50"
        >
          <Edit className="w-4 h-4 mr-2" />
          Edit
        </Button>
        <Button
          onClick={handleDeleteClick}
          variant="ghost"
          size="sm"
          className="h-9 px-3 text-slate-400 hover:text-red-500 hover:bg-red-50"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};

export default DiagramCard;
