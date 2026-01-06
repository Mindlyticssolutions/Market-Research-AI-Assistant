# Analytix: AI-Powered Data Assistant 🚀

Analytix is a state-of-the-art AI-powered data analysis platform that combines **Multi-Agent Orchestration**, **RAG (Retrieval-Augmented Generation)**, and **KAG (Knowledge-Augmented Generation)** to help users analyze structured and unstructured datasets securely.

---

## 🏗️ Architecture Overview

The system is built with a decoupled "Data Instance" security architecture:

- **Frontend**: Clean React/Vite dashboard for data visualization and chat.
- **Backend**: FastAPI server handling authentication, file processing, and agent coordination.
- **Agent Framework**: Multi-agent system (Orchestrator, Researcher, Analyst, etc.) using Azure OpenAI.
- **Storage Layer**: 
  - **Azure Blob Storage**: Raw file storage for uploaded datasets.
  - **Azure AI Search (RAG)**: Vector-indexed metadata and document chunks.
  - **Azure Cosmos DB (KAG)**: Knowledge graph structure.

---

## 🤖 Multi-Agent System

The platform uses a specialized agent registry:

1. **Orchestrator**: Routes user queries to the best specialist.
2. **Researcher**: Specialized in RAG/KAG retrieval (Metadata visibility only).
3. **Analyst**: Processes statistical patterns and insights.
4. **SQL Agent**: (Planned/Integration) For direct database querying.
5. **Python Agent**: For dynamic code execution and plotting.

> [!IMPORTANT]
> **Metadata Security**: Agents ONLY see metadata (filenames, schemas, topics). They cannot read raw sensitive data values unless explicitly processed by Databricks for insights.

---

## 🛠️ Tech Stack

- **Frontend**: React, TypeScript, Vite, Tailwind CSS.
- **Backend**: Python 3.10+, FastAPI, Uvicorn.
- **AI/ML**: LangChain, Azure OpenAI (GPT-4.1, Text-Embedding-Ada-002).
- **Search**: Azure AI Search.
- **Cloud**: Azure Blob Storage, Azure Cosmos DB.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js & npm
- Azure OpenAI/Storage credentials in `.env`

### 2. Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd Ai_Assistant_Frontend
npm install
npm run dev
```

---

## 🖇️ Key Features

- **Sync File Indexing**: New uploads are indexed synchronously into Azure AI Search, making them queryable immediately.
- **Smart Deduplication**: Agent context is automatically cleaned to show unique files instead of redundant chunks.
- **Hybrid Search**: Combines semantic vector search with keyword matching.
- **Interactive Sandbox**: View data sources and visualizations in real-time.

---

## 📁 Project Structure

```text
AI-Assistant/
├── agents/                 # Multi-agent framework
│   ├── base/               # Core BaseAgent and logic
│   ├── orchestrator/       # Routing and coordination
│   └── researcher_agent/   # Specialist agents
├── backend/                # FastAPI Application
│   ├── app/                # Core logic, API, RAG
│   └── .env                # Environment configuration
└── Ai_Assistant_Frontend/  # React Application
```

---

## 📝 Recent Fixes (Dec 2025)

- **Import Path Resolution**: Standardized `sys.path` in `main.py` for global agent accessibility.
- **Upload Latency**: Moved indexing to synchronous execution to prevent "file not found" errors immediately after upload.
- **Agent Visibility**: Implemented title-based deduplication in the agent context window to ensure new files aren't hidden by old ones.
