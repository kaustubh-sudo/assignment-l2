import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Sparkles, RotateCcw, Code2, ChevronDown, ChevronUp } from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/collapsible';

const DIAGRAM_TYPES = [
  { value: 'graphviz', label: '🔷 GraphViz', description: 'Graphs, flowcharts, and network diagrams' },
  { value: 'mermaid', label: '🧜 Mermaid', description: 'Flowcharts, sequences, and state diagrams' },
  { value: 'plantuml', label: '🌱 PlantUML', description: 'UML diagrams, sequences, and use cases' },
];

const InputPanel = ({
  userInput,
  setUserInput,
  diagramType,
  setDiagramType,
  generatedCode,
  showCode,
  setShowCode,
  onGenerate,
  onClear,
  isGenerating,
  isRendering,
}) => {
  const selectedType = DIAGRAM_TYPES.find(t => t.value === diagramType);

  return (
    <Card className="h-full flex flex-col shadow-lg border-border/50 bg-card/95 backdrop-blur-sm">
      <CardHeader className="pb-3 border-b border-border/50">
        <CardTitle className="text-base font-semibold">
          Describe Your Diagram
        </CardTitle>
        <p className="text-sm text-muted-foreground mt-1.5">
          Explain what you want to visualize in plain language
        </p>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col gap-3 pt-3 overflow-hidden">
        <div className="space-y-1.5">
          <Label htmlFor="diagram-type" className="text-sm font-medium">
            What type of diagram?
          </Label>
          <Select value={diagramType} onValueChange={setDiagramType}>
            <SelectTrigger id="diagram-type" className="h-11">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DIAGRAM_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  <div className="flex flex-col items-start">
                    <span className="font-medium">{type.label}</span>
                    <span className="text-xs text-muted-foreground">{type.description}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1 flex flex-col gap-2 min-h-0">
          <Label htmlFor="user-input" className="text-sm font-medium">
            Describe what you want to create
          </Label>
          <Textarea
            id="user-input"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Example: Create a flowchart showing the customer support process from ticket creation to resolution..."
            className="flex-1 text-sm md:text-base leading-relaxed custom-scrollbar resize-none min-h-[150px] md:min-h-[200px]"
          />
        </div>

        {generatedCode && (
          <Collapsible open={showCode} onOpenChange={setShowCode}>
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-between text-xs text-muted-foreground hover:text-foreground"
              >
                <span className="flex items-center gap-2">
                  <Code2 className="w-3.5 h-3.5 flex-shrink-0" style={{marginTop: '-1px'}} />
                  Generated Code
                </span>
                {showCode ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-2">
              <div className="rounded-lg bg-[hsl(var(--editor-bg))] p-3 max-h-32 overflow-auto custom-scrollbar">
                <pre className="text-xs text-[hsl(var(--editor-foreground))] font-mono whitespace-pre-wrap break-all">
                  {generatedCode}
                </pre>
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}

        <div className="flex gap-2 pt-2">
          <Button
            onClick={onGenerate}
            disabled={isGenerating || isRendering || !userInput.trim()}
            className="flex-1 bg-gradient-to-r from-primary to-secondary hover:opacity-90 transition-all duration-300 shadow-md hover:shadow-lg h-11"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            {isGenerating ? 'Thinking...' : isRendering ? 'Creating...' : 'Generate Diagram'}
          </Button>
          <Button
            onClick={onClear}
            variant="outline"
            className="border-border hover:bg-muted h-11"
          >
            <RotateCcw className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default InputPanel;