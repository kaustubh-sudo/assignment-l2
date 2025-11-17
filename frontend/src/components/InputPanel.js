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
    <Card className="h-full flex flex-col shadow-xl border-border/50 bg-card/95 backdrop-blur-sm rounded-2xl">
      <CardHeader className="pb-4 border-b border-border/50">
        <CardTitle className="text-lg md:text-xl font-semibold">
          Describe Your Diagram
        </CardTitle>
        <p className="text-base text-muted-foreground mt-2">
          Explain what you want to visualize in plain language
        </p>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col gap-5 pt-5 overflow-hidden">
        <div className="space-y-3">
          <Label htmlFor="diagram-type" className="text-base font-medium">
            What type of diagram?
          </Label>
          <Select value={diagramType} onValueChange={setDiagramType}>
            <SelectTrigger id="diagram-type" className="h-12 bg-background/50">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-background border-border shadow-xl">
              {DIAGRAM_TYPES.map((type) => (
                <SelectItem key={type.value} value={type.value} className="cursor-pointer py-1 px-3 h-auto leading-none">
                  <div className="flex flex-col items-start py-0.5">
                    <span className="font-medium text-sm leading-tight mb-0.5">{type.label}</span>
                    <span className="text-[10px] text-muted-foreground/70 leading-tight">{type.description}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1 flex flex-col gap-3 min-h-0">
          <Label htmlFor="user-input" className="text-base font-medium">
            Describe what you want to create
          </Label>
          <Textarea
            id="user-input"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Example: Create a flowchart showing the customer support process from ticket creation to resolution..."
            className="flex-1 text-base leading-relaxed custom-scrollbar resize-none min-h-[150px] md:min-h-[200px] bg-background/50"
          />
        </div>

        {generatedCode && (
          <Collapsible open={showCode} onOpenChange={setShowCode}>
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-between text-sm text-muted-foreground hover:text-foreground"
              >
                <span className="flex items-center gap-2">
                  <Code2 className="w-4 h-4 flex-shrink-0" />
                  Generated Code
                </span>
                {showCode ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-2">
              <div className="rounded-lg bg-[hsl(var(--editor-bg))] p-4 max-h-40 overflow-auto custom-scrollbar">
                <pre className="text-sm text-[hsl(var(--editor-foreground))] font-mono whitespace-pre-wrap break-all">
                  {generatedCode}
                </pre>
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}

        <div className="flex gap-3 pt-2">
          <Button
            onClick={onGenerate}
            disabled={isGenerating || isRendering || !userInput.trim()}
            className="flex-1 bg-gradient-to-r from-blue-600 to-teal-600 hover:from-blue-700 hover:to-teal-700 text-white transition-all duration-300 shadow-lg hover:shadow-xl h-12 text-base font-medium rounded-xl"
          >
            <Sparkles className="w-5 h-5 mr-2" />
            {isGenerating ? 'Thinking...' : isRendering ? 'Creating...' : 'Generate Diagram'}
          </Button>
          <Button
            onClick={onClear}
            variant="outline"
            className="border-border hover:bg-muted h-12 px-4 rounded-xl"
          >
            <RotateCcw className="w-5 h-5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default InputPanel;