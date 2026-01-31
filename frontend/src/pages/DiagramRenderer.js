import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import Header from '../components/Header';
import InputPanel from '../components/InputPanel';
import PreviewPanel from '../components/PreviewPanel';
import SaveDiagramModal from '../components/SaveDiagramModal';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const DiagramRenderer = () => {
  const { token } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const { diagramId } = useParams(); // Get diagram ID from URL params
  
  // Check if editing existing diagram (from state or URL)
  const editingDiagramFromState = location.state?.diagram;
  
  const [userInput, setUserInput] = useState(
    "A user presses a button. The system checks if the user is logged in. If the user is logged in, it shows the dashboard. If the user is not logged in, it shows the login page."
  );
  const [diagramType, setDiagramType] = useState('graphviz');
  const [generatedCode, setGeneratedCode] = useState('');
  const [renderedDiagram, setRenderedDiagram] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRendering, setIsRendering] = useState(false);
  const [error, setError] = useState(null);
  const [showCode, setShowCode] = useState(false);
  const [isLoadingDiagram, setIsLoadingDiagram] = useState(false);
  
  // Save diagram state
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedDiagram, setSavedDiagram] = useState(null); // { id, title, description, folder_id, updated_at }
  const [isExporting, setIsExporting] = useState(false);
  
  // Folders state
  const [folders, setFolders] = useState([]);
  
  // Use ref to prevent duplicate renders
  const renderingRef = React.useRef(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Fetch folders
  useEffect(() => {
    const fetchFolders = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/folders`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setFolders(data.folders || []);
        }
      } catch (err) {
        console.error('Failed to fetch folders:', err);
      }
    };
    
    if (token) {
      fetchFolders();
    }
  }, [token, BACKEND_URL]);

  // Load diagram data when editing (from URL param or state)
  useEffect(() => {
    const diagramIdToLoad = diagramId || editingDiagramFromState?.id;
    
    if (diagramIdToLoad) {
      setIsLoadingDiagram(true);
      
      const fetchDiagram = async () => {
        try {
          const response = await fetch(`${BACKEND_URL}/api/diagrams/${diagramIdToLoad}`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          if (response.ok) {
            const data = await response.json();
            setDiagramType(data.diagram_type);
            setGeneratedCode(data.diagram_code);
            // TODO: The textarea is empty when loading a saved diagram - description not populated
            setSavedDiagram({
              id: data.id,
              title: data.title,
              description: data.description,
              folder_id: data.folder_id,
              updated_at: data.updated_at
            });
            
            // Render the diagram
            if (data.diagram_code) {
              await renderDiagramWithKroki(data.diagram_code, data.diagram_type);
            }
            
            toast.info(`Editing: ${data.title}`);
          } else if (response.status === 404) {
            toast.error('Diagram not found');
            navigate('/');
          } else if (response.status === 403) {
            toast.error('You do not have access to this diagram');
            navigate('/');
          }
        } catch (err) {
          toast.error('Failed to load diagram');
          navigate('/');
        } finally {
          setIsLoadingDiagram(false);
        }
      };
      
      fetchDiagram();
    }
  }, [diagramId, editingDiagramFromState?.id, token]);

  // Kroki type is now directly the diagram type selected by user
  const getKrokiType = (type) => {
    return type;
  };

  // Generate diagram code from natural language using backend
  const generateDiagramCode = async (description, type) => {
    const response = await fetch('/api/generate-diagram', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        description: description,
        diagram_type: type,
      }),
    });

    // Store status BEFORE reading body
    const { status, ok } = response;
    
    // Read response body only once
    const data = await response.json();
    
    // Check status AFTER reading body
    if (!ok) {
      throw new Error(data.detail || `Backend error: ${status}`);
    }

    return data.code;
  };

  // Render the diagram using Kroki API  
  const renderDiagram = async (code, krokiType) => {
    const krokiUrl = `https://kroki.io/${krokiType}/svg`;
    
    const response = await fetch(krokiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/plain',
      },
      body: code,
    });

    // Store status before reading body
    const { status, ok } = response;
    
    // Read body only once
    const svgText = await response.text();
    
    // Check status after reading
    if (!ok) {
      console.error('Kroki error response:', svgText);
      throw new Error(`Kroki API returned ${status}. Check diagram syntax.`);
    }

    return { type: 'svg', content: svgText };
  };

  // Helper to render existing diagram code
  const renderDiagramWithKroki = async (code, type) => {
    setIsRendering(true);
    try {
      const krokiType = getKrokiType(type);
      const diagram = await renderDiagram(code, krokiType);
      setRenderedDiagram(diagram);
    } catch (err) {
      console.error('Render error:', err);
      setError(err.message);
    } finally {
      setIsRendering(false);
    }
  };

  // Main function to generate and render diagram
  const handleGenerateDiagram = async () => {
    if (!userInput.trim()) {
      toast.error('Please describe what you want to visualize');
      return;
    }

    // Prevent duplicate calls
    if (renderingRef.current) {
      console.log('Already rendering, skipping duplicate call');
      return;
    }

    renderingRef.current = true;
    setIsGenerating(true);
    setError(null);

    try {
      // Step 1: Generate diagram code from natural language
      toast.info('Understanding your description...');
      const code = await generateDiagramCode(userInput, diagramType);
      setGeneratedCode(code);
      
      // Step 2: Render the diagram
      setIsRendering(true);
      toast.info('Creating your diagram...');
      const krokiType = getKrokiType(diagramType);
      const diagram = await renderDiagram(code, krokiType);
      
      if (diagram) {
        setRenderedDiagram(diagram);
        toast.success('Your diagram is ready!');
      }
    } catch (err) {
      setError(err.message);
      toast.error(err.message);
    } finally {
      setIsGenerating(false);
      setIsRendering(false);
      renderingRef.current = false;
    }
  };

  // Generate filename from diagram title or default
  const getExportFilename = (format) => {
    // TODO: Downloaded files all named "diagram.png" - should use actual diagram title
    return `diagram.${format}`;
  };

  // Export diagram as SVG or PNG
  const handleExport = async (format) => {
    if (!renderedDiagram) {
      toast.error('Please generate a diagram first');
      return;
    }

    if (!generatedCode) {
      toast.error('No diagram code available to export');
      return;
    }

    // Prevent multiple clicks
    if (isExporting) {
      return;
    }

    setIsExporting(true);

    try {
      const filename = getExportFilename(format);
      
      if (format === 'svg') {
        // Export as SVG
        const blob = new Blob([renderedDiagram.content], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success(`Exported as ${filename}`);
      } else if (format === 'png') {
        // Render as PNG using Kroki
        const krokiType = getKrokiType(diagramType);
        const krokiUrl = `https://kroki.io/${krokiType}/png`;
        
        console.log('Exporting PNG:', { krokiType, codeLength: generatedCode.length });
        
        const response = await fetch(krokiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'text/plain',
          },
          body: generatedCode,
        });

        // Store status BEFORE reading body
        const { status, ok } = response;
        
        // Read body as blob
        const blob = await response.blob();
        
        // Check status AFTER reading body
        if (!ok) {
          console.error('Kroki PNG error:', status);
          throw new Error(`Failed to export as PNG: ${status}`);
        }

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success(`Exported as ${filename}`);
      }
    } catch (err) {
      toast.error(`Failed to export diagram: ${err.message}`);
      console.error('Export error:', err);
    }
    // FIXME: Export button shows spinner forever after export fails
  };

  const clearAll = () => {
    setUserInput('');
    setGeneratedCode('');
    setRenderedDiagram(null);
    setError(null);
    setSavedDiagram(null); // Clear saved diagram state
    toast.info('Cleared');
  };

  // Save or update diagram
  const handleSaveDiagram = async ({ title, description, folder_id }) => {
    if (!generatedCode) {
      toast.error('Please generate a diagram first');
      return;
    }

    setIsSaving(true);
    
    try {
      const diagramData = {
        title,
        description,
        diagram_type: diagramType,
        diagram_code: generatedCode,
        folder_id: folder_id
      };

      let response;
      
      if (savedDiagram?.id) {
        // Update existing diagram
        response = await fetch(`${BACKEND_URL}/api/diagrams/${savedDiagram.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(diagramData)
        });
      } else {
        // Create new diagram
        response = await fetch(`${BACKEND_URL}/api/diagrams`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(diagramData)
        });
      }

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to save diagram');
      }

      setSavedDiagram({
        id: data.id,
        title: data.title,
        description: data.description,
        folder_id: data.folder_id,
        updated_at: savedDiagram?.updated_at  // FIXME: "Last saved" time never changes after re-saving
      });

      setShowSaveModal(false);
      toast.success(savedDiagram?.id ? 'Diagram updated!' : 'Diagram saved!');
    } catch (err) {
      toast.error(err.message);
    }
    // FIXME: Save button stays disabled forever after first save - state not cleaned up
  };

  // Format last saved time
  const formatLastSaved = (isoString) => {
    if (!isoString) return null;
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  // Show loading state while fetching diagram
  if (isLoadingDiagram) {
    return (
      <div className="flex flex-col h-screen bg-gradient-to-br from-background via-background to-muted/30">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            <p className="text-slate-500">Loading diagram...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Header />
      
      {/* Editing Banner */}
      {savedDiagram && (
        <div className="bg-blue-50 border-b border-blue-200 px-3 sm:px-4 py-2">
          <div className="max-w-[1800px] mx-auto flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-blue-600 font-medium text-sm sm:text-base">Editing:</span>
              <span className="text-slate-800 truncate text-sm sm:text-base">{savedDiagram.title}</span>
            </div>
            <button
              onClick={() => navigate('/')}
              className="text-sm text-slate-500 hover:text-blue-600 transition-colors whitespace-nowrap ml-2"
            >
              ← Back
            </button>
          </div>
        </div>
      )}
      
      <div className="flex-1 flex flex-col lg:flex-row gap-3 sm:gap-4 lg:gap-6 p-3 sm:p-4 lg:p-6 max-w-[1800px] w-full mx-auto overflow-hidden">
        {/* Left Side - Input */}
        <div className="flex-none lg:flex-1 lg:min-h-0 lg:max-w-[50%]">
          <InputPanel
            userInput={userInput}
            setUserInput={setUserInput}
            diagramType={diagramType}
            setDiagramType={setDiagramType}
            generatedCode={generatedCode}
            showCode={showCode}
            setShowCode={setShowCode}
            onGenerate={handleGenerateDiagram}
            onClear={clearAll}
            isGenerating={isGenerating}
            isRendering={isRendering}
            // Save props
            onSave={() => setShowSaveModal(true)}
            canSave={!!generatedCode}
            savedDiagram={savedDiagram}
            lastSavedAt={formatLastSaved(savedDiagram?.updated_at)}
          />
        </div>

        {/* Right Side - Preview */}
        <div className="flex-1 min-h-0 lg:max-w-[50%]">
          <PreviewPanel
            renderedDiagram={renderedDiagram}
            isLoading={isGenerating || isRendering}
            error={error}
            onExport={handleExport}
            isExporting={isExporting}
          />
        </div>
      </div>

      {/* Save Diagram Modal */}
      <SaveDiagramModal
        isOpen={showSaveModal}
        onClose={() => setShowSaveModal(false)}
        onSave={handleSaveDiagram}
        isLoading={isSaving}
        existingTitle={savedDiagram?.title || ''}
        existingDescription={savedDiagram?.description || ''}
        existingFolderId={savedDiagram?.folder_id || null}
        folders={folders}
      />
    </div>
  );
};

export default DiagramRenderer;