import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { Skeleton } from './ui/skeleton';
import { Eye, AlertCircle, Image as ImageIcon, Download, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';

const PreviewPanel = ({ renderedDiagram, isLoading, error, onExport }) => {
  const [zoom, setZoom] = useState(100);
  
  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 10, 200));
  };
  
  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 10, 30));
  };
  
  const handleResetZoom = () => {
    setZoom(100);
  };
  return (
    <Card className="h-full flex flex-col shadow-lg border-border/50 bg-card/95 backdrop-blur-sm">
      <CardHeader className="pb-3 border-b border-border/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Eye className="w-5 h-5 text-secondary" />
            <CardTitle className="text-lg">Preview</CardTitle>
          </div>
          
          <div className="flex items-center gap-2">
            {renderedDiagram && !isLoading && (
              <>
                {/* Zoom Controls */}
                <div className="flex items-center gap-1 border border-border rounded-lg p-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleZoomOut}
                    className="h-7 w-7 p-0"
                    title="Zoom Out"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </Button>
                  <span className="text-xs font-medium px-2 min-w-[3rem] text-center">
                    {zoom}%
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleZoomIn}
                    className="h-7 w-7 p-0"
                    title="Zoom In"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleResetZoom}
                    className="h-7 w-7 p-0"
                    title="Reset Zoom"
                  >
                    <Maximize2 className="w-4 h-4" />
                  </Button>
                </div>
                
                {/* Export Button */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      size="sm"
                      className="bg-accent hover:bg-accent/90 text-accent-foreground"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Export
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onExport('svg')}>
                      <span className="font-medium">Download as SVG</span>
                      <span className="text-xs text-muted-foreground ml-2">(Vector)</span>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onExport('png')}>
                      <span className="font-medium">Download as PNG</span>
                      <span className="text-xs text-muted-foreground ml-2">(Image)</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 p-4 overflow-hidden">
        <div className="h-full flex items-center justify-center bg-muted/30 rounded-lg border border-border/50 overflow-auto custom-scrollbar">
          {isLoading ? (
            <div className="w-full h-full p-6 space-y-4">
              <Skeleton className="w-full h-8 bg-muted" />
              <Skeleton className="w-3/4 h-8 bg-muted" />
              <Skeleton className="w-full h-32 bg-muted" />
              <Skeleton className="w-5/6 h-8 bg-muted" />
              <div className="flex justify-center items-center py-8">
                <div className="relative">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent" />
                  <Sparkles className="w-6 h-6 text-primary absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                </div>
              </div>
              <p className="text-center text-sm text-muted-foreground">Creating your diagram...</p>
            </div>
          ) : error ? (
            <Alert variant="destructive" className="m-6 max-w-2xl">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-sm">
                {error}
              </AlertDescription>
            </Alert>
          ) : renderedDiagram ? (
            <div className="w-full h-full p-6 flex items-center justify-center animate-fade-in">
              {renderedDiagram.type === 'svg' ? (
                <div
                  className="w-full h-full flex items-center justify-center"
                  style={{ transform: `scale(${zoom / 100})` }}
                  dangerouslySetInnerHTML={{ __html: renderedDiagram.content }}
                />
              ) : (
                <img
                  src={renderedDiagram.content}
                  alt="Generated diagram"
                  className="max-w-full max-h-full object-contain"
                  style={{ transform: `scale(${zoom / 100})` }}
                />
              )}
            </div>
          ) : (
            <div className="text-center text-muted-foreground space-y-3 p-6">
              <ImageIcon className="w-16 h-16 mx-auto opacity-30" />
              <p className="text-base font-medium">Ready to create something amazing?</p>
              <p className="text-sm">Describe your diagram on the left and click "Generate Diagram"</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Import Sparkles for loading animation
import { Sparkles } from 'lucide-react';

export default PreviewPanel;