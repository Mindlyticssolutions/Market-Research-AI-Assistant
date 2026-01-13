# Analytix - AI-Powered Data Analysis Platform

An intelligent data analysis platform that combines RAG/KAG retrieval with agentic code execution in a Databricks sandbox environment. The platform enables natural language interactions for data exploration, analysis, and visualization.

## 🎯 Key Features

- **🤖 Multi-Agent System**: Orchestrator routes queries to specialized agents (Python, SQL, Researcher, Analyst, Writer)
- **💬 Natural Language Interface**: Chat-based interaction with AI-powered query understanding
- **📊 Code Interpreter**: Execute Python/SQL code in Databricks sandbox with automatic error handling
- **📝 Smart Routing**: Automatically distinguishes between "write code" (text-only) and "run code" (execution) requests
- **🔍 RAG/KAG Retrieval**: Hybrid search using Azure AI Search (documents) and Cosmos DB Gremlin (knowledge graph)
- **📁 File Upload**: Support for CSV, Excel, PDF, Word, PowerPoint, and text files
- **📓 Continuous Notebook**: Databricks-integrated notebook with query history tracking
- **🎨 Modern UI**: React + TypeScript frontend with dark mode and responsive design

---

## 📁 Project Structure & File Responsibilities

### Directory Tree Overview

```
AI-Assistant/
├── Ai_Assistant_Frontend/       # React + TypeScript Frontend
│   ├── src/
│   │   ├── components/          # UI Components
│   │   │   ├── layout/          # AIAssistant, Sidebar, Navbar
│   │   │   ├── sandbox/         # Code editor, Notebook, QueryWorkflow
│   │   │   └── ui/              # Reusable UI components (shadcn/ui)
│   │   ├── pages/               # Route pages (Home, Sandbox, Insights)
│   │   ├── services/            # API services (chat, file, databricks)
│   │   ├── store/               # Zustand state management
│   │   └── lib/                 # Utilities
│   ├── package.json             # Frontend dependencies
│   └── vite.config.ts           # Vite configuration with proxy
│
├── backend/                     # FastAPI Backend
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── api/v1/endpoints/    # API endpoints
│   │   │   ├── chat.py          # Chat & WebSocket endpoints
│   │   │   ├── databricks.py    # Databricks code execution
│   │   │   └── files.py         # File upload & management
│   │   ├── core/                # Core services
│   │   │   ├── azure_client.py  # Azure AI Foundry client
│   │   │   └── data_access.py   # Data access layer
│   │   ├── rag/                 # RAG (Retrieval-Augmented Generation)
│   │   │   ├── indexer.py       # Document indexing
│   │   │   └── retriever.py     # Azure AI Search integration
│   │   └── kag/                 # KAG (Knowledge-Augmented Generation)
│   │       └── graph_retriever.py # Cosmos DB Gremlin integration
│   ├── requirements.txt         # Python dependencies
│   └── .env                     # Environment configuration
│
├── agents/                      # Agent System
│   ├── base/
│   │   └── agent.py             # BaseAgent with ReAct loop
│   ├── orchestrator/
│   │   └── agent.py             # Routes queries to specialized agents
│   ├── python_agent/
│   │   └── agent.py             # Python code generation & execution
│   ├── sql_agent/
│   │   └── agent.py             # SQL query generation
│   ├── researcher_agent/
│   │   └── agent.py             # Document search & retrieval
│   ├── analyst_agent/
│   │   └── agent.py             # Business insights & analysis
│   ├── writer_agent/
│   │   └── agent.py             # Report generation
│   ├── registry.py              # Agent registration & discovery
│   └── AGENT_ARCHITECTURE.md    # Agent system documentation
│
└── tests/                       # Test files
    └── verify_agent.py          # Agent verification tests
```

---

### Detailed File Responsibilities

### Frontend (`Ai_Assistant_Frontend/`)

#### Core Application Files
- **`src/main.tsx`**
  - Application entry point
  - Initializes React Router and renders root component
  - Wraps app with theme provider and query client

- **`src/App.tsx`**
  - Main application component
  - Defines route structure (Home, Sandbox, Insights)
  - Manages layout and navigation

- **`vite.config.ts`**
  - **Critical**: Configures Vite dev server with proxy
  - Forwards `/api/*` requests to backend (`:8000`)
  - Enables hot module replacement (HMR)

- **`package.json`**
  - Lists all npm dependencies (React, TypeScript, TailwindCSS, etc.)
  - Defines scripts: `dev`, `build`, `preview`

---

#### Components (`src/components/`)

**Layout Components** (`layout/`)
- **`AIAssistant.tsx`**
  - **Purpose**: Collapsible right-side chat panel
  - **What it does**:
    - Connects to backend via WebSocket (`chatService.getStreamUrl()`)
    - Displays streaming AI responses (thinking, code execution, observations)
    - Sends code to Sandbox when AI executes it
    - Manages chat history and message state
  - **Key Features**:
    - Auto-scroll during streaming
    - "Send to Sandbox" button for manual code transfer
    - Suggestion chips for follow-up questions

- **`Sidebar.tsx`**
  - Navigation menu (Home, Sandbox, Insights)
  - File upload button
  - Databricks connection status indicator

- **`Navbar.tsx`**
  - Top navigation bar
  - Theme toggle (dark/light mode)
  - User profile menu

**Sandbox Components** (`sandbox/`)
- **`NotebookCell.tsx`**
  - **Purpose**: Displays a single code cell in the Databricks notebook
  - **What it does**:
    - Shows query title, prompt, code, and output
    - Highlights active cell on click (from Query Workflow)
    - Displays execution status (pending, running, success, error)
  - **Data Source**: Reads from `useAppStore((state) => state.queries)`

- **`QueryWorkflow.tsx`**
  - **Purpose**: Left sidebar showing execution history
  - **What it does**:
    - Lists all executed queries chronologically
    - Click to scroll notebook to corresponding cell
    - Status indicators (⏳ pending, ▶ running, ✓ success, ✗ error)

- **`CodeEditor.tsx`**
  - Monaco Editor wrapper for manual code entry
  - Syntax highlighting for Python
  - Execute button to run code in Databricks

**UI Components** (`ui/`)
- Reusable components from **shadcn/ui** library
- Examples: `Button`, `Card`, `Dialog`, `Input`, `Textarea`
- Pre-styled with TailwindCSS

---

#### Services (`src/services/`)

- **`chatService.ts`**
  - **Purpose**: API client for chat endpoints
  - **Functions**:
    - `sendMessage()` - POST to `/api/v1/chat/send` (REST)
    - `getStreamUrl()` - Returns WebSocket URL
    - `getHistory()`, `clearHistory()` - Session management

- **`fileService.ts`**
  - **Purpose**: Handle file uploads
  - **Functions**:
    - `uploadFile()` - POST to `/api/v1/files/upload` (multipart/form-data)
    - `listFiles()` - GET uploaded files with status
    - `deleteFile()` - Remove file from Azure

- **`databricksService.ts`**
  - **Purpose**: Execute code in Databricks sandbox
  - **Functions**:
    - `executeCode()` - POST to `/api/v1/databricks/execute`
    - `getClusters()` - List available Databricks clusters

---

#### State Management (`src/store/`)

- **`appStore.ts`**
  - **Purpose**: Zustand global state store
  - **State**:
    - `aiMessages` - Chat history
    - `queries` - Sandbox notebook cells
    - `activePlot` - Current visualization
    - `isAIPanelCollapsed` - UI state
  - **Actions**:
    - `addAIMessage()` - Add message to chat
    - `addQuery()` - Add notebook cell
    - `updateQuery()` - Update cell status/output
    - `setActivePlot()` - Display plot on Insights page

---

### Backend (`backend/app/`)

#### Application Core

- **`main.py`**
  - **Purpose**: FastAPI application entry point
  - **What it does**:
    - Creates FastAPI app with CORS middleware
    - Initializes Agent Registry on startup
    - Includes API routers with `/api/v1` prefix
    - Defines root and health check endpoints
  - **Startup Flow**:
    1. Loads environment variables from `.env`
    2. Imports `AgentRegistry.initialize()` to load all agents
    3. Starts uvicorn server

---

#### API Endpoints (`app/api/v1/endpoints/`)

- **`chat.py`**
  - **Purpose**: Handle AI chat interactions
  - **Endpoints**:
    - `POST /send` - Send message, get response (REST)
    - `WS /ws/{session_id}` - Real-time chat with streaming
    - `GET /history/{session_id}` - Retrieve conversation
    - `DELETE /history/{session_id}` - Clear history
  - **Key Function**: `_execute_agent()`
    - Calls `AgentRegistry.get_agent("orchestrator")`
    - Passes conversation history and context
    - Returns response with optional sources and plots

- **`files.py`**
  - **Purpose**: File upload and RAG/KAG indexing
  - **Endpoints**:
    - `POST /upload` - Upload file to Azure Blob
    - `GET /list` - List all uploaded files
    - `GET /{file_id}` - Get file metadata
    - `GET /{file_id}/status` - Check indexing status
    - `DELETE /{file_id}` - Delete file
  - **Background Processing**:
    - `_upload_to_blob()` - Saves to Azure Blob Storage
    - `_extract_text_content()` - Extracts text from PDF, DOCX, XLSX
    - `_process_and_index_file()` - Background task that:
      1. Chunks text (1000 chars)
      2. Calls `RAGIndexer.index_document()`
      3. Updates file status to `indexed`

- **`databricks.py`**
  - **Purpose**: Execute code in Databricks sandbox
  - **Endpoints**:
    - `POST /execute` - Run Python/SQL code
    - `GET /clusters` - List Databricks clusters
  - **Security**: Code execution isolated in Databricks context

- **`router.py`**
  - **Purpose**: Combines all endpoint routers
  - **What it does**: Includes routers with prefixes and tags

---

#### Core Services (`app/core/`)

- **`config.py`**
  - **Purpose**: Environment configuration with Pydantic
  - **What it does**:
    - Loads variables from `.env` file
    - Validates required Azure credentials
    - Provides typed settings object (`settings`)
  - **Critical Variables**:
    - `AZURE_OPENAI_*` - LLM connection
    - `AZURE_SEARCH_*` - RAG index
    - `AZURE_STORAGE_*` - File storage
    - `DATABRICKS_*` - Code execution

- **`azure_client.py`**
  - **Purpose**: Azure AI Foundry SDK client
  - **What it does**: Creates authenticated clients for Azure services

- **`data_access.py`**
  - Database connection and query execution
  - (Currently minimal, designed for future SQL integration)

---

#### RAG System (`app/rag/`)

- **`indexer.py`**
  - **Purpose**: Index documents into Azure AI Search
  - **Class**: `RAGIndexer`
  - **Key Method**: `index_document(file_id, content, title, source)`
    - Chunks content with `RecursiveCharacterTextSplitter`
    - Generates embeddings via `AzureOpenAIEmbeddings`
    - Stores vectors in `AzureSearch` (LangChain integration)
  - **Returns**: `{"success": True, "chunks_indexed": 15}`

- **`retriever.py`**
  - **Purpose**: Retrieve relevant documents from Azure AI Search
  - **Class**: `RAGRetriever`
  - **Key Method**: `retrieve(query, top_k=5)`
    - Converts query to embedding
    - Performs vector similarity search
    - Returns top-k matching document chunks

---

#### KAG System (`app/kag/`)

- **`graph_retriever.py`**
  - **Purpose**: Knowledge graph retrieval from Cosmos DB Gremlin
  - **Class**: `KAGRetriever`
  - **What it does**:
    - Connects to Cosmos DB Gremlin API
    - Extracts entities and relationships from documents
    - Stores as graph (nodes = entities, edges = relationships)
    - Query graph for contextual knowledge
  - **Example**: "Apple competes with Microsoft" → Graph: `Apple --[competes_with]--> Microsoft`

---

### Agent System (`agents/`)

#### Base Agent

- **`agents/base/agent.py`**
  - **Purpose**: Base class for all agents with ReAct loop
  - **Class**: `BaseAgent`
  - **Key Features**:
    - **ReAct Loop**: Reasoning → Action → Observation (iterates until done)
    - **Tool Calling**: Agents can call tools (e.g., `execute_databricks_code`)
    - **Error Handling**: Automatic retry on failures
    - **Streaming**: Callbacks for live updates
  - **Abstract Methods**:
    - `_get_system_prompt()` - Agent's instructions
    - `_get_tools()` - Available tools
  - **Execution Flow**:
    1. Agent receives query
    2. Calls Azure OpenAI with tools
    3. If tool call → Execute tool → Feed result back
    4. Repeat until final answer

---

#### Specialized Agents

- **`agents/orchestrator/agent.py`**
  - **Purpose**: Routes user queries to appropriate specialized agents
  - **Tool**: `route_to_agent(agent_name, query)`
  - **Routing Logic**: Keyword matching
    - "code", "python" → Python Agent
    - "sql", "query" → SQL Agent
    - "search", "find" → Researcher Agent
  - **Smart Prefixes**:
    - "EXECUTE: ..." → Run code
    - "TEXT ONLY: ..." → Just show code

- **`agents/python_agent/agent.py`**
  - **Purpose**: Generate and execute Python code
  - **Tool**: `execute_databricks_code(code)`
  - **What it does**:
    1. Writes Python code
    2. Calls `/api/v1/databricks/execute`
    3. Observes results
    4. Self-corrects if errors occur
  - **ReAct Example**:
    - Thought: "I'll calculate Fibonacci"
    - Action: `execute_databricks_code("def fib(n): ...")`
    - Observation: "Result: 55"
    - Answer: "The 10th Fibonacci number is 55"

- **`agents/sql_agent/agent.py`**
  - **Purpose**: Generate SQL queries from natural language
  - **Metadata Only**: Works with schema (table/column names), not actual data
  - **Tool**: `generate_sql(question)`
  - **Example**:
    - Input: "Find top customers"
    - Output: `SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id`

- **`agents/researcher_agent/agent.py`**
  - **Purpose**: Search documents via RAG/KAG
  - **Tool**: `search_documents(query)`
  - **What it does**:
    - Calls `RAGRetriever.retrieve(query)`
    - Returns relevant document chunks
    - Metadata only (titles, filenames, not full content)

- **`agents/analyst_agent/agent.py`**
  - **Purpose**: Provide business insights and recommendations
  - **Tool**: `analyze_trends(topic)`
  - **Use Case**: High-level analysis, not code execution

- **`agents/writer_agent/agent.py`**
  - **Purpose**: Generate reports and summaries
  - **Tool**: `write_report(topic)`
  - **Use Case**: Long-form content generation

---

#### Agent Registry

- **`agents/registry.py`**
  - **Purpose**: Central registry for all agents (Singleton pattern)
  - **What it does**:
    - Loads all agents into memory on startup
    - Provides `get_agent(name)` for fast lookup
    - Prevents re-initialization
  - **Registered Agents**: orchestrator, python, sql, researcher, analyst, writer

---

### Configuration Files

- **`backend/.env`**
  - Environment variables (Azure credentials, API keys)
  - **Critical**: Never commit to Git (use `.env.example`)

- **`backend/.env.example`**
  - Template for `.env` with placeholder values
  - Safe to commit to version control

- **`backend/requirements.txt`**
  - Python dependencies (FastAPI, Azure SDKs, LangChain, etc.)
  - Install with `pip install -r requirements.txt`

- **`Ai_Assistant_Frontend/package.json`**
  - npm dependencies (React, TypeScript, Vite, TailwindCSS)
  - Install with `npm install`

---

### Testing Files

- **`tests/verify_agent.py`**
  - Test script to verify agent functionality
  - Sends sample queries to each agent
  - Checks for successful responses

- **`backend/test_ws_connection.py`**
  - WebSocket connection test
  - Verifies real-time streaming works

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** (v18+)
- **Python** (3.10+)
- **Azure Account** with:
  - Azure AI Foundry
  - Azure AI Search
  - Azure Blob Storage
  - Azure Cosmos DB (Gremlin API)
  - Databricks Workspace (for code execution)

### Installation

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd AI-Assistant
```

#### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Copy .env.example to .env and fill in your Azure credentials
cp .env.example .env
```

**Required Environment Variables** (`.env`):
```env
# Azure AI Foundry
AZURE_AI_PROJECT_CONNECTION_STRING=<your-connection-string>

# Azure AI Search (RAG)
AZURE_SEARCH_ENDPOINT=<your-search-endpoint>
AZURE_SEARCH_KEY=<your-search-key>
AZURE_SEARCH_INDEX_NAME=<your-index-name>

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=<your-storage-connection>
AZURE_STORAGE_CONTAINER=<your-container-name>

# Azure Cosmos DB (KAG - Gremlin)
COSMOS_GREMLIN_ENDPOINT=<your-gremlin-endpoint>
COSMOS_GREMLIN_KEY=<your-gremlin-key>
COSMOS_DATABASE_NAME=<your-database-name>
COSMOS_GRAPH_NAME=<your-graph-name>

# Databricks
DATABRICKS_HOST=<your-databricks-host>
DATABRICKS_TOKEN=<your-databricks-token>
DATABRICKS_CLUSTER_ID=<your-cluster-id>
```

#### 3. Frontend Setup

```bash
# Navigate to frontend
cd ../Ai_Assistant_Frontend

# Install dependencies
npm install
```

---

## ▶️ Running the Application

### Development Mode

#### Terminal 1: Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on: `http://localhost:8000`

#### Terminal 2: Start Frontend
```bash
cd Ai_Assistant_Frontend
npm run dev
```

Frontend will run on: `http://localhost:8080`

### Building for Production

#### Backend
```bash
cd backend
# Backend runs with uvicorn, no build step needed
```

#### Frontend
```bash
cd Ai_Assistant_Frontend
npm run build
```

Built files will be in `Ai_Assistant_Frontend/dist/`

---

## 📖 How to Use

### 1. Upload Files
- Navigate to the **Home** page
- Click "Upload" or drag-and-drop files
- Supported formats: CSV, Excel, PDF, Word, PowerPoint, TXT, MD
- Files are indexed automatically for RAG/KAG retrieval

### 2. Chat with AI Assistant

The AI Assistant understands two types of requests:

#### **"Write Code" (Text Only)**
When you ask the AI to **write**, **show**, or **provide** code:
- ✅ AI returns code in chat interface
- ✅ "Send to Sandbox" button appears for manual execution
- ❌ NO automatic notebook cell creation
- ❌ NO automatic execution

**Examples:**
- "Write a python function to calculate Fibonacci numbers"
- "Show me code to analyze correlation in my dataset"
- "Provide an example of data visualization with matplotlib"

#### **"Write and Run Code" (Execution)**
When you ask the AI to **run**, **calculate**, **analyze**, or **plot**:
- ✅ AI writes code
- ✅ Code is automatically executed in Databricks sandbox
- ✅ Notebook cell is created in Query Workflow
- ✅ Results are displayed

**Examples:**
- "Calculate the 10th Fibonacci number using Python"
- "Analyze the correlation in sales_data.csv"
- "Plot a bar chart of revenue by region"

### 3. Sandbox Page
- View **Databricks Notebook** with all executed code
- **Query Workflow** sidebar shows execution history
- Click on queries to navigate to corresponding notebook cells
- Code editor for manual code entry and execution

### 4. Insights Page
- View AI-generated visualizations and plots
- Automatically displays charts from sandbox execution

---

## 🤖 Agent System

The platform uses a **multi-agent architecture** with intelligent routing:

### Agent Types

| Agent | Purpose | Triggers |
|-------|---------|----------|
| **Orchestrator** | Routes queries to appropriate agents | All user queries |
| **Python Agent** | Python code generation & execution | "code", "python", "analyze", "calculate" |
| **SQL Agent** | SQL query generation | "sql", "query", "database", "select" |
| **Researcher** | Document search via RAG/KAG | "search", "find", "what is" |
| **Analyst** | Business insights & recommendations | "analyze", "insight", "pattern" |
| **Writer** | Report generation & summarization | "write report", "summarize" |

### How Agents Work

1. **User sends a query** → Orchestrator Agent receives it
2. **Orchestrator analyzes intent** and routes to specialized agent
3. **Specialized agent executes** using ReAct loop (Reasoning + Acting)
4. **Agent retrieves context** from RAG (documents) and KAG (knowledge graph)
5. **Agent returns response** to user via WebSocket streaming

### Key Agent Features

- ✅ **ReAct Loop**: Agents think, act (use tools), and observe results iteratively
- ✅ **Tool Usage**: Agents can call `execute_databricks_code`, `route_to_agent`, etc.
- ✅ **Error Handling**: Automatic retry with self-correction
- ✅ **Context Awareness**: Access to conversation history and uploaded files

See [`agents/AGENT_ARCHITECTURE.md`](agents/AGENT_ARCHITECTURE.md) for detailed documentation.

---

## 🔧 API Architecture & Endpoints

### FastAPI Backend Overview

The backend is built with **FastAPI**, a modern Python web framework that provides:
- ✅ **Automatic API Documentation** (OpenAPI/Swagger at `/docs`)
- ✅ **Type Safety** with Pydantic models
- ✅ **Async/Await** support for high concurrency
- ✅ **WebSocket** support for real-time streaming
- ✅ **CORS** middleware for frontend communication

### How FastAPI Works in This Project

#### 1. **Application Initialization** (`backend/app/main.py`)

When the server starts:
1. Creates the FastAPI app instance with metadata
2. Initializes **Agent Registry** (loads all agents into memory)
3. Adds **CORS middleware** to allow frontend requests
4. Includes API routers with `/api/v1` prefix
5. Sets up **lifespan events** for startup/shutdown

```python
# Startup Process
app = FastAPI(
    title="Market Research Assistant",
    openapi_url="/api/v1/openapi.json"
)
→ Initializes Agent Registry
→ Configures CORS for frontend
→ Includes routers: chat, files, databricks
```

#### 2. **Request Flow**

**REST API Request:**
```
Frontend → Vite Proxy (:8080/api/*) 
        → FastAPI (:8000/api/v1/*)
        → Router (chat.py / files.py / databricks.py)
        → Pydantic Validation
        → Business Logic
        → Response
```

**WebSocket Request:**
```
Frontend WebSocket → FastAPI WebSocket Endpoint
                  → Agent Execution (with streaming callback)
                  → Events streamed back: thinking, code_execution, observation, response
                  → Connection closed
```

#### 3. **Modular Router Architecture**

The API uses a **modular routing system** (`backend/app/api/v1/router.py`):

```python
api_router
├── /health     → health.py    (System health checks)
├── /files      → files.py     (File upload & management)
├── /agents     → agents.py    (Direct agent interaction)
├── /chat       → chat.py      (AI chat & WebSocket)
└── /databricks → databricks.py (Code execution sandbox)
```

---

### Base URL: `http://localhost:8000`

### 📡 Chat API

#### `POST /api/v1/chat/send`
**Purpose:** Send a message to the AI and get a response (REST endpoint)

**Request:**
```json
{
  "message": "Calculate Fibonacci(10)",
  "agent": "orchestrator",
  "session_id": "uuid-optional",
  "context": {}
}
```

**Response:**
```json
{
  "session_id": "a1b2c3d4",
  "agent": "orchestrator",
  "response": "The 10th Fibonacci number is 55.",
  "timestamp": "2024-01-15T10:30:00Z",
  "sources": ["doc1.pdf", "doc2.csv"],
  "plot": "base64-image-data"
}
```

**Flow:**
1. Validates request with Pydantic model
2. Creates or retrieves session
3. Adds user message to session history
4. Executes agent with RAG/KAG context
5. Returns response with optional sources/plots

---

#### `WS /api/v1/chat/ws/{session_id}`
**Purpose:** Real-time chat with streaming responses (WebSocket endpoint)

**Connection:** `ws://localhost:8000/api/v1/chat/ws/{session_id}`

**Send Message:**
```json
{
  "message": "Plot sales data",
  "agent": "orchestrator"
}
```

**Streaming Events:**
```json
// Event 1: Status
{"type": "status", "status": "processing", "agent": "orchestrator"}

// Event 2: Thinking Process
{"type": "thinking", "content": "[Task: Plotting] Routing to Python Agent"}

// Event 3: Code Execution
{"type": "code_execution", "content": "import matplotlib..."}

// Event 4: Observation
{"type": "observation", "content": "Plot generated successfully"}

// Event 5: Final Response
{"type": "response", "content": "Here's your sales plot", "plot": "..."}
```

**Flow:**
1. Client connects via WebSocket
2. Sends JSON message
3. Backend executes agent with streaming callback
4. Agent streams intermediate events (thinking, code_execution, observation)
5. Final response sent and connection remains open for next message

---

#### `GET /api/v1/chat/history/{session_id}`
**Purpose:** Retrieve conversation history for a session

**Response:**
```json
{
  "session_id": "a1b2c3d4",
  "messages": [
    {"role": "user", "content": "Hello", "timestamp": "..."},
    {"role": "assistant", "content": "Hi!", "timestamp": "..."}
  ],
  "message_count": 2
}
```

---

#### `DELETE /api/v1/chat/history/{session_id}`
**Purpose:** Clear chat history for a session

**Response:**
```json
{"message": "Chat history cleared", "session_id": "a1b2c3d4"}
```

---

### 📁 File Upload API

#### `POST /api/v1/files/upload`
**Purpose:** Upload a file to Azure Blob Storage and trigger RAG/KAG indexing

**Request:** `multipart/form-data`
```
file: <binary-file-data>
```

**Response:**
```json
{
  "message": "File uploaded to Blob Storage, indexing started",
  "file_id": "uuid",
  "filename": "sales_data.csv",
  "status": "pending",
  "blob_url": "https://storage.blob.core.windows.net/..."
}
```

**Background Processing:**
1. File saved to Azure Blob Storage
2. Text extracted (PDF, DOCX, XLSX, etc.)
3. Content chunked (1000 chars per chunk)
4. Embeddings generated via Azure OpenAI
5. Vectors indexed in Azure AI Search
6. Entities/relationships extracted to Cosmos DB Gremlin (KAG)
7. Status updated to `indexed`

---

#### `GET /api/v1/files/list`
**Purpose:** List all uploaded files with their indexing status

**Response:**
```json
[
  {
    "id": "uuid-1",
    "filename": "sales_2023.csv",
    "file_type": "csv",
    "size": 245678,
    "uploaded_at": "2024-01-15T10:00:00Z",
    "status": "indexed",
    "blob_url": "https://...",
    "chunks_indexed": 15
  }
]
```

---

#### `GET /api/v1/files/{file_id}`
**Purpose:** Get detailed metadata for a specific file

**Response:**
```json
{
  "id": "uuid-1",
  "filename": "report.pdf",
  "file_type": "pdf",
  "size": 1024000,
  "uploaded_at": "2024-01-15T10:00:00Z",
  "status": "indexed",
  "blob_url": "https://...",
  "chunks_indexed": 42
}
```

---

#### `GET /api/v1/files/{file_id}/status`
**Purpose:** Check processing status of a file

**Response:**
```json
{
  "file_id": "uuid-1",
  "filename": "data.xlsx",
  "status": "processing",
  "chunks_indexed": null,
  "blob_url": "https://...",
  "message": "File is processing"
}
```

**Status Values:**
- `pending` - Uploaded, waiting for indexing
- `processing` - Currently being indexed
- `indexed` - Successfully indexed and ready
- `failed` - Indexing failed (check logs)

---

#### `DELETE /api/v1/files/{file_id}`
**Purpose:** Delete a file and remove from RAG index

**Response:**
```json
{"message": "File deleted successfully", "file_id": "uuid-1"}
```

---

### 🖥️ Databricks API

#### `POST /api/v1/databricks/execute`
**Purpose:** Execute Python/SQL code in Databricks sandbox

**Request:**
```json
{
  "code": "df = spark.read.csv('data.csv')\ndf.show()",
  "language": "python"
}
```

**Response:**
```json
{
  "status": "success",
  "output": "+-----+------+\n| Name| Sales|\n+-----+------+\n|Alice|  1000|\n...",
  "execution_time_ms": 1234,
  "error": null
}
```

**Flow:**
1. Code validated and sanitized
2. Sent to Databricks cluster via REST API
3. Executed in isolated context
4. Results captured and returned
5. Errors caught and formatted

---

#### `GET /api/v1/databricks/clusters`
**Purpose:** List available Databricks clusters

**Response:**
```json
{
  "clusters": [
    {
      "cluster_id": "0123-456789-abcdef",
      "cluster_name": "AI-Assistant-Cluster",
      "state": "RUNNING",
      "spark_version": "13.3.x-scala2.12"
    }
  ]
}
```

---

### 🔒 Authentication & Security

**Current Implementation:**
- No authentication required (development mode)
- CORS restricted to localhost origins
- File size limits enforced (50MB default)

**Production Recommendations:**
- Add API key authentication
- Implement rate limiting
- Use Azure AD for SSO
- Enable HTTPS/TLS
- Add request validation middleware

---

### 📊 API Documentation

**Interactive Docs:**
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/api/v1/openapi.json`

These provide:
- Interactive API testing
- Request/response schemas
- Authentication requirements
- Example payloads

---

## 🗂️ File Upload & Indexing

The platform implements a **hybrid RAG/KAG system** for document understanding:

### Upload Flow
1. User uploads file via frontend
2. Backend stores file in **Azure Blob Storage**
3. Text is extracted (PDF, Excel, Word, etc.)
4. Document is chunked and embedded
5. Vectors stored in **Azure AI Search** (RAG)
6. Entities and relationships extracted to **Cosmos DB Gremlin** (KAG)
7. File marked as "indexed" and ready for queries

### Supported File Types
- 📊 **Spreadsheets**: `.csv`, `.xlsx`, `.xls`
- 📄 **Documents**: `.pdf`, `.docx`, `.doc`
- 📝 **Text**: `.txt`, `.md`
- 📽️ **Presentations**: `.pptx`, `.ppt`

See [`FILE_UPLOAD_DOCUMENT_SYSTEM.md`](FILE_UPLOAD_DOCUMENT_SYSTEM.md) for technical details.

---

## 🛠️ Technology Stack

### Frontend
- **React 18** + **TypeScript**
- **Vite** (build tool)
- **TailwindCSS** (styling)
- **shadcn/ui** (UI components)
- **Zustand** (state management)
- **Monaco Editor** (code editor)
- **React Router** (routing)

### Backend
- **FastAPI** (web framework)
- **Azure AI Foundry** (LLM orchestration)
- **Azure AI Search** (RAG retrieval)
- **Azure Cosmos DB** (KAG graph database)
- **Azure Blob Storage** (file storage)
- **Databricks** (code execution sandbox)
- **WebSockets** (real-time streaming)

### Agent Framework
- Custom **ReAct loop** implementation
- **LangChain** integration
- Tool-calling via Azure OpenAI

---

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
pytest tests/
```

### Verify Agent Functionality
```bash
python verify_agent.py
```

### Test WebSocket Connection
```bash
python test_ws_connection.py
```

---

## 📚 Additional Documentation

- [`agents/AGENT_ARCHITECTURE.md`](agents/AGENT_ARCHITECTURE.md) - Agent system design
- [`FILE_UPLOAD_DOCUMENT_SYSTEM.md`](FILE_UPLOAD_DOCUMENT_SYSTEM.md) - File handling details
- [`backend/README.md`](backend/README.md) - Backend-specific docs
- [`Ai_Assistant_Frontend/README.md`](Ai_Assistant_Frontend/README.md) - Frontend-specific docs

---

## 🐛 Troubleshooting

### Backend won't start
- ✅ Check `.env` file has all required Azure credentials
- ✅ Verify Python virtual environment is activated
- ✅ Ensure port 8000 is not already in use

### Frontend shows connection error
- ✅ Ensure backend is running on `http://localhost:8000`
- ✅ Check Vite proxy configuration in `vite.config.ts`

### "Write code" creates notebook cells (should not)
- ✅ Ensure backend server was restarted after recent updates
- ✅ Check `agents/orchestrator/agent.py` and `agents/python_agent/agent.py` for correct prompt logic

### File upload fails
- ✅ Check Azure Blob Storage connection string
- ✅ Verify Azure AI Search credentials
- ✅ Check file size limits (default: 50MB)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

This project is proprietary. All rights reserved.

---

## 👥 Team

Developed by Mindlytics Solutions

---

## 📞 Support

For issues or questions, please open a GitHub issue or contact the development team.
