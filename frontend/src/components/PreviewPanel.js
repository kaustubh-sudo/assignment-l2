import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { Skeleton } from './ui/skeleton';
import { Eye, AlertCircle, FileImage } from 'lucide-react';

const PreviewPanel = ({ renderedDiagram, isLoading, error, outputFormat }) => {
  return (
    <Card className="h-full flex flex-col shadow-lg border-border/50 bg-card/95 backdrop-blur-sm">
      <CardHeader className="pb-3 border-b border-border/50">
        <div className="flex items-center gap-2">
          <Eye className="w-5 h-5 text-secondary" />
          <CardTitle className="text-lg">Preview</CardTitle>
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
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent" />
              </div>
            </div>
          ) : error ? (
            <Alert variant="destructive" className="m-6 max-w-2xl">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="font-mono text-sm whitespace-pre-wrap">
                {error}
              </AlertDescription>
            </Alert>
          ) : renderedDiagram ? (
            <div className="w-full h-full p-6 flex items-center justify-center animate-fade-in">
              {renderedDiagram.type === 'svg' ? (
                <div
                  className="w-full h-full flex items-center justify-center"
                  dangerouslySetInnerHTML={{ __html: renderedDiagram.content }}
                />
              ) : (
                <img
                  src={renderedDiagram.content}
                  alt="Rendered diagram"
                  className="max-w-full max-h-full object-contain"
                />
              )}
            </div>
          ) : (
            <div className="text-center text-muted-foreground space-y-3 p-6">
              <FileImage className="w-16 h-16 mx-auto opacity-30" />
              <p className="text-sm">No diagram rendered yet</p>
              <p className="text-xs">Configure your diagram and click "Render Diagram" to preview</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default PreviewPanel;