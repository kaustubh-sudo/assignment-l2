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
import { Sparkles } from 'lucide-react';

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
    <Card className="h-full flex flex-col shadow-xl border-border/50 bg-card/95 backdrop-blur-sm rounded-2xl">
      <CardHeader className="flex-none pb-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <CardTitle className="text-lg md:text-xl font-semibold">
            Preview
          </CardTitle>
          
          <div className="flex items-center gap-1.5 md:gap-2">
            {renderedDiagram && (
              <>
                {/* Zoom Controls - Compact on mobile */}
                <div className="flex items-center gap-0.5 md:gap-1 border border-border rounded-xl p-0.5 md:p-1 bg-background/50">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleZoomOut}
                    className="h-7 w-7 md:h-8 md:w-8 p-0 hover:bg-muted rounded-lg"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </Button>
                  
                  <span className="text-xs font-medium px-2 md:px-3 min-w-[50px] text-center">
                    {Math.round(zoom)}%
                  </span>
                  
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleZoomIn}
                    className="h-7 w-7 md:h-8 md:w-8 p-0 hover:bg-muted rounded-lg"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleResetZoom}
                    className="h-7 w-7 md:h-8 md:w-8 p-0 hover:bg-muted rounded-lg"
                  >
                    <Maximize2 className="w-4 h-4" />
                  </Button>
                </div>
                
                {/* Export Button */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      size="sm"
                      className="bg-gradient-to-r from-blue-600 to-teal-600 hover:from-blue-700 hover:to-teal-700 text-white h-8 md:h-9 px-3 md:px-4 text-xs md:text-sm rounded-xl shadow-lg"
                    >
                      <Download className="w-4 h-4 md:mr-2" />
                      <span className="hidden md:inline">Export</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="bg-background border-border shadow-xl">
                    <DropdownMenuItem onClick={() => onExport('svg')} className="cursor-pointer">
                      <span className="font-medium text-sm">SVG</span>
                      <span className="text-xs text-muted-foreground ml-2">(Vector)</span>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onExport('png')} className="cursor-pointer">
                      <span className="font-medium text-sm">PNG</span>
                      <span className="text-xs text-muted-foreground ml-2">(Image)</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 p-3 md:p-4 lg:p-5 overflow-hidden">
        <div className="h-full flex items-center justify-center bg-muted/20 rounded-xl border border-border/50 overflow-auto custom-scrollbar">
          {isLoading ? (
            <div className="w-full h-full p-6 space-y-4">
              <Skeleton className="w-full h-8 bg-muted" />
              <Skeleton className="w-3/4 h-8 bg-muted" />
              <Skeleton className="w-full h-32 bg-muted" />
              <Skeleton className="w-5/6 h-8 bg-muted" />
              <div className="flex justify-center items-center py-8">
                <div className="relative">
                  <div className="animate-spin rounded-full h-16 w-16 border-4 border-primary border-t-transparent" />
                  <Sparkles className="w-8 h-8 text-primary absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                </div>
              </div>
              <p className="text-center text-base text-muted-foreground font-medium">Creating your diagram...</p>
            </div>
          ) : error ? (
            <Alert variant="destructive" className="m-6 max-w-2xl">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-sm">
                {error}
              </AlertDescription>
            </Alert>
          ) : renderedDiagram ? (
            <div className="w-full h-full p-6 flex items-center justify-center animate-fade-in overflow-auto">
              {renderedDiagram.type === 'svg' ? (
                <div
                  className="flex items-center justify-center transition-transform duration-200"
                  style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'center center' }}
                  dangerouslySetInnerHTML={{ __html: renderedDiagram.content }}
                />
              ) : (
                <img
                  src={renderedDiagram.content}
                  alt="Generated diagram"
                  className="object-contain transition-transform duration-200"
                  style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'center center' }}
                />
              )}
            </div>
          ) : (
            <div className="text-center text-muted-foreground space-y-4 p-8">
              <ImageIcon className="w-20 h-20 md:w-24 md:h-24 mx-auto opacity-20" />
              <p className="text-lg md:text-xl font-semibold">Ready to create something amazing?</p>
              <p className="text-base text-muted-foreground/80">Describe your diagram on the left and click "Generate Diagram"</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default PreviewPanel;