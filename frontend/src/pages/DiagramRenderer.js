import React, { useState } from 'react';
import Header from '../components/Header';
import EditorPanel from '../components/EditorPanel';
import PreviewPanel from '../components/PreviewPanel';
import OptionsPanel from '../components/OptionsPanel';
import { toast } from 'sonner';

const DiagramRenderer = () => {
  const [diagramSource, setDiagramSource] = useState(
    `digraph G {
  bgcolor="transparent"
  node [style=filled, fillcolor="#22d3ee20", color="#06b6d4", fontcolor="#0e7490"];
  edge [color="#06b6d4"];
  
  A [label="Start"];
  B [label="Process"];
  C [label="Decision", shape=diamond];
  D [label="End"];
  
  A -> B;
  B -> C;
  C -> D [label="Yes"];
  C -> B [label="No"];
}`
  );
  const [diagramType, setDiagramType] = useState('graphviz');
  const [outputFormat, setOutputFormat] = useState('svg');
  const [method, setMethod] = useState('POST');
  const [diagramOptions, setDiagramOptions] = useState({});
  const [renderedDiagram, setRenderedDiagram] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [encodedUrl, setEncodedUrl] = useState('');

  // Mock function to simulate Kroki API
  const renderDiagram = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));

      // For demo purposes, we'll use the actual Kroki API
      if (method === 'POST') {
        // Using plain-text POST
        const krokiUrl = `https://kroki.io/${diagramType}/${outputFormat}`;
        const response = await fetch(krokiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'text/plain',
          },
          body: diagramSource,
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(errorText || `HTTP ${response.status}: ${response.statusText}`);
        }

        if (outputFormat === 'svg') {
          const svgText = await response.text();
          setRenderedDiagram({ type: 'svg', content: svgText });
        } else {
          const blob = await response.blob();
          const imageUrl = URL.createObjectURL(blob);
          setRenderedDiagram({ type: 'image', content: imageUrl });
        }

        toast.success('Diagram rendered successfully!');
      } else {
        // GET method - encode the diagram using proper base64 URL encoding
        // For demo purposes, we'll use simple URL encoding
        const encoded = encodeURIComponent(diagramSource);
        const url = `https://kroki.io/${diagramType}/${outputFormat}/${encoded}`;
        setEncodedUrl(url);
        
        // For GET method with images, we can directly use the URL
        // For SVG, we'll use POST to avoid CORS issues
        if (outputFormat === 'svg') {
          // Use POST method for SVG to avoid CORS
          const krokiUrl = `https://kroki.io/${diagramType}/${outputFormat}`;
          const response = await fetch(krokiUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'text/plain',
            },
            body: diagramSource,
          });

          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText || `HTTP ${response.status}: ${response.statusText}`);
          }

          const svgText = await response.text();
          setRenderedDiagram({ type: 'svg', content: svgText });
        } else {
          // For non-SVG formats, use the URL directly
          setRenderedDiagram({ type: 'image', content: url });
        }

        toast.success('Diagram rendered successfully! (URL generated)');
      }
    } catch (err) {
      setError(err.message);
      toast.error('Failed to render diagram: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const clearDiagram = () => {
    setRenderedDiagram(null);
    setError(null);
    setEncodedUrl('');
    toast.info('Preview cleared');
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-background to-muted">
      <Header />
      
      <div className="flex-1 flex flex-col lg:flex-row gap-4 p-4 overflow-hidden">
        {/* Left Side - Editor and Options */}
        <div className="flex-1 flex flex-col gap-4 min-h-0">
          <EditorPanel
            diagramSource={diagramSource}
            setDiagramSource={setDiagramSource}
            diagramType={diagramType}
            setDiagramType={setDiagramType}
            outputFormat={outputFormat}
            setOutputFormat={setOutputFormat}
            method={method}
            setMethod={setMethod}
            onRender={renderDiagram}
            onClear={clearDiagram}
            isLoading={isLoading}
          />
          
          <OptionsPanel
            diagramOptions={diagramOptions}
            setDiagramOptions={setDiagramOptions}
            encodedUrl={encodedUrl}
            method={method}
          />
        </div>

        {/* Right Side - Preview */}
        <div className="flex-1 min-h-0">
          <PreviewPanel
            renderedDiagram={renderedDiagram}
            isLoading={isLoading}
            error={error}
            outputFormat={outputFormat}
          />
        </div>
      </div>
    </div>
  );
};

export default DiagramRenderer;