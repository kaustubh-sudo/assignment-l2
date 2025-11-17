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

  // Generate diagram code from natural language
  const generateDiagramCode = async (description, type) => {
    // For demo purposes, we'll use a smart template-based approach
    // Extract key information from the description
    
    await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate processing time
    
    const lowerDesc = description.toLowerCase();
    
    if (type === 'flowchart' || type === 'process') {
      // Parse for workflow steps
      const code = `digraph G {
  bgcolor="transparent"
  rankdir=${type === 'process' ? 'LR' : 'TB'}
  node [fontname="Arial", fontsize=12]
  edge [fontname="Arial", fontsize=10]
  
  start [label="Start", shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"]
  
  ${lowerDesc.includes('review') ? `review [label="Review Document", shape=box, style="rounded,filled", fillcolor="#e0f2fe", color="#0284c7", fontcolor="#0c4a6e"]` : ''}
  
  ${lowerDesc.includes('approve') || lowerDesc.includes('decision') || lowerDesc.includes('reject') ? `decision [label="Approve?", shape=diamond, style=filled, fillcolor="#fef3c7", color="#f59e0b", fontcolor="#78350f"]` : ''}
  
  ${lowerDesc.includes('complete') ? `complete [label="Complete", shape=box, style="rounded,filled", fillcolor="#e0f2fe", color="#0284c7", fontcolor="#0c4a6e"]` : ''}
  
  end [label="End", shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"]
  
  start -> ${lowerDesc.includes('review') ? 'review' : 'decision'}
  ${lowerDesc.includes('review') ? 'review -> decision' : ''}
  ${lowerDesc.includes('approve') ? `decision -> complete [label="Approved", color="#64748b"]
  decision -> ${lowerDesc.includes('review') ? 'review' : 'start'} [label="Rejected", color="#64748b"]
  complete -> end` : 'decision -> end'}
}`;
      return code;
    }
    
    if (type === 'sequence') {
      return `sequenceDiagram
    participant User
    participant System
    participant Database
    
    User->>System: Send Request
    System->>Database: Query Data
    Database-->>System: Return Results
    System-->>User: Display Response`;
    }
    
    if (type === 'mindmap') {
      return `graph TD
    A[Main Topic] --> B[Subtopic 1]
    A --> C[Subtopic 2]
    A --> D[Subtopic 3]
    B --> E[Detail 1]
    B --> F[Detail 2]
    C --> G[Detail 3]
    D --> H[Detail 4]`;
    }
    
    if (type === 'organization') {
      return `digraph G {
  bgcolor="transparent"
  rankdir=TB
  node [fontname="Arial", fontsize=12, shape=box, style="rounded,filled", fillcolor="#fce7f3", color="#db2777", fontcolor="#831843"]
  
  CEO [label="CEO"]
  CTO [label="CTO"]
  CFO [label="CFO"]
  Dev1 [label="Developer 1"]
  Dev2 [label="Developer 2"]
  Acc1 [label="Accountant"]
  
  CEO -> CTO
  CEO -> CFO
  CTO -> Dev1
  CTO -> Dev2
  CFO -> Acc1
}`;
    }
    
    // Default flowchart
    return `digraph G {
  bgcolor="transparent"
  rankdir=TB
  node [fontname="Arial", fontsize=12]
  
  start [label="Start", shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"]
  process [label="Process", shape=box, style="rounded,filled", fillcolor="#e0f2fe", color="#0284c7", fontcolor="#0c4a6e"]
  end [label="End", shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"]
  
  start -> process [color="#64748b"]
  process -> end [color="#64748b"]
}`;
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