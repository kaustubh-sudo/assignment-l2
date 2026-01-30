import React, { useState } from 'react';
import Header from '../components/Header';
import InputPanel from '../components/InputPanel';
import PreviewPanel from '../components/PreviewPanel';
import SaveDiagramModal from '../components/SaveDiagramModal';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

const DiagramRenderer = () => {
  const { token } = useAuth();
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
  
  // Save diagram state
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedDiagram, setSavedDiagram] = useState(null); // { id, title, description, updated_at }
  
  // Use ref to prevent duplicate renders
  const renderingRef = React.useRef(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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

    try {
      if (format === 'svg') {
        // Export as SVG
        const blob = new Blob([renderedDiagram.content], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${diagramType}-diagram-${Date.now()}.svg`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success('Diagram exported as SVG!');
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
        a.download = `${diagramType}-diagram-${Date.now()}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success('Diagram exported as PNG!');
      }
    } catch (err) {
      toast.error(`Failed to export diagram: ${err.message}`);
      console.error('Export error:', err);
    }
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
  const handleSaveDiagram = async ({ title, description }) => {
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
        diagram_code: generatedCode
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
        updated_at: data.updated_at
      });

      setShowSaveModal(false);
      toast.success(savedDiagram?.id ? 'Diagram updated!' : 'Diagram saved!');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  // Format last saved time
  const formatLastSaved = (isoString) => {
    if (!isoString) return null;
    const date = new Date(isoString);
    return date.toLocaleString();
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-background via-background to-muted/30">
      <Header />
      
      <div className="flex-1 flex flex-col lg:flex-row gap-4 md:gap-5 lg:gap-6 p-4 md:p-5 lg:p-6 max-w-[1800px] w-full mx-auto overflow-hidden">
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
      />
    </div>
  );
};

export default DiagramRenderer;