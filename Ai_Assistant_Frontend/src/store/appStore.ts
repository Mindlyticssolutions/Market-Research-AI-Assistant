import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Types
export interface DataSource {
  id: string;
  name: string;
  type: 'csv' | 'excel' | 'json' | 'database' | 'api';
  connectedAt: Date;
  status: 'connected' | 'disconnected' | 'error';
}

export interface QueryArtifact {
  type: 'chart' | 'table' | 'kpi' | 'model';
  data: unknown;
  title?: string;
}

export interface Query {
  id: string;
  number: number;
  title: string;
  prompt: string;
  code: string;
  output: string;
  artifacts: QueryArtifact[];
  createdAt: Date;
  updatedAt: Date;
  status?: 'idle' | 'generating' | 'running' | 'success' | 'error';
  type?: 'code' | 'markdown';
}

export interface AIMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  code?: string;
  suggestions?: string[];
  plot?: string;
  executionLogs?: string[];
  timestamp: Date;
  isThinking?: boolean;
  wasAutoSynced?: boolean;
}

interface AppState {
  // Data Sources
  dataSources: DataSource[];
  isConnected: boolean;
  addDataSource: (source: Omit<DataSource, 'id' | 'connectedAt'>) => void;
  removeDataSource: (id: string) => void;

  queries: Query[];
  activeQueryId: string | null;
  addQuery: (title: string, prompt: string, code: string) => Query;
  updateQuery: (id: string, updates: Partial<Query>) => void;
  removeQuery: (id: string) => void;
  setActiveQuery: (id: string | null) => void;
  getActiveQuery: () => Query | null;

  // AI Assistant
  aiMessages: AIMessage[];
  addAIMessage: (role: 'user' | 'assistant', content: string, code?: string, suggestions?: string[], plot?: string) => string; // Return ID
  appendExecutionLog: (messageId: string, log: string) => void;
  updateAIMessage: (id: string, updates: Partial<AIMessage>) => void;
  clearAIMessages: () => void;

  // UI State
  isSidebarCollapsed: boolean;
  isAIPanelCollapsed: boolean;
  toggleSidebar: () => void;
  toggleAIPanel: () => void;
  aiScrollPosition: number;
  setAIScrollPosition: (position: number) => void;

  // Modal State
  activeArtifact: QueryArtifact | null;
  activeArtifactCode: string | null;
  setActiveArtifact: (artifact: QueryArtifact | null, code?: string) => void;

  // Plot State
  activePlot: string | null;
  activePlotCode: string | null;
  setActivePlot: (plot: string | null) => void;
  setActivePlotCode: (code: string | null) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Data Sources
      dataSources: [],
      isConnected: false,

      addDataSource: (source) => {
        const newSource: DataSource = {
          ...source,
          id: crypto.randomUUID(),
          connectedAt: new Date(),
        };
        set((state) => ({
          dataSources: [...state.dataSources, newSource],
          isConnected: true,
        }));
      },

      removeDataSource: (id) => {
        set((state) => {
          const newSources = state.dataSources.filter((s) => s.id !== id);
          return {
            dataSources: newSources,
            isConnected: newSources.length > 0,
          };
        });
      },

      // Queries - Demo workflow data
      queries: [
        {
          id: 'demo-query-1',
          number: 1,
          title: 'Sales Exploration',
          prompt: 'Load and explore the sales dataset',
          code: `import pandas as pd
import numpy as np

# Load the sales data
df = pd.read_csv('sales_data.csv')

# Display basic info
print("Dataset Shape:", df.shape)
print("\\nColumn Types:")
print(df.dtypes)
print("\\nFirst 5 rows:")
df.head()`,
          output: 'Dataset Shape: (1000, 8)\n\nColumn Types:\ndate          datetime64[ns]\nproduct       object\ncategory      object\nregion        object\nsales         float64\nquantity      int64\ncustomer_id   object\nprofit        float64\n\nFirst 5 rows:\n| date       | product    | category   | region | sales  | quantity | profit |\n|------------|------------|------------|--------|--------|----------|--------|\n| 2024-01-01 | Widget A   | Electronics| North  | 299.99 | 5        | 45.50  |\n| 2024-01-01 | Widget B   | Furniture  | South  | 549.00 | 2        | 82.35  |',
          artifacts: [],
          createdAt: new Date(Date.now() - 3600000),
          updatedAt: new Date(Date.now() - 3600000),
        },
        {
          id: 'demo-query-2',
          number: 2,
          title: 'Sales Trend Viz',
          prompt: 'Create a sales trend visualization',
          code: `import matplotlib.pyplot as plt
import seaborn as sns

# Group by month and calculate total sales
monthly_sales = df.groupby(df['date'].dt.to_period('M'))['sales'].sum()

# Create the visualization
plt.figure(figsize=(12, 6))
plt.plot(monthly_sales.index.astype(str), monthly_sales.values, marker='o', linewidth=2)
plt.title('Monthly Sales Trend', fontsize=14)
plt.xlabel('Month')
plt.ylabel('Total Sales ($)')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()`,
          output: 'Chart generated successfully.\nMonthly sales range: $45,230 - $78,450\nPeak month: November 2024',
          artifacts: [
            {
              type: 'chart' as const,
              title: 'Monthly Sales Trend',
              data: {
                type: 'line',
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                values: [45230, 48900, 52100, 49800, 55400, 58200, 62100, 65800, 68400, 72100, 78450, 75200],
              },
            },
          ],
          createdAt: new Date(Date.now() - 3000000),
          updatedAt: new Date(Date.now() - 3000000),
        },
        {
          id: 'demo-query-3',
          number: 3,
          title: 'Success Prediction',
          prompt: 'Predict the success of each sale',
          code: `from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Prepare features
X = df[['quantity', 'category_encoded', 'region_encoded', 'month']]
y = df['sales']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Model Performance:")
print(f"  MSE: {mse:.2f}")
print(f"  R² Score: {r2:.4f}")
print(f"\\nFeature Importance:")
for feat, imp in zip(X.columns, model.feature_importances_):
    print(f"  {feat}: {imp:.4f}")`,
          output: 'Model Performance:\n  MSE: 1245.67\n  R² Score: 0.8934\n\nFeature Importance:\n  quantity: 0.4521\n  category_encoded: 0.2134\n  region_encoded: 0.1876\n  month: 0.1469',
          artifacts: [
            {
              type: 'model' as const,
              title: 'Sales Prediction Model',
              data: {
                algorithm: 'Random Forest Regressor',
                r2_score: 0.8934,
                mse: 1245.67,
              },
            },
          ],
          createdAt: new Date(Date.now() - 2400000),
          updatedAt: new Date(Date.now() - 2400000),
        },
      ],
      activeQueryId: 'demo-query-1',

      addQuery: (title, prompt, code) => {
        const newQuery: Query = {
          id: crypto.randomUUID(),
          number: get().queries.length + 1,
          title,
          prompt,
          code,
          output: '',
          artifacts: [],
          createdAt: new Date(),
          updatedAt: new Date(),
        };
        set((state) => ({
          queries: [...state.queries, newQuery],
          activeQueryId: newQuery.id,
        }));
        return newQuery;
      },

      updateQuery: (id, updates) => {
        set((state) => ({
          queries: state.queries.map((q) =>
            q.id === id ? { ...q, ...updates, updatedAt: new Date() } : q
          ),
        }));
      },

      removeQuery: (id) => {
        set((state) => {
          const newQueries = state.queries
            .filter((q) => q.id !== id)
            .map((q, index) => ({ ...q, number: index + 1 }));

          return {
            queries: newQueries,
            activeQueryId: state.activeQueryId === id ? null : state.activeQueryId,
          };
        });
      },

      setActiveQuery: (id) => set({ activeQueryId: id }),

      getActiveQuery: () => {
        const state = get();
        return state.queries.find((q) => q.id === state.activeQueryId) || null;
      },

      // AI Assistant
      aiMessages: [],

      addAIMessage: (role, content, code, suggestions, plot) => {
        const id = crypto.randomUUID();
        const newMessage: AIMessage = {
          id,
          role,
          content,
          code,
          suggestions,
          plot,
          timestamp: new Date(),
          executionLogs: [],
          isThinking: role === 'assistant'
        };
        set((state) => ({
          aiMessages: [...state.aiMessages, newMessage],
        }));
        return id;
      },

      appendExecutionLog: (messageId, log) => {
        set((state) => ({
          aiMessages: state.aiMessages.map((msg) =>
            msg.id === messageId
              ? { ...msg, executionLogs: [...(msg.executionLogs || []), log] }
              : msg
          ),
        }));
      },

      updateAIMessage: (id, updates) => {
        set((state) => ({
          aiMessages: state.aiMessages.map((msg) =>
            msg.id === id ? { ...msg, ...updates } : msg
          ),
        }));
      },

      clearAIMessages: () => set({ aiMessages: [] }),

      // UI State
      isSidebarCollapsed: false,
      isAIPanelCollapsed: false,

      toggleSidebar: () =>
        set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),

      toggleAIPanel: () =>
        set((state) => ({ isAIPanelCollapsed: !state.isAIPanelCollapsed })),

      aiScrollPosition: 0,
      setAIScrollPosition: (position) => set({ aiScrollPosition: position }),


      // Modal State
      activeArtifact: null,
      activeArtifactCode: null,

      setActiveArtifact: (artifact, code) =>
        set({ activeArtifact: artifact, activeArtifactCode: code || null }),

      // Plot State
      activePlot: null,
      activePlotCode: null,
      setActivePlot: (plot) => set({ activePlot: plot }),
      setActivePlotCode: (code) => set({ activePlotCode: code }),
    }),
    {
      name: 'analytix-storage',
      partialize: (state) => ({
        dataSources: state.dataSources,
        queries: state.queries,
        aiMessages: state.aiMessages,
        isConnected: state.isConnected,
        aiScrollPosition: state.aiScrollPosition,
        activePlot: state.activePlot,
      }),
    }
  )
);
