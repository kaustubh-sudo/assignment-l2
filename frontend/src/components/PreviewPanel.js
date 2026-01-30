import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { Skeleton } from './ui/skeleton';
import { AlertCircle, Image as ImageIcon, Download, ZoomIn, ZoomOut, Maximize2, Loader2 } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { Sparkles } from 'lucide-react';

const PreviewPanel = ({ renderedDiagram, isLoading, error, onExport, isExporting }) => {
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
    <Card className="h-full flex flex-col shadow-lg border-slate-200 bg-white rounded-xl sm:rounded-2xl">
      <CardHeader className="flex-none pb-3 sm:pb-4 px-4 sm:px-6">
        <div className="flex items-center justify-between flex-wrap gap-2 sm:gap-3">
          <CardTitle className="text-base sm:text-lg md:text-xl font-semibold text-slate-800">
            Preview
          </CardTitle>
          
          <div className="flex items-center gap-1 sm:gap-1.5 md:gap-2">
            {renderedDiagram && (
              <>
                {/* Zoom Controls - Compact on mobile */}
                <div className="flex items-center gap-0.5 border border-slate-200 rounded-lg sm:rounded-xl p-0.5 bg-slate-50">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleZoomOut}
                    className="h-7 w-7 p-0 hover:bg-slate-200 rounded-md sm:rounded-lg"
                  >
                    <ZoomOut className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-slate-600" />
                  </Button>
                  
                  <span className="text-xs font-medium px-1.5 sm:px-2 min-w-[40px] sm:min-w-[50px] text-center text-slate-600">
                    {Math.round(zoom)}%
                  </span>
                  
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleZoomIn}
                    className="h-7 w-7 p-0 hover:bg-slate-200 rounded-md sm:rounded-lg"
                  >
                    <ZoomIn className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-slate-600" />
                  </Button>
                  
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleResetZoom}
                    className="h-7 w-7 p-0 hover:bg-slate-200 rounded-md sm:rounded-lg"
                  >
                    <Maximize2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-slate-600" />
                  </Button>
                </div>
                
                {/* Export Button */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      size="sm"
                      disabled={isExporting}
                      className="bg-gradient-to-r from-blue-600 to-teal-600 hover:from-blue-700 hover:to-teal-700 text-white h-7 sm:h-8 md:h-9 px-2 sm:px-3 md:px-4 text-xs md:text-sm rounded-lg sm:rounded-xl shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                      data-testid="export-button"
                    >
                      {isExporting ? (
                        <Loader2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 animate-spin sm:mr-2" />
                      ) : (
                        <Download className="w-3.5 h-3.5 sm:w-4 sm:h-4 sm:mr-2" />
                      )}
                      <span className="hidden sm:inline">{isExporting ? 'Exporting...' : 'Export'}</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="bg-white border-slate-200 shadow-lg">
                    <DropdownMenuItem 
                      onClick={() => onExport('svg')} 
                      className="cursor-pointer"
                      disabled={isExporting}
                      data-testid="export-svg-option"
                    >
                      <span className="font-medium text-sm text-slate-800">SVG</span>
                      <span className="text-xs text-slate-500 ml-2">(Vector)</span>
                    </DropdownMenuItem>
                    <DropdownMenuItem 
                      onClick={() => onExport('png')} 
                      className="cursor-pointer"
                      disabled={isExporting}
                      data-testid="export-png-option"
                    >
                      <span className="font-medium text-sm text-slate-800">PNG</span>
                      <span className="text-xs text-slate-500 ml-2">(Image)</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 p-3 sm:p-4 lg:p-5 overflow-hidden">
        <div className="h-full flex items-center justify-center bg-slate-50 rounded-lg sm:rounded-xl border border-slate-200 overflow-auto custom-scrollbar">
          {isLoading ? (
            <div className="w-full h-full p-4 sm:p-6 space-y-4">
              <Skeleton className="w-full h-8 bg-slate-200" />
              <Skeleton className="w-3/4 h-8 bg-slate-200" />
              <Skeleton className="w-full h-32 bg-slate-200" />
              <Skeleton className="w-5/6 h-8 bg-slate-200" />
              <div className="flex justify-center items-center py-6 sm:py-8">
                <div className="relative">
                  <div className="animate-spin rounded-full h-12 w-12 sm:h-16 sm:w-16 border-4 border-blue-500 border-t-transparent" />
                  <Sparkles className="w-6 h-6 sm:w-8 sm:h-8 text-blue-500 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                </div>
              </div>
              <p className="text-center text-sm sm:text-base text-slate-500 font-medium">Creating your diagram...</p>
            </div>
          ) : error ? (
            <Alert variant="destructive" className="m-4 sm:m-6 max-w-2xl">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-sm">
                {error}
              </AlertDescription>
            </Alert>
          ) : renderedDiagram ? (
            <div className="w-full h-full p-4 sm:p-6 flex items-center justify-center animate-fade-in overflow-auto">
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
            <div className="text-center text-slate-400 space-y-3 sm:space-y-4 p-6 sm:p-8">
              <ImageIcon className="w-16 h-16 sm:w-20 sm:h-20 md:w-24 md:h-24 mx-auto opacity-30" />
              <p className="text-base sm:text-lg md:text-xl font-semibold text-slate-600">Ready to create something amazing?</p>
              <p className="text-sm sm:text-base text-slate-400">Describe your diagram on the left and click "Generate Diagram"</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default PreviewPanel;