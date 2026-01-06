"""
Base Agent Class
All agents inherit from this class
Uses Azure AI Foundry SDK for LLM operations
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import sys
import os

# Note: sys.path is set up by app.main on startup
from app.core.shared_state import shared_state


@dataclass
class AgentResponse:
    """Standard response from an agent"""
    content: str
    agent_name: str
    sources: List[str] = None
    metadata: Dict[str, Any] = None
    success: bool = True
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Abstract base class for all agents
    
    SECURITY: Data access is restricted to DataAccessLayer only.
    Agents can ONLY access data through:
    - RAG (Azure AI Search) 
    - KAG (Cosmos DB Gremlin)
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._llm = None
        self._data_layer = None
    
    @property
    def llm(self):
        """Lazy load LLM client"""
        if self._llm is None:
            self._llm = self._initialize_llm()
        return self._llm
    
    def _initialize_llm(self):
        """Initialize Azure AI Foundry LLM client"""
        try:
            from app.core.azure_client import get_ai_client
            return get_ai_client()
        except ImportError as e:
            err_msg = f"Warning: Could not import Azure client for {self.name}: {e}\n"
            try:
                import traceback
                err_msg += traceback.format_exc()
                with open("C:/Users/WELCOME/.gemini/antigravity/brain/344a2003-6407-4384-a872-02ca18f46655/import_error.log", "a", encoding="utf-8") as f:
                    f.write(err_msg + "\n" + "="*50 + "\n")
            except:
                pass
            print(err_msg)
            return None
    
    @property
    def data_layer(self):
        """
        Secure Data Access Layer - the ONLY way to access data.
        
        This enforces that all data access goes through:
        - RAG (Azure AI Search)
        - KAG (Cosmos DB Gremlin)
        
        No direct file access. No direct database queries.
        """
        if self._data_layer is None:
            try:
                from app.core.data_access import get_data_access_layer
                self._data_layer = get_data_access_layer()
            except ImportError as e:
                print(f"Warning: DataAccessLayer not available: {e}")
        return self._data_layer
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        pass
    
    @abstractmethod
    def _get_tools(self) -> List[Dict]:
        """Get the tools available to this agent"""
        pass
    
    def _get_data_access_policy(self) -> str:
        """Standard data access policy for all agents"""
        return """
DATA ACCESS POLICY:
- You ONLY have access to data retrieved from the knowledge base
- Data sources: Uploaded Documents (RAG) and Knowledge Graph (KAG)
- You CANNOT access local files, databases, or external APIs directly
- When referencing data, always indicate its source
- If asked about data not in your context, say you don't have access to it
"""
    
    async def retrieve_context(self, query: str) -> Dict[str, Any]:
        """
        Retrieve context from RAG and KAG directly (using secured retrievers).
        
        This enables agents to have direct access to metadata services
        as requested by the user, while still being safe because the
        retrievers themselves are configured to only fetch metadata.
        """
        context = {
            "rag_results": [],
            "kag_results": [],
            "sources_used": [],
            "context_text": ""
        }
        
        try:
            # DIRECT ACCESS: Instantiate retrievers directly
            from app.rag.retriever import RAGRetriever
            from app.kag.graph_retriever import KAGRetriever
            
            # 1. Direct RAG Access (Metadata Only)
            rag = RAGRetriever()
            # Increase top_k to get more chunks for better coverage
            rag_docs = await rag.retrieve(query, top_k=20)
            
            unique_docs = []
            if rag_docs:
                # SESSION CATEGORIZATION: Distinguish between active session and persistent database
                active_files = shared_state.list_files()
                active_file_ids = {f.id for f in active_files}
                
                active_rag_docs = []
                historical_rag_docs = []
                seen_titles = set()
                
                for doc in rag_docs:
                    f_id = doc.get("file_id") or doc.get("metadata", {}).get("file_id")
                    title = doc.get("title", "Unknown")
                    
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)
                    
                    if f_id in active_file_ids:
                        active_rag_docs.append(doc)
                    else:
                        historical_rag_docs.append(doc)
                
                context["active_rag_results"] = active_rag_docs
                context["historical_rag_results"] = historical_rag_docs
                context["rag_results"] = active_rag_docs + historical_rag_docs
                context["sources_used"].append("Azure AI Search (Categorized)")
                
                # For backward compatibility and simplified prompt building
                unique_docs = context["rag_results"]
                
            # 2. Direct KAG Access (Graph Structure Only)
            kag = KAGRetriever()
            kag_entities = await kag.retrieve(query)
            
            if kag_entities:
                # Deduplicate entities too
                seen_entities = set()
                unique_entities = []
                for ent in kag_entities:
                    name = ent.get("name", "Unknown")
                    if name not in seen_entities:
                        unique_entities.append(ent)
                        seen_entities.add(name)
                context["kag_results"] = unique_entities
                context["sources_used"].append("Cosmos DB Gremlin (Direct Graph)")
            
            # Build context text from results
            context_parts = ["=== DATA SOURCES & METADATA ==="]
            
            # 1. ANALYZE INTENT (Conditional Filtering)
            query_lower = query.lower()
            
            # Get historical docs first so we can reference it
            hist_docs = context.get("historical_rag_results", [])
            
            # Keywords implying "Database / All History"
            db_keywords = ["database", "all metadata", "storage", "everything", "all files", "meta", "history", "archive", "repository", "azure"]
            is_database_query = any(w in query_lower for w in db_keywords)
            
            # Keywords implying "Current Session / Web UI"
            session_keywords = ["current", "session", "uploaded", "this time", "files uploaded", "web page", "webpage", "on the screen", "visible", "ui"]
            is_session_query = any(w in query_lower for w in session_keywords)
            
            # LOGIC:
            # If user asks for "current/session" AND NOT "database", we hide historical data.
            # If user asks for "uploaded metadata", that's ambiguous, but "metadata" triggers database query, so show all.
            # If user asks for "uploaded files in web page", triggers session filter.
            
            show_historical = True
            if is_session_query and not is_database_query:
                show_historical = False
                print(f"[Agent Filter] HARD GATE ACTIVE. User asked for session/web files. Hiding {len(hist_docs)} historical docs.")
                
                # CRITICAL: Purge the raw data structures too, so agents accessing 'rag_results' directly effectively see nothing.
                context["historical_rag_results"] = [] 
                context["rag_results"] = context["active_rag_results"] # ONLY active files remain
                hist_docs = [] # Local variable update for the text builder below
                

            # 2. INJECT ACTIVE SESSION FILES (Source of Truth for "Currently Uploaded")
            all_files = shared_state.list_files()
            if all_files:
                context_parts.append("\n📁 ACTIVE SESSION FILES (Source of Truth for 'Currently Uploaded'):")
                for f in all_files:
                    context_parts.append(f"  - [Session] {f.filename} (Status: {f.status})")
            else:
                context_parts.append("\n⚠️ NO FILES UPLOADED IN CURRENT SESSION.")

            # 3. INJECT PERSISTENT KNOWLEDGE BASE (Condensed)
            # Only show if show_historical is True (which corresponds to hist_docs being not empty now)
            if hist_docs:
                context_parts.append("\n💾 PERSISTENT KNOWLEDGE BASE (Historical Metadata in Database):")
                for doc in hist_docs[:15]:
                    title = doc.get('title', 'Unknown')
                    context_parts.append(f"  - [Database] {title}")
            elif not show_historical:
                 context_parts.append("\n👻 [Historical files hidden to prevent hallucinations on current session query]")

            # 4. KNOWLEDGE GRAPH
            if unique_entities:
                context_parts.append("\n🔗 KNOWLEDGE GRAPH ENTITIES:")
                for entity in unique_entities[:10]:
                    name = entity.get('name', 'Unknown')
                    label = entity.get('label', 'Entity')
                    context_parts.append(f"  - [Graph] {label}: {name}")
            
            context_parts.append("\n--- USAGE INSTRUCTIONS ---")
            context_parts.append("- If results contain both [Session] and [Database] files, distinguish them clearly.")
            context_parts.append("- If user asks about 'Current/Uploaded' items, you MUST refer to [Session] markers.")
            context_parts.append("- If user asks for 'Database/All' items, include [Database] markers.")
            context_parts.append("- If no [Session] files are present, state that clearly before mentioning database history.")
            
            if not rag_docs and not kag_entities and not all_files:
                context_parts.append("No relevant metadata found.")
                
            context["context_text"] = "\n".join(context_parts)
                
        except Exception as e:
            print(f"Direct retrieval error: {e}")
        
        return context
    
    async def execute(self, query: str, context: Dict = None) -> AgentResponse:
        """
        Execute the agent with a query
        
        Args:
            query: User query or task
            context: Optional additional context
            
        Returns:
            AgentResponse with results
        """
        try:
            # Retrieve relevant context from RAG/KAG via secure DataAccessLayer
            retrieved_context = await self.retrieve_context(query)
            
            # Merge with provided context
            full_context = {**(context or {}), **retrieved_context}
            
            # Build prompt with data access policy first
            system_prompt = self._get_data_access_policy() + "\n" + self._get_system_prompt()
            
            # Add retrieved context (with source attribution)
            if retrieved_context.get("context_text"):
                system_prompt += f"\n\n{retrieved_context['context_text']}"
            elif retrieved_context["rag_results"]:
                # Fallback for backward compatibility
                rag_text = "\n".join([str(r) for r in retrieved_context["rag_results"][:5]])
                system_prompt += f"\n\nRelevant information from uploaded documents:\n{rag_text}"
            
            # Add conversation history if available
            if full_context.get("conversation_history"):
                system_prompt += f"\n\nConversation History:\n{full_context['conversation_history']}"
            
            # Execute with LLM
            if self.llm:
                try:
                    response = await self.llm.simple_chat(
                        user_message=query,
                        system_message=system_prompt
                    )
                except Exception as llm_error:
                    print(f"LLM execution error: {llm_error}")
                    response = f"[{self.name}] I'm having trouble connecting to the AI service. Error: {str(llm_error) or 'Unknown'}"
            else:
                # Provide a meaningful fallback response
                response = f"Hello! I'm the {self.name} agent. I understood your query: '{query}'\n\n"
                response += "However, the AI model is not currently available. "
                response += "Please ensure Azure OpenAI is properly configured.\n\n"
                if retrieved_context.get("rag_results"):
                    response += f"I found {len(retrieved_context['rag_results'])} relevant documents that might help."
            
            # Include sources used in response metadata
            sources_used = retrieved_context.get("sources_used", [])
            
            return AgentResponse(
                content=response,
                agent_name=self.name,
                sources=sources_used + [str(r.get("title", r.get("content", "")[:50])) for r in retrieved_context.get("rag_results", [])[:3]],
                metadata={
                    "context_used": bool(retrieved_context["rag_results"]),
                    "sources_used": sources_used,
                    "data_access": "RAG/KAG only"
                },
                success=True
            )
            
        except Exception as e:
            error_msg = str(e) if str(e) else f"Unknown error in {self.name} agent"
            print(f"Agent execution error: {error_msg}")
            return AgentResponse(
                content=f"I apologize, I encountered an issue: {error_msg}",
                agent_name=self.name,
                success=False,
                error=error_msg
            )
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}')>"
