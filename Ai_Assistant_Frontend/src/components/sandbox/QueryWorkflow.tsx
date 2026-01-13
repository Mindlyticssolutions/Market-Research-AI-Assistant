import { useState } from 'react';
import { Clock, Sparkles, ChevronLeft, ChevronRight, X, Loader2, Play, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function QueryWorkflow() {
  const { queries, activeQueryId, setActiveQuery, removeQuery } = useAppStore();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <motion.div
      className="h-full flex flex-col bg-sidebar border-r border-sidebar-border"
      animate={{ width: isCollapsed ? 64 : 256 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
    >
      {/* Header */}
      <div className="h-14 flex items-center justify-between px-3 border-b border-sidebar-border">
        <AnimatePresence mode="wait">
          {!isCollapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2"
            >
              <span className="text-sm font-medium text-foreground">Query Workflow</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                {queries.length}
              </span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Query List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {queries.length === 0 ? (
          !isCollapsed && (
            <div className="text-center py-12">
              <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center mx-auto mb-3">
                <Sparkles className="w-5 h-5 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground">
                No queries yet
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Use AI to create your first query
              </p>
            </div>
          )
        ) : (
          queries.map((query, index) => (
            <TooltipProvider key={query.id}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    onClick={() => setActiveQuery(query.id)}
                    className={cn(
                      'w-full text-left rounded-xl transition-all relative group cursor-pointer border',
                      'hover:bg-sidebar-accent hover:border-primary/20 hover:shadow-md',
                      isCollapsed ? 'p-2 flex items-center justify-center' : 'p-3',
                      activeQueryId === query.id
                        ? 'bg-sidebar-accent border-primary shadow-sm ring-1 ring-primary/20'
                        : 'bg-transparent border-transparent'
                    )}
                  >
                    <div className={cn(
                      'w-6 h-6 rounded-md flex items-center justify-center text-xs font-medium shrink-0 transition-colors',
                      activeQueryId === query.id || query.status === 'running' || query.status === 'generating'
                        ? 'bg-primary text-primary-foreground'
                        : query.status === 'success' ? 'bg-green-500/20 text-green-500'
                          : query.status === 'error' ? 'bg-red-500/20 text-red-500'
                            : 'bg-muted text-muted-foreground'
                    )}>
                      {query.status === 'generating' ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : query.status === 'running' ? (
                        <Play className="w-3 h-3 fill-current animate-pulse" />
                      ) : query.status === 'success' ? (
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      ) : query.status === 'error' ? (
                        <AlertCircle className="w-3.5 h-3.5" />
                      ) : (
                        <div className="w-1.5 h-1.5 rounded-full bg-muted-foreground/30" />
                      )}
                    </div>

                    {/* Active Execution Glow Overlay */}
                    {(query.status === 'running' || query.status === 'generating') && (
                      <motion.div
                        layoutId={`glow-${query.id}`}
                        className="absolute inset-0 rounded-xl border border-primary/50 pointer-events-none"
                        initial={{ opacity: 0 }}
                        animate={{
                          opacity: [0.3, 0.6, 0.3],
                          scale: [1, 1.01, 1],
                          boxShadow: [
                            "0 0 0px var(--primary)",
                            "0 0 8px var(--primary)",
                            "0 0 0px var(--primary)"
                          ]
                        }}
                        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                      />
                    )}
                    {!isCollapsed && (
                      <>
                        <div className="flex flex-col gap-1 mb-1 mt-2">
                          <div className="flex items-start justify-between gap-2">
                            <span className="text-sm font-medium text-foreground leading-tight line-clamp-2 flex-1">
                              {query.title || ((query.prompt || '').length > 30 ? (query.prompt || '').substring(0, 30) + "..." : (query.prompt || 'New Query'))}
                            </span>
                            {(query.status === 'running' || query.status === 'generating') && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary animate-pulse font-medium whitespace-nowrap shrink-0">
                                Active
                              </span>
                            )}
                          </div>
                          {query.status === 'success' && query.output && (
                            <div className="flex items-center gap-1.5 text-[10px] text-green-500/90 font-mono bg-green-500/5 px-1.5 py-0.5 rounded border border-green-500/10 w-fit max-w-full overflow-hidden">
                              <span className="shrink-0 opacity-70">Result:</span>
                              <span className="truncate">
                                {query.output.replace(/[\n\r]/g, ' ')}
                              </span>
                            </div>
                          )}
                        </div>
                        {(query.prompt || '').toLowerCase() !== (query.title || '').toLowerCase() && (
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {query.prompt}
                          </p>
                        )}
                        <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                          <Clock className="w-3 h-3" />
                          <span>{formatTime(query.createdAt)}</span>
                        </div>
                      </>
                    )}
                    {!isCollapsed && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeQuery(query.id);
                        }}
                        className={cn(
                          "absolute top-2 right-2 p-1 rounded-md opacity-0 group-hover:opacity-100 transition-opacity",
                          "hover:bg-destructive/10 hover:text-destructive",
                          activeQueryId === query.id ? "text-primary-foreground/60 hover:text-primary-foreground" : "text-muted-foreground"
                        )}
                        title="Delete query"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    )}
                  </motion.div>
                </TooltipTrigger>
                <TooltipContent side="right" className="max-w-[300px]">
                  <p className="text-xs text-muted-foreground">{query.prompt}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ))
        )}
      </div>

      {/* Collapse Toggle */}
      <div className="p-3 border-t border-sidebar-border">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={cn(
            'w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg',
            'text-sidebar-foreground hover:text-sidebar-accent-foreground',
            'hover:bg-sidebar-accent transition-colors'
          )}
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span className="text-xs">Collapse</span>
            </>
          )}
        </button>
      </div>
    </motion.div>
  );
}
