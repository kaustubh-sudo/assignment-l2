import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Settings, Plus, X, Copy, Check } from 'lucide-react';
import { toast } from 'sonner';

const OptionsPanel = ({ diagramOptions, setDiagramOptions, encodedUrl, method }) => {
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [copied, setCopied] = useState(false);

  const addOption = () => {
    if (newKey.trim() && newValue.trim()) {
      setDiagramOptions({
        ...diagramOptions,
        [newKey.trim()]: newValue.trim(),
      });
      setNewKey('');
      setNewValue('');
      toast.success('Option added');
    }
  };

  const removeOption = (key) => {
    const updated = { ...diagramOptions };
    delete updated[key];
    setDiagramOptions(updated);
    toast.info('Option removed');
  };

  const copyUrl = () => {
    if (encodedUrl) {
      navigator.clipboard.writeText(encodedUrl);
      setCopied(true);
      toast.success('URL copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Card className="shadow-lg border-border/50 bg-card/95 backdrop-blur-sm">
      <CardHeader className="pb-3 border-b border-border/50">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-accent" />
          <CardTitle className="text-lg">Options & Configuration</CardTitle>
        </div>
      </CardHeader>
      
      <CardContent className="pt-4 space-y-4">
        {/* Diagram Options */}
        <div className="space-y-3">
          <Label className="text-xs font-medium text-muted-foreground">Diagram Options (Key-Value)</Label>
          
          <div className="flex gap-2">
            <Input
              placeholder="Key"
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addOption()}
              className="flex-1 h-9 text-sm"
            />
            <Input
              placeholder="Value"
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addOption()}
              className="flex-1 h-9 text-sm"
            />
            <Button
              size="sm"
              onClick={addOption}
              disabled={!newKey.trim() || !newValue.trim()}
              className="h-9 bg-accent hover:bg-accent/90 text-accent-foreground"
            >
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          {Object.keys(diagramOptions).length > 0 && (
            <div className="space-y-2 pt-2">
              {Object.entries(diagramOptions).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center justify-between p-2 rounded-md bg-muted/50 border border-border/50 group hover:border-accent/50 transition-colors"
                >
                  <div className="flex-1 flex items-center gap-2 font-mono text-xs">
                    <Badge variant="outline" className="text-xs px-2 py-0.5">
                      {key}
                    </Badge>
                    <span className="text-muted-foreground">=</span>
                    <span className="text-foreground">{value}</span>
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={() => removeOption(key)}
                    className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive hover:bg-destructive/10"
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Encoded URL for GET method */}
        {method === 'GET' && encodedUrl && (
          <div className="space-y-2 pt-4 border-t border-border/50">
            <Label className="text-xs font-medium text-muted-foreground">Encoded GET URL</Label>
            <div className="flex gap-2">
              <Input
                value={encodedUrl}
                readOnly
                className="flex-1 h-9 text-xs font-mono bg-muted/30"
              />
              <Button
                size="sm"
                variant="outline"
                onClick={copyUrl}
                className="h-9"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-success" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        )}

        {/* Info */}
        <div className="pt-4 border-t border-border/50">
          <p className="text-xs text-muted-foreground leading-relaxed">
            Add optional diagram-specific options as key-value pairs. These will be sent with your request to customize the rendering behavior.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default OptionsPanel;