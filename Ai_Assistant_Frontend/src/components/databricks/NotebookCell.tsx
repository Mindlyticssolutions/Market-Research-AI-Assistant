import { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Play, Trash2, ChevronUp, ChevronDown, Check, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useTheme } from 'next-themes';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface NotebookCellProps {
  id: string;
  code: string;
  output?: string;
  status?: 'idle' | 'running' | 'success' | 'error';
  type: 'code' | 'markdown';
  isActive?: boolean;
  onCodeChange: (value: string) => void;
  onRun: () => void;
  onDelete: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
}

export function NotebookCell({
  code = '',
  output,
  status = 'idle',
  type,
  isActive,
  onCodeChange,
  onRun,
  onDelete,
  onMoveUp,
  onMoveDown
}: NotebookCellProps) {
  const { resolvedTheme } = useTheme();
  const [isHovered, setIsHovered] = useState(false);
  const [isEditing, setIsEditing] = useState(true); // For markdown toggle

  // Ensure code is always a string
  const safeCode = code || '';

  // Auto-switch to preview for markdown if successful run
  const showPreview = type === 'markdown' && status === 'success' && !isEditing;

  const handleRun = () => {
    onRun();
    if (type === 'markdown') {
      setIsEditing(false);
    }
  };

  return (
    <div
      className={cn(
        "group relative border rounded-lg mb-4 transition-all duration-200",
        isActive ? "ring-2 ring-primary border-primary shadow-lg scale-[1.01]" : "border-border hover:border-border/80",
        status === 'running' && !isActive ? "border-primary shadow-md ring-1 ring-primary/20" : "",
        "bg-card"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Side controls */}
      <div className={cn(
        "absolute -left-12 top-2 flex flex-col gap-1 transition-opacity duration-200",
        isHovered ? "opacity-100" : "opacity-0"
      )}>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onMoveUp}>
          <ChevronUp className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onMoveDown}>
          <ChevronDown className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={onDelete}>
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>

      {/* Cell Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-muted/30 border-b border-border/50 rounded-t-lg">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-muted-foreground uppercase">{type}</span>
          {status === 'running' && (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-medium animate-in fade-in">
              <Loader2 className="h-3 w-3 animate-spin" />
              Running...
            </div>
          )}
          {status === 'success' && (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-green-500/10 text-green-600 text-[10px] font-medium animate-in fade-in">
              <Check className="h-3 w-3" />
              Done
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {type === 'markdown' && !isEditing && (
            <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => setIsEditing(true)}>
              Edit
            </Button>
          )}
          <Button
            variant="secondary"
            size="sm"
            className={cn("h-7 gap-1.5 text-xs", status === 'running' && "opacity-50 pointer-events-none")}
            onClick={handleRun}
          >
            <Play className="h-3 w-3 fill-current" />
            {type === 'markdown' ? 'Render' : 'Run Cell'}
          </Button>
        </div>
      </div>

      {/* Content Area */}
      <div className="min-h-[100px] border-b border-border/50 bg-card rounded-b-lg">
        {type === 'markdown' && !isEditing ? (
          <div className="p-6 prose dark:prose-invert max-w-none" onDoubleClick={() => setIsEditing(true)}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{safeCode}</ReactMarkdown>
          </div>
        ) : (
          <div className="py-4">
            <Editor
              height={Math.max(100, (safeCode.split('\n').length * 21) + 24) + "px"}
              value={safeCode}
              defaultLanguage={type === 'code' ? 'python' : 'markdown'}
              onChange={(val) => onCodeChange(val || '')}
              theme={resolvedTheme === 'dark' ? 'vs-dark' : 'light'}
              options={{
                minimap: { enabled: false },
                lineNumbers: 'on',
                folding: false,
                scrollBeyondLastLine: false,
                automaticLayout: true,
                padding: { top: 8, bottom: 8 },
                fontSize: 14,
                fontFamily: 'JetBrains Mono, monospace',
                renderLineHighlight: 'none',
                overviewRulerLanes: 0,
                hideCursorInOverviewRuler: true,
                scrollbar: {
                  vertical: 'hidden',
                  horizontal: 'hidden',
                  alwaysConsumeMouseWheel: false
                },
              }}
            />
          </div>
        )}
      </div>

      {/* Output Area (Code Only) */}
      <AnimatePresence>
        {output && type === 'code' && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="bg-muted/10 border-t border-border/50"
          >
            <div className="p-4 font-mono text-xs overflow-x-auto whitespace-pre-wrap text-foreground/90 max-h-[300px] overflow-y-auto custom-scrollbar">
              {output}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
