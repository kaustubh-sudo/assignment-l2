import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Trash2, Edit, Calendar, ExternalLink, Folder } from 'lucide-react';
import { Button } from './ui/button';

const DIAGRAM_TYPE_LABELS = {
  graphviz: { label: 'GraphViz', emoji: '🔷', color: 'bg-blue-500/20 text-blue-400' },
  mermaid: { label: 'Mermaid', emoji: '🧜', color: 'bg-teal-500/20 text-teal-400' },
  plantuml: { label: 'PlantUML', emoji: '🌱', color: 'bg-green-500/20 text-green-400' },
  d2: { label: 'D2', emoji: '📊', color: 'bg-purple-500/20 text-purple-400' },
  blockdiag: { label: 'BlockDiag', emoji: '📦', color: 'bg-orange-500/20 text-orange-400' },
  pikchr: { label: 'Pikchr', emoji: '✏️', color: 'bg-pink-500/20 text-pink-400' },
};

const DiagramCard = ({ diagram, onDelete, folderName }) => {
  const navigate = useNavigate();
  
  const typeInfo = DIAGRAM_TYPE_LABELS[diagram.diagram_type] || {
    label: diagram.diagram_type,
    emoji: '📄',
    color: 'bg-gray-500/20 text-gray-400'
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
      className="group bg-gray-800/50 border border-gray-700 rounded-xl p-5 hover:border-blue-500/50 hover:bg-gray-800/80 transition-all duration-200 cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-white truncate group-hover:text-blue-400 transition-colors flex items-center gap-2">
            {diagram.title}
            <ExternalLink className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
          </h3>
          {diagram.description && (
            <p className="text-sm text-gray-400 mt-1 line-clamp-2">
              {diagram.description}
            </p>
          )}
        </div>
      </div>

      {/* Meta info */}
      <div className="flex items-center gap-4 mb-4">
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${typeInfo.color}`}>
          <span>{typeInfo.emoji}</span>
          {typeInfo.label}
        </span>
        <span className="flex items-center gap-1.5 text-xs text-gray-500">
          <Calendar className="w-3.5 h-3.5" />
          {formatDate(diagram.created_at)}
        </span>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-3 border-t border-gray-700/50">
        <Button
          onClick={handleEditClick}
          variant="ghost"
          size="sm"
          className="flex-1 h-9 text-gray-300 hover:text-white hover:bg-blue-500/20"
        >
          <Edit className="w-4 h-4 mr-2" />
          Edit
        </Button>
        <Button
          onClick={handleDeleteClick}
          variant="ghost"
          size="sm"
          className="h-9 px-3 text-gray-400 hover:text-red-400 hover:bg-red-500/20"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};

export default DiagramCard;
