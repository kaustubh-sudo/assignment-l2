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

  // Generate diagram code from natural language using AI
  const generateDiagramCode = async (description, type) => {
    const prompts = {
      flowchart: `Convert this description into GraphViz DOT code for a flowchart. Use these styling rules:
- Set bgcolor="transparent"
- Use rounded rectangles for process steps: shape=box, style="rounded,filled", fillcolor="#e0f2fe", color="#0284c7", fontcolor="#0c4a6e"
- Use diamonds for decisions: shape=diamond, style=filled, fillcolor="#fef3c7", color="#f59e0b", fontcolor="#78350f"
- Use ovals for start/end: shape=oval, style=filled, fillcolor="#dcfce7", color="#16a34a", fontcolor="#14532d"
- Use simple edge colors: color="#64748b"
- Keep labels clear and concise
- Use rankdir=TB for top-to-bottom flow

Description: ${description}

Return ONLY the GraphViz DOT code, no explanations or markdown.`,
      
      sequence: `Convert this description into Mermaid sequence diagram code. Use clear actor names and messages.

Description: ${description}

Return ONLY the Mermaid code starting with 'sequenceDiagram', no explanations or markdown.`,
      
      mindmap: `Convert this description into a Mermaid mindmap. Use clear hierarchical structure.

Description: ${description}

Return ONLY the Mermaid code starting with 'mindmap', no explanations or markdown.`,
      
      process: `Convert this description into a GraphViz DOT code for a process diagram. Use these styling rules:
- Set bgcolor="transparent"
- Use boxes for steps: shape=box, style=filled, fillcolor="#ddd6fe", color="#7c3aed", fontcolor="#4c1d95"
- Use arrows for flow: color="#64748b"
- Use rankdir=LR for left-to-right flow

Description: ${description}

Return ONLY the GraphViz DOT code, no explanations or markdown.`,
      
      organization: `Convert this description into GraphViz DOT code for an organization chart. Use these styling rules:
- Set bgcolor="transparent"
- Use rounded boxes: shape=box, style="rounded,filled", fillcolor="#fce7f3", color="#db2777", fontcolor="#831843"
- Use rankdir=TB for top-to-bottom hierarchy

Description: ${description}

Return ONLY the GraphViz DOT code, no explanations or markdown.`,
    };

    const apiKey = process.env.REACT_APP_OPENAI_API_KEY;
    
    try {
      const response = await fetch('https://llm.emergent.sh/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model: 'gpt-4o-mini',
          messages: [
            {
              role: 'system',
              content: 'You are a diagram code generator. Generate clean, valid diagram code based on user descriptions. Return ONLY the code without any markdown formatting or explanations.'
            },
            {
              role: 'user',
              content: prompts[type] || prompts.flowchart
            }
          ],
          temperature: 0.7,
          max_tokens: 1000,
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      let code = data.choices[0].message.content.trim();
      
      // Clean up the code - remove markdown code blocks if present
      code = code.replace(/```[a-z]*\n?/g, '').replace(/```$/g, '').trim();
      
      return code;
    } catch (error) {
      console.error('Error generating diagram code:', error);
      throw new Error('Failed to generate diagram code. Please try again.');
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