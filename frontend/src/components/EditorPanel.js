import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Tabs, TabsList, TabsTrigger } from './ui/tabs';
import { Play, RotateCcw, FileCode2 } from 'lucide-react';

const DIAGRAM_TYPES = [
  { value: 'graphviz', label: 'GraphViz (DOT)' },
  { value: 'plantuml', label: 'PlantUML' },
  { value: 'mermaid', label: 'Mermaid' },
  { value: 'blockdiag', label: 'BlockDiag' },
  { value: 'seqdiag', label: 'SeqDiag' },
  { value: 'actdiag', label: 'ActDiag' },
  { value: 'nwdiag', label: 'NwDiag' },
  { value: 'c4plantuml', label: 'C4 with PlantUML' },
  { value: 'ditaa', label: 'Ditaa' },
  { value: 'erd', label: 'ERD' },
  { value: 'excalidraw', label: 'Excalidraw' },
  { value: 'pikchr', label: 'Pikchr' },
  { value: 'structurizr', label: 'Structurizr' },
  { value: 'vega', label: 'Vega' },
  { value: 'vegalite', label: 'Vega-Lite' },
  { value: 'wavedrom', label: 'WaveDrom' },
];

const OUTPUT_FORMATS = [
  { value: 'svg', label: 'SVG' },
  { value: 'png', label: 'PNG' },
  { value: 'pdf', label: 'PDF' },
  { value: 'jpeg', label: 'JPEG' },
];

const EditorPanel = ({
  diagramSource,
  setDiagramSource,
  diagramType,
  setDiagramType,
  outputFormat,
  setOutputFormat,
  method,
  setMethod,
  onRender,
  onClear,
  isLoading,
}) => {
  return (
    <Card className="flex-1 flex flex-col shadow-lg border-border/50 bg-card/95 backdrop-blur-sm min-h-0">
      <CardHeader className="pb-3 border-b border-border/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileCode2 className="w-5 h-5 text-primary" />
            <CardTitle className="text-lg">Diagram Editor</CardTitle>
          </div>
          <Tabs value={method} onValueChange={setMethod} className="w-auto">
            <TabsList className="h-8">
              <TabsTrigger value="POST" className="text-xs px-3">POST</TabsTrigger>
              <TabsTrigger value="GET" className="text-xs px-3">GET</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col gap-4 pt-4 min-h-0">
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="diagram-type" className="text-xs font-medium text-muted-foreground">
              Diagram Type
            </Label>
            <Select value={diagramType} onValueChange={setDiagramType}>
              <SelectTrigger id="diagram-type" className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]">
                {DIAGRAM_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="output-format" className="text-xs font-medium text-muted-foreground">
              Output Format
            </Label>
            <Select value={outputFormat} onValueChange={setOutputFormat}>
              <SelectTrigger id="output-format" className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {OUTPUT_FORMATS.map((format) => (
                  <SelectItem key={format.value} value={format.value}>
                    {format.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex-1 flex flex-col gap-2 min-h-0">
          <Label htmlFor="diagram-source" className="text-xs font-medium text-muted-foreground">
            Diagram Source Code
          </Label>
          <Textarea
            id="diagram-source"
            value={diagramSource}
            onChange={(e) => setDiagramSource(e.target.value)}
            placeholder="Enter your diagram code here..."
            className="flex-1 font-mono text-sm code-editor custom-scrollbar resize-none min-h-[200px]"
          />
        </div>

        <div className="flex gap-2">
          <Button
            onClick={onRender}
            disabled={isLoading || !diagramSource.trim()}
            className="flex-1 bg-gradient-to-r from-primary to-secondary hover:opacity-90 transition-all duration-300 shadow-md hover:shadow-lg"
          >
            <Play className="w-4 h-4 mr-2" />
            {isLoading ? 'Rendering...' : 'Render Diagram'}
          </Button>
          <Button
            onClick={onClear}
            variant="outline"
            className="border-destructive/30 text-destructive hover:bg-destructive/10"
          >
            <RotateCcw className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default EditorPanel;