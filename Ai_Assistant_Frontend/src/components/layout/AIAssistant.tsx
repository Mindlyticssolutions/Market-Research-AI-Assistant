import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Code, ChevronRight, ChevronLeft, Copy, Check, ArrowDown, TrendingUp } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

export function AIAssistant() {
  const navigate = useNavigate();
  // Use selectors to prevent re-renders when other parts of the store change (like aiScrollPosition)
  const aiMessages = useAppStore(state => state.aiMessages);
  const addAIMessage = useAppStore(state => state.addAIMessage);
  const addQuery = useAppStore(state => state.addQuery);
  const isAIPanelCollapsed = useAppStore(state => state.isAIPanelCollapsed);
  const toggleAIPanel = useAppStore(state => state.toggleAIPanel);
  const setAIScrollPosition = useAppStore(state => state.setAIScrollPosition);
  const setActivePlotCode = useAppStore(state => state.setActivePlotCode);
  const setActivePlot = useAppStore(state => state.setActivePlot);

  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

  useEffect(() => {
    if (shouldAutoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [aiMessages, shouldAutoScroll]);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (container) {
      const handleScroll = () => {
        const { scrollTop, scrollHeight, clientHeight } = container;
        setAIScrollPosition(scrollTop); // Save position

        const isNearBottom = scrollHeight - Math.ceil(scrollTop) - clientHeight < 250; // Increased threshold
        setShouldAutoScroll(isNearBottom);
      };

      container.addEventListener('scroll', handleScroll);

      // Restore scroll position with a slight delay to ensure layout is ready
      setTimeout(() => {
        const savedPosition = useAppStore.getState().aiScrollPosition;
        if (savedPosition > 0) {
          container.scrollTop = savedPosition;
        }
        // Check initial button visibility after restoration
        handleScroll();
      }, 0);

      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, []);





  const updateAIMessage = useAppStore(state => state.updateAIMessage);
  const appendExecutionLog = useAppStore(state => state.appendExecutionLog);

  const handleSend = async (text?: string) => {
    const userInput = text || input;
    if (!userInput.trim()) return;

    // 1. Add User Message
    addAIMessage('user', userInput);
    setInput('');
    const textarea = document.querySelector('textarea');
    if (textarea) textarea.style.height = 'auto';
    setIsTyping(true);
    setShouldAutoScroll(true);

    setActivePlot(null);
    setActivePlotCode(null);

    try {
      // 2. Add empty Assistant Message (placeholder)
      // We pass empty content. The store will init logs.
      const messageId = addAIMessage('assistant', '');

      // 3. Import chat service for URL
      const { chatService } = await import('@/services/chatService');
      const wsUrl = chatService.getStreamUrl();

      // 4. Connect WebSocket
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({
          message: userInput,
          agent: 'orchestrator' // Default agent
        }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'status') {
          // e.g. "processing"
        } else if (data.type === 'thinking') {
          appendExecutionLog(messageId, data.content);
        } else if (data.type === 'code_execution') {
          appendExecutionLog(messageId, data.content);

          // Sync with Sandbox
          let codeToSync = data.content;
          // Extract code if wrapped in markdown
          if (codeToSync.includes('```')) {
            const match = codeToSync.match(/```(?:\w+)?\n?([\s\S]*?)```/);
            if (match) codeToSync = match[1].trim();
          }
          // Also strip "Running python code:\n" prefix if present from the log message
          if (codeToSync.startsWith("Running python code:\n")) {
            codeToSync = codeToSync.replace("Running python code:\n", "");
          } else if (codeToSync.startsWith("Running")) {
            // Try to find the code part
            const parts = codeToSync.split(":\n");
            if (parts.length > 1) {
              codeToSync = parts.slice(1).join(":\n");
            }
          }

          // Update Sandbox Store
          addQuery("AI Generated execution", codeToSync);
          navigate('/sandbox');

        } else if (data.type === 'observation') {
          appendExecutionLog(messageId, data.content);
        } else if (data.type === 'response') {
          // Final response
          let fullResponse = data.content;
          let suggestions: string[] = [];
          let code: string | undefined;
          let plot: string | undefined = data.plot;

          // Parse code/suggestions (reuse existing logic)
          if (fullResponse.includes('```')) {
            const codeMatch = fullResponse.match(/```(?:\w+)?\n?([\s\S]*?)```/);
            code = codeMatch ? codeMatch[1].trim() : undefined;
            if (code) {
              fullResponse = fullResponse.replace(/```(?:\w+)?\n?[\s\S]*?```/g, '').trim();
            }
          }

          const suggestionMatch = fullResponse.match(/(?:^|\n)(?:Suggestions|Suggested Next Steps):([\s\S]*)$/i);
          if (suggestionMatch) {
            const suggestionText = suggestionMatch[1];
            suggestions = suggestionText.split('\n').map(l => l.trim()).filter(l => l.startsWith('-') || l.startsWith('•')).map(l => l.substring(1).trim());
            fullResponse = fullResponse.substring(0, suggestionMatch.index).trim();
          }

          updateAIMessage(messageId, {
            content: fullResponse,
            code,
            suggestions: suggestions.length > 0 ? suggestions : undefined,
            plot,
            isThinking: false
          });

          if (plot) {
            const setActivePlot = useAppStore.getState().setActivePlot;
            setActivePlot(plot);
            if (code) setActivePlotCode(code);
          }

          setIsTyping(false);
          ws.close();
        } else if (data.type === 'error') {
          updateAIMessage(messageId, {
            content: `Error: ${data.message}`,
            isThinking: false
          });
          setIsTyping(false);
          ws.close();
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        updateAIMessage(messageId, {
          content: "Connection error. Please ensure backend is running.",
          isThinking: false
        });
        setIsTyping(false);
      };

    } catch (error) {
      console.error("Setup error:", error);
      setIsTyping(false);
    }
  };

  const handleSendToSandbox = (code: string, prompt: string) => {
    addQuery(prompt, code);
    navigate('/sandbox');
  };

  const handleCopyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (isAIPanelCollapsed) {
    return (
      <motion.div
        initial={{ width: 48 }}
        animate={{ width: 48 }}
        className="h-screen bg-card border-l border-border flex flex-col items-center py-4 shrink-0"
      >
        <button
          onClick={toggleAIPanel}
          className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center hover:bg-primary/20 transition-colors"
        >
          <Sparkles className="w-5 h-5 text-primary" />
        </button>

      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ width: 380 }}
      animate={{ width: 380 }}
      className="h-screen bg-card border-l border-border flex flex-col shrink-0 relative"
    >
      {/* Header */}
      <div className="h-14 flex items-center justify-between px-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-primary" />
          </div>
          <span className="font-medium text-foreground">AI Assistant</span>
        </div>
        <button
          onClick={toggleAIPanel}
          className="p-2 text-muted-foreground hover:text-foreground rounded-lg hover:bg-muted transition-colors"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Messages */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
      >
        {aiMessages.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-8 h-8 text-primary" />
            </div>
            <h3 className="font-medium text-foreground mb-2">AI-Powered Analysis</h3>
            <p className="text-sm text-muted-foreground max-w-[280px] mx-auto">
              Ask me to analyze data, create visualizations, or build analytical models.
            </p>
          </div>
        )}

        <AnimatePresence mode="popLayout">
          {aiMessages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={cn(
                'flex flex-col', // Changed to column to stack suggestions
                message.role === 'user' ? 'items-end' : 'items-start'
              )}
            >
              <div
                className={cn(
                  'max-w-[90%] rounded-xl px-4 py-3',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground'
                )}
              >
                {/* Thinking Process */}
                {(message.executionLogs && message.executionLogs.length > 0) && (
                  <div className="mb-3 rounded-lg border border-border/50 bg-background/50 overflow-hidden">
                    <button
                      className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-muted/50 transition-colors"
                      onClick={(e) => {
                        const logs = e.currentTarget.nextElementSibling;
                        logs?.classList.toggle('hidden');
                        e.currentTarget.querySelector('svg')?.classList.toggle('rotate-180');
                      }}
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      Thinking Process ({message.executionLogs.length} steps)
                      <ChevronRight className="w-3.5 h-3.5 ml-auto transition-transform" />
                    </button>
                    <div className="hidden border-t border-border/50 bg-editor-bg p-3 space-y-2">
                      {message.executionLogs.map((log, i) => (
                        <div key={i} className="flex gap-2 text-xs font-mono text-muted-foreground/80">
                          <span className="opacity-50 select-none">{(i + 1).toString().padStart(2, '0')}</span>
                          <span className="whitespace-pre-wrap font-mono">{log}</span>
                        </div>
                      ))}
                      {message.isThinking && (
                        <div className="flex gap-2 text-xs text-primary animate-pulse">
                          <span className="opacity-50">..</span>
                          <span>Thinking...</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <p className="text-sm whitespace-pre-wrap">{message.content || (message.isThinking ? '' : 'No content')}</p>

                {message.code && (
                  <div className="mt-3 rounded-lg overflow-hidden border border-border/50">
                    <div className="flex items-center justify-between px-3 py-2 bg-editor-bg border-b border-border/50">
                      <div className="flex items-center gap-2">
                        <Code className="w-3.5 h-3.5 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">Code</span>
                      </div>
                      <button
                        onClick={() => handleCopyCode(message.code!, message.id)}
                        className="p-1 hover:bg-muted rounded transition-colors"
                      >
                        {copiedId === message.id ? (
                          <Check className="w-3.5 h-3.5 text-success" />
                        ) : (
                          <Copy className="w-3.5 h-3.5 text-muted-foreground" />
                        )}
                      </button>
                    </div>
                    <pre className="p-3 text-xs font-mono bg-editor-bg text-foreground overflow-x-auto">
                      {message.code}
                    </pre>
                    <div className="px-3 py-2 bg-editor-bg border-t border-border/50 flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => handleSendToSandbox(message.code!, message.content)}
                        className="flex-1 gap-2"
                      >
                        <Send className="w-3.5 h-3.5" />
                        Send to Sandbox
                      </Button>
                    </div>
                  </div>
                )}
              </div>

              {/* Suggestions Chips */}
              {message.suggestions && message.suggestions.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2 max-w-[90%] pl-1">
                  {message.suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSend(suggestion)}
                      className="text-xs bg-background border border-border hover:border-primary/50 hover:bg-muted text-muted-foreground hover:text-foreground px-3 py-1.5 rounded-full transition-colors text-left"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="bg-muted rounded-xl px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-muted-foreground animate-pulse" />
                <span className="w-2 h-2 rounded-full bg-muted-foreground animate-pulse" style={{ animationDelay: '0.2s' }} />
                <span className="w-2 h-2 rounded-full bg-muted-foreground animate-pulse" style={{ animationDelay: '0.4s' }} />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />

      </div>



      {/* Input */}
      <div className="p-4 border-t border-border">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              // Auto-resize
              e.target.style.height = 'auto';
              e.target.style.height = `${e.target.scrollHeight}px`;
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask me anything..."
            className="flex-1 min-h-[40px] max-h-[150px] bg-muted rounded-lg px-4 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none overflow-y-auto [&::-webkit-scrollbar]:hidden [scrollbar-width:none]"
            rows={1}
          />
          <Button
            size="icon"
            onClick={() => handleSend()}
            disabled={!input.trim()}
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

function generateSampleCode(prompt: string): string {
  if (prompt.toLowerCase().includes('chart') || prompt.toLowerCase().includes('plot')) {
    return `import pandas as pd
import matplotlib.pyplot as plt

# Load and prepare data
df = pd.read_csv('data.csv')

# Create visualization
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df['x'], df['y'], color='#22d3ee', linewidth=2)
ax.set_xlabel('X Axis')
ax.set_ylabel('Y Axis')
ax.set_title('Data Visualization')
plt.tight_layout()
plt.show()`;
  }

  if (prompt.toLowerCase().includes('model')) {
    return `from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# Prepare data
X = df.drop('target', axis=1)
y = df['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train model
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Evaluate
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"Model Accuracy: {accuracy:.2%}")`;
  }

  return `import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('data.csv')

# Perform analysis
summary = df.describe()
correlations = df.corr()

print("Data Summary:")
print(summary)
print("\\nCorrelations:")
print(correlations)`;
}
