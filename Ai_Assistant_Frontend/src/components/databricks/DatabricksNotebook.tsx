import { useState, useEffect, useRef } from 'react';
import { databricksService } from '@/services/databricksService';
import { NotebookCell } from './NotebookCell';
import { ClusterSelector } from './ClusterSelector';
import { Button } from '@/components/ui/button';
import { Plus, Play, Sparkles, RotateCw, Trash, FileText, Code2 } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { toast } from 'sonner';

interface Cell {
  id: string;
  code: string;
  output?: string;
  status: 'idle' | 'running' | 'success' | 'error';
  type: 'code' | 'markdown';
}

export function DatabricksNotebook() {
  const {
    queries,
    activeQueryId,
    updateQuery,
    addQuery,
    removeQuery,
    setActiveQuery // Used to highlight active query
  } = useAppStore();

  const [clusterId, setClusterId] = useState<string>();
  const cellRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  // Auto-scroll to active query
  useEffect(() => {
    if (activeQueryId && cellRefs.current[activeQueryId]) {
      cellRefs.current[activeQueryId]?.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      });
    }
  }, [activeQueryId]);

  // Map queries to cells format
  const cells = queries.map(q => ({
    id: q.id,
    code: q.code,
    output: q.output,
    status: q.status || 'idle',
    type: q.type || 'code'
  }));

  const addCell = (type: 'code' | 'markdown' = 'code') => {
    const newQuery = addQuery(
      type === 'code' ? 'New Query' : 'Markdown Cell',
      type === 'code' ? '' : '### New Markdown Cell'
    );
    // Determine type for new query if not standard
    updateQuery(newQuery.id, { type, status: 'idle' });
  };

  const handleCellChange = (id: string, value: string) => {
    updateQuery(id, { code: value });
  };

  const executeCell = async (id: string) => {
    const cell = cells.find(c => c.id === id);
    if (!cell) return;

    // Handle Markdown "Execution" (Just Render)
    if (cell.type === 'markdown') {
      updateQuery(id, { status: 'success' });
      return;
    }

    if (!clusterId) {
      toast.error("Please select a Databricks cluster first");
      return;
    }

    updateQuery(id, { status: 'running', output: '' });

    try {
      const result = await databricksService.executeCode(clusterId, cell.code);

      updateQuery(id, {
        status: result.status === 'error' ? 'error' : 'success',
        output: result.error || result.output
      });

      // Sync plot results to Insights page via store
      if (result.plot) {
        useAppStore.getState().setActivePlot(result.plot);
        useAppStore.getState().setActivePlotCode(cell.code);
        toast.info("Visualization sent to Insights", {
          action: {
            label: "View",
            onClick: () => window.location.href = '/insights'
          }
        });
      }

    } catch (error) {
      updateQuery(id, { status: 'error', output: 'Failed to execute code' });
      toast.error("Execution failed");
    }
  };

  const runAll = async () => {
    if (!clusterId) {
      toast.error("Please select a Databricks cluster first");
      return;
    }

    // Reset statuses
    // queries.forEach(q => updateQuery(q.id, { status: 'idle' })); // Optional: reset all first?

    for (const cell of cells) {
      // Highlight in sidebar
      setActiveQuery(cell.id);

      updateQuery(cell.id, { status: 'running' });

      try {
        if (cell.type === 'markdown') {
          await new Promise(r => setTimeout(r, 200));
          updateQuery(cell.id, { status: 'success' });
          continue;
        }

        const result = await databricksService.executeCode(clusterId, cell.code);
        const isError = result.status === 'error';

        updateQuery(cell.id, {
          status: isError ? 'error' : 'success',
          output: result.error || result.output
        });

        if (isError) {
          toast.error(`Execution stopped at cell ${cell.id}`);
          break; // Stop on error
        }

      } catch (error) {
        updateQuery(cell.id, { status: 'error', output: 'System Error during Run All' });
        break;
      }
    }
  };

  const restartKernel = async () => {
    if (!clusterId) return;
    try {
      toast.promise(databricksService.restartContext(clusterId), {
        loading: 'Restarting Kernel...',
        success: 'Kernel Restarted. Memory cleared.',
        error: 'Failed to restart kernel'
      });
      // Clear all outputs
      queries.forEach(q => updateQuery(q.id, { status: 'idle', output: '' }));
    } catch (e) {
      console.error(e);
    }
  };

  const clearOutputs = () => {
    queries.forEach(q => updateQuery(q.id, { status: 'idle', output: '' }));
    toast.success("Outputs cleared");
  };

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Toolbar */}
      <div className="h-14 flex items-center justify-between px-4 border-b border-border bg-card">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#ff3621]" />
            <span className="font-semibold text-foreground text-sm">Databricks Notebook</span>
          </div>
          <div className="h-4 w-px bg-border" />
          <ClusterSelector selectedId={clusterId} onSelect={setClusterId} />
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={restartKernel} title="Restart Kernel">
            <RotateCw className="w-4 h-4 text-muted-foreground hover:text-foreground" />
          </Button>
          <Button variant="ghost" size="sm" onClick={clearOutputs} title="Clear Outputs">
            <Trash className="w-4 h-4 text-muted-foreground hover:text-foreground" />
          </Button>
          <div className="h-4 w-px bg-border mx-1" />
          <Button size="sm" variant="secondary" onClick={runAll}>
            <Play className="w-4 h-4 mr-2 fill-current" />
            Run All
          </Button>
        </div>
      </div>

      {/* Notebook Content */}
      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar bg-secondary/10">
        <div className="max-w-5xl mx-auto space-y-4 pb-20">
          {cells.map((cell, index) => (
            <div key={cell.id} ref={el => cellRefs.current[cell.id] = el}>
              <NotebookCell
                // Cast to any because NotebookCell props might slightly differ from exact Query type but we mapped it
                {...cell as any}
                isActive={activeQueryId === cell.id}
                onCodeChange={(val) => handleCellChange(cell.id, val)}
                onRun={() => executeCell(cell.id)}
                onDelete={() => removeQuery(cell.id)}
                onMoveUp={() => {
                  if (index === 0) return;
                  toast.info("Reordering not yet implemented in store sync mode");
                }}
                onMoveDown={() => {
                  toast.info("Reordering not yet implemented in store sync mode");
                }}
              />
            </div>
          ))}

          {/* Add Cell Controls */}
          <div className="flex items-center justify-center gap-4 py-8 opacity-50 hover:opacity-100 transition-opacity">
            <Button variant="outline" className="gap-2 bg-background border-dashed" onClick={() => addCell('code')}>
              <Code2 className="w-4 h-4" />
              Code
            </Button>
            <Button variant="outline" className="gap-2 bg-background border-dashed" onClick={() => addCell('markdown')}>
              <FileText className="w-4 h-4" />
              Text
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
