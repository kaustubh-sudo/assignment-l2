import React, { useState } from 'react';
import Header from '../components/Header';
import InputPanel from '../components/InputPanel';
import PreviewPanel from '../components/PreviewPanel';
import { toast } from 'sonner';

const DiagramRenderer = () => {
  const [userInput, setUserInput] = useState(
    "Create a simple workflow showing: Start → Review Document → Approve or Reject → If approved go to Complete, if rejected go back to Review → End"
  );
  const [diagramType, setDiagramType] = useState('flowchart');
  const [generatedCode, setGeneratedCode] = useState('');
  const [renderedDiagram, setRenderedDiagram] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRendering, setIsRendering] = useState(false);
  const [error, setError] = useState(null);
  const [showCode, setShowCode] = useState(false);

  // Convert user-friendly diagram type to Kroki type
  const getKrokiType = (type) => {
    const mapping = {
      'flowchart': 'graphviz',
      'sequence': 'mermaid',
      'mindmap': 'mermaid',
      'process': 'graphviz',
      'organization': 'graphviz',
    };
    return mapping[type] || 'graphviz';
  };

  // Generate diagram code from natural language using backend AI
  const generateDiagramCode = async (description, type) => {
    // Use local backend URL to avoid CORS issues
    const BACKEND_URL = window.location.hostname === 'localhost' ? 'http://localhost:8001' : process.env.REACT_APP_BACKEND_URL;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/generate-diagram`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: description,
          diagram_type: type,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to generate diagram code: ${response.status}`);
      }

      const data = await response.json();
      return data.code;
    } catch (error) {
      console.error('Error generating diagram code:', error);
      throw new Error(error.message || 'Failed to generate diagram code. Please try again.');
    }
  };

  // Render the diagram using Kroki API
  const renderDiagram = async (code, krokiType) => {
    try {
      const krokiUrl = `https://kroki.io/${krokiType}/svg`;
      const response = await fetch(krokiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'text/plain',
        },
        body: code,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || `Failed to render diagram`);
      }

      const svgText = await response.text();
      return { type: 'svg', content: svgText };
    } catch (error) {
      console.error('Error rendering diagram:', error);
      throw error;
    }
  };

  // Main function to generate and render diagram
  const handleGenerateDiagram = async () => {
    if (!userInput.trim()) {
      toast.error('Please describe what you want to visualize');
      return;
    }

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
      setRenderedDiagram(diagram);
      
      toast.success('Your diagram is ready!');
    } catch (err) {
      setError(err.message);
      toast.error(err.message);
    } finally {
      setIsGenerating(false);
      setIsRendering(false);
    }
  };

  // Export diagram as SVG or PNG
  const handleExport = async (format) => {
    if (!renderedDiagram) {
      toast.error('Please generate a diagram first');
      return;
    }

    try {
      if (format === 'svg') {
        // Export as SVG
        const blob = new Blob([renderedDiagram.content], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `diagram-${Date.now()}.svg`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success('Diagram exported as SVG!');
      } else if (format === 'png') {
        // Render as PNG using Kroki
        const krokiType = getKrokiType(diagramType);
        const krokiUrl = `https://kroki.io/${krokiType}/png`;
        const response = await fetch(krokiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'text/plain',
          },
          body: generatedCode,
        });

        if (!response.ok) {
          throw new Error('Failed to export as PNG');
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `diagram-${Date.now()}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success('Diagram exported as PNG!');
      }
    } catch (err) {
      toast.error('Failed to export diagram');
      console.error('Export error:', err);
    }
  };

  const clearAll = () => {
    setUserInput('');
    setGeneratedCode('');
    setRenderedDiagram(null);
    setError(null);
    toast.info('Cleared');
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-background to-muted">
      <Header />
      
      <div className="flex-1 flex flex-col lg:flex-row gap-4 p-4 overflow-hidden">
        {/* Left Side - Input */}
        <div className="flex-1 min-h-0">
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
          />
        </div>

        {/* Right Side - Preview */}
        <div className="flex-1 min-h-0">
          <PreviewPanel
            renderedDiagram={renderedDiagram}
            isLoading={isGenerating || isRendering}
            error={error}
            onExport={handleExport}
          />
        </div>
      </div>
    </div>
  );
};

export default DiagramRenderer;