import { useAppStore } from '@/store/appStore';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart3, Clock, Code2, Download, Maximize2, Share2, Sparkles, Wand2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

const Insights = () => {
    const { activePlot, activePlotCode, queries } = useAppStore();

    const visualizationQueries = queries.filter(q => q.code && (q.code.includes('plt.') || q.code.includes('sns.') || q.code.includes('px.')));

    return (
        <div className="flex-1 flex flex-col h-full bg-background overflow-hidden">
            {/* Header */}
            <div className="h-16 border-b border-border bg-card/50 backdrop-blur-md flex items-center justify-between px-6 shrink-0">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                        <BarChart3 className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h1 className="text-lg font-semibold tracking-tight">Visual Insights</h1>
                        <p className="text-xs text-muted-foreground">Live visualization from sandbox execution</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {activePlot && (
                        <>
                            <Button variant="outline" size="sm" className="gap-2">
                                <Download className="w-4 h-4" />
                                Export
                            </Button>
                            <Button variant="outline" size="sm" className="gap-2">
                                <Share2 className="w-4 h-4" />
                                Share
                            </Button>
                        </>
                    )}
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 md:p-8 custom-scrollbar">
                <div className="max-w-7xl mx-auto space-y-8">

                    <AnimatePresence mode="wait">
                        {!activePlot ? (
                            <motion.div
                                key="empty"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                className="flex flex-col items-center justify-center py-20 text-center space-y-6"
                            >
                                <div className="relative">
                                    <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full" />
                                    <div className="relative w-24 h-24 rounded-3xl bg-card border border-border shadow-2xl flex items-center justify-center">
                                        <Wand2 className="w-10 h-10 text-primary animate-pulse" />
                                    </div>
                                </div>
                                <div className="space-y-2 max-w-md">
                                    <h2 className="text-2xl font-bold tracking-tight">No Active Visualizations</h2>
                                    <p className="text-muted-foreground text-sm leading-relaxed">
                                        Ask the AI Assistant to create a plot, then click <strong>"Send to Sandbox"</strong> and execute the code to see your insights here.
                                    </p>
                                </div>
                                <Button variant="default" className="gap-2 shadow-lg shadow-primary/20" onClick={() => window.location.href = '/'}>
                                    <Sparkles className="w-4 h-4" />
                                    Start Chatting
                                </Button>
                            </motion.div>
                        ) : (
                            <motion.div
                                key="viz"
                                initial={{ opacity: 0, scale: 0.98 }}
                                animate={{ opacity: 1, scale: 1 }}
                                className="space-y-6"
                            >
                                {/* Primary Visualization Card */}
                                <div className="bg-card border border-border rounded-3xl overflow-hidden shadow-2xl">
                                    <div className="p-4 border-b border-border bg-muted/30 flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Life Execution Output</span>
                                        </div>
                                        <Button variant="ghost" size="icon" className="h-8 w-8 rounded-lg">
                                            <Maximize2 className="w-4 h-4" />
                                        </Button>
                                    </div>
                                    <div className="p-8 flex items-center justify-center bg-white/5 min-h-[500px]">
                                        <img
                                            src={`data:image/png;base64,${activePlot}`}
                                            alt="Visualization"
                                            className="max-w-full h-auto rounded-lg shadow-lg"
                                        />
                                    </div>
                                    <div className="p-6 border-t border-border bg-muted/10">
                                        <div className="flex items-start gap-4">
                                            <div className="mt-1 w-8 h-8 rounded-lg bg-card border border-border flex items-center justify-center shrink-0">
                                                <Code2 className="w-4 h-4 text-primary" />
                                            </div>
                                            <div className="flex-1 space-y-1">
                                                <p className="text-sm font-medium">Generation Logic</p>
                                                <pre className="text-xs font-mono bg-background/50 p-4 rounded-xl border border-border overflow-x-auto text-muted-foreground line-clamp-5 hover:line-clamp-none transition-all duration-300">
                                                    {activePlotCode}
                                                </pre>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Grid for other stats or history */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    {visualizationQueries.slice(-3).reverse().map((q, i) => (
                                        <motion.div
                                            key={q.id}
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.1 }}
                                            className="bg-card border border-border p-5 rounded-2xl space-y-4 hover:shadow-lg transition-shadow cursor-pointer group"
                                            onClick={() => {
                                                // In a real app, we'd swap the active plot
                                                // for now just visual
                                            }}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="w-8 h-8 rounded-lg bg-secondary/50 flex items-center justify-center group-hover:bg-primary/10 transition-colors">
                                                    <BarChart3 className="w-4 h-4 text-muted-foreground group-hover:text-primary" />
                                                </div>
                                                <span className="text-[10px] text-muted-foreground font-medium uppercase">{format(new Date(q.createdAt), 'MMM d, h:mm a')}</span>
                                            </div>
                                            <div>
                                                <h4 className="text-sm font-semibold truncate group-hover:text-primary transition-colors">{q.prompt}</h4>
                                                <p className="text-[10px] text-muted-foreground mt-1">From Query #{q.number}</p>
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
};

export default Insights;
