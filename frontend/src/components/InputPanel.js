import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Sparkles, RotateCcw, Code2, ChevronDown, ChevronUp, Save, Clock } from 'lucide-react';
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
  // Save props
  onSave,
  canSave,
  savedDiagram,
  lastSavedAt,
}) => {
  return (
    <Card className="h-full flex flex-col shadow-lg border-slate-200 bg-white rounded-xl sm:rounded-2xl overflow-hidden">
      {/* Header */}
      <CardHeader className="flex-shrink-0 pb-3 sm:pb-4 border-b border-slate-100 px-4 sm:px-6 pt-4 sm:pt-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base sm:text-lg md:text-xl font-semibold text-slate-800">
              Describe Your Diagram
            </CardTitle>
            <p className="text-sm text-slate-500 mt-1">
              Explain what you want to visualize in plain language
            </p>
          </div>
          {lastSavedAt && (
            <div className="flex-shrink-0 flex items-center gap-1.5 text-xs text-slate-400 bg-slate-100 px-2 py-1 rounded-md whitespace-nowrap">
              <Clock className="w-3 h-3" />
              <span>{lastSavedAt}</span>
            </div>
          )}
        </div>
      </CardHeader>
      
      {/* Content */}
      <CardContent className="flex-1 flex flex-col gap-4 pt-4 pb-4 overflow-auto px-4 sm:px-6">
        {/* Diagram Type Selection */}
        <div className="flex-shrink-0">
          <Label className="text-sm font-medium text-slate-700 mb-2 block">
            Choose diagram type
          </Label>
          <div className="flex flex-wrap gap-2">
            {DIAGRAM_TYPES.map((type) => (
              <button
                key={type.value}
                onClick={() => setDiagramType(type.value)}
                className={`
                  flex flex-col items-start px-3 py-2 rounded-lg border-2 transition-all duration-200
                  ${diagramType === type.value 
                    ? 'border-blue-500 bg-blue-50 shadow-sm' 
                    : 'border-slate-200 bg-white hover:border-blue-300 hover:bg-slate-50'
                  }
                `}
                data-testid={`diagram-type-${type.value}`}
              >
                <span className="font-medium text-sm text-slate-800">{type.label}</span>
                <span className="text-xs text-slate-500 hidden sm:block">{type.description}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Text Input */}
        <div className="flex-1 flex flex-col min-h-0">
          <Label htmlFor="user-input" className="text-sm font-medium text-slate-700 mb-2 block flex-shrink-0">
            Describe what you want to create
          </Label>
          <Textarea
            id="user-input"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder="Example: Create a flowchart showing the customer support process from ticket creation to resolution..."
            className="flex-1 text-sm leading-relaxed resize-none min-h-[120px] bg-slate-50 border-slate-200 text-slate-800 placeholder-slate-400 focus:ring-blue-500 focus:border-blue-500"
            data-testid="diagram-input-textarea"
          />
        </div>

        {/* Generated Code (Collapsible) */}
        {generatedCode && (
          <Collapsible open={showCode} onOpenChange={setShowCode} className="flex-shrink-0">
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-between text-sm text-slate-500 hover:text-slate-700 hover:bg-slate-50 h-9"
              >
                <span className="flex items-center gap-2">
                  <Code2 className="w-4 h-4 flex-shrink-0" />
                  Generated Code
                </span>
                {showCode ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-2">
              <div className="rounded-lg bg-slate-800 p-3 max-h-32 overflow-auto">
                <pre className="text-xs text-slate-100 font-mono whitespace-pre-wrap break-all">
                  {generatedCode}
                </pre>
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Action Buttons */}
        <div className="flex-shrink-0 flex gap-2 pt-2">
          <Button
            onClick={onGenerate}
            disabled={isGenerating || isRendering || !userInput.trim()}
            className="flex-1 bg-gradient-to-r from-blue-600 to-teal-600 hover:from-blue-700 hover:to-teal-700 text-white transition-all duration-300 shadow-md hover:shadow-lg h-10 sm:h-11 text-sm font-medium rounded-lg"
            data-testid="generate-diagram-btn"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            {isGenerating ? 'Thinking...' : isRendering ? 'Creating...' : 'Generate Diagram'}
          </Button>
          <Button
            onClick={onSave}
            disabled={!canSave}
            variant="outline"
            className="border-slate-200 hover:bg-green-50 hover:border-green-300 h-10 sm:h-11 px-3 rounded-lg transition-all"
            title={savedDiagram ? 'Update diagram' : 'Save diagram'}
            data-testid="save-diagram-btn"
          >
            <Save className="w-4 h-4" />
          </Button>
          <Button
            onClick={onClear}
            variant="outline"
            className="border-slate-200 hover:bg-slate-50 h-10 sm:h-11 px-3 rounded-lg"
            data-testid="clear-diagram-btn"
          >
            <RotateCcw className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default InputPanel;
