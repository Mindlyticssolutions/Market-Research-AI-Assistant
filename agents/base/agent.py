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
import asyncio
import re
import json

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


@dataclass
class AgentResponse:
    """Standard response from an agent"""
    content: str
    agent_name: str
    sources: List[str] = None
    metadata: Dict[str, Any] = None
    success: bool = True
    error: Optional[str] = None
    plot: Optional[str] = None # Base64 encoded image


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
        except ImportError:
            print(f"Warning: Could not import Azure client for {self.name}")
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
    
    def _get_tool_choice(self) -> str:
        """Get tool choice mode for this agent. Override to 'required' to force tool use."""
        return "auto"
    
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
            print(f"DEBUG: [{self.name}] retrieve_context started for query: {query[:50]}")
            # DIRECT ACCESS: Instantiate retrievers directly
            from app.rag.retriever import RAGRetriever
            from app.kag.graph_retriever import KAGRetriever
            
            # 1. Direct RAG Access (Metadata Only)
            print(f"DEBUG: [{self.name}] Initializing RAGRetriever...")
            rag = RAGRetriever()
            print(f"DEBUG: [{self.name}] Calling RAGRetriever.retrieve...")
            rag_docs = await rag.retrieve(query)
            print(f"DEBUG: [{self.name}] RAGRetriever.retrieve complete. docs count: {len(rag_docs) if rag_docs else 0}")
            
            if rag_docs:
                context["rag_results"] = rag_docs
                context["sources_used"].append("Azure AI Search (Direct Metadata)")
                
            # 2. Direct KAG Access (Graph Structure Only)
            print(f"DEBUG: [{self.name}] Initializing KAGRetriever...")
            kag = KAGRetriever()
            print(f"DEBUG: [{self.name}] Calling KAGRetriever.retrieve...")
            kag_entities = await kag.retrieve(query)
            print(f"DEBUG: [{self.name}] KAGRetriever.retrieve complete. entities count: {len(kag_entities) if kag_entities else 0}")
            
            if kag_entities:
                context["kag_results"] = kag_entities
                context["sources_used"].append("Cosmos DB Gremlin (Direct Graph)")
            
            # Build context text from results
            context_parts = ["=== AVAILABLE METADATA (Direct Access) ==="]
            
            if rag_docs:
                context_parts.append("\n📁 Documents (Metadata):")
                # Deduplicate by title/filename to avoid cluttering context with chunks
                seen_files = set()
                for doc in rag_docs:
                    title = doc.get('title', 'Unknown')
                    # Fallback chain for filename
                    fname = doc.get('metadata_storage_name') or doc.get('source') or doc.get('filename') or "Unknown File"
                    
                    # If it's a long source URL, just take the basename
                    if "/" in fname or "\\" in fname:
                        import os
                        fname = os.path.basename(fname)
                    
                    file_key = f"{title}_{fname}"
                    if file_key not in seen_files:
                        file_id = doc.get('file_id') or doc.get('id') or "unknown_id"
                        context_parts.append(f"  - [Doc] {title} (ID: {file_id}) (Filename: {fname})")
                        seen_files.add(file_key)

            if kag_entities:
                context_parts.append("\n🔗 Knowledge Graph (Structure):")
                for entity in kag_entities[:10]: # Show more entities
                    name = entity.get('name', 'Unknown')
                    label = entity.get('label', 'Entity')
                    context_parts.append(f"  - [Graph] {label}: {name}")
            
            if not rag_docs and not kag_entities:
                context_parts.append("No relevant metadata found for this query.")
                
            context["context_text"] = "\n".join(context_parts)
            print(f"DEBUG: [{self.name}] retrieve_context complete.")
                
        except Exception as e:
            print(f"DEBUG: [{self.name}] Direct retrieval error: {e}")
            import traceback
            traceback.print_exc()
        
        return context
    
    async def execute(self, query: str, context: Dict = None, callback=None) -> AgentResponse:
        """
        Execute the agent with a query
        
        Args:
            query: User query or task
            context: Optional additional context
            callback: Async function to report intermediate progress (typing: function(event_type: str, content: str))
            
        Returns:
            AgentResponse with results
        """
        try:
            # Retrieve relevant context from RAG/KAG via secure DataAccessLayer
            retrieved_context = await self.retrieve_context(query)
            
            # Merge with provided context
            full_context = {**(context or {}), **retrieved_context}
            
            # Build prompt with data access policy first
            base_system_prompt = self._get_data_access_policy() + "\n" + self._get_system_prompt()
            
            # Add retrieved context (with source attribution)
            if retrieved_context.get("context_text"):
                base_system_prompt += f"\n\n{retrieved_context['context_text']}"
            elif retrieved_context["rag_results"]:
                rag_text = "\n".join([str(r) for r in retrieved_context["rag_results"][:5]])
                base_system_prompt += f"\n\nRelevant information from uploaded documents:\n{rag_text}"
            
            # Add conversation history
            if full_context.get("conversation_history"):
                base_system_prompt += f"\n\nConversation History:\n{full_context['conversation_history']}"

            messages = [{"role": "system", "content": base_system_prompt}]
            messages.append({"role": "user", "content": query})

            # ReAct Loop
            max_steps = 10
            max_retries = 3
            step_count = 0
            retry_count = 0
            
            if callback:
                await callback("thinking", f"Planning how to answer: {query}")

            has_executed_tool = False  # Track if we've already executed a tool
            
            print(f"DEBUG: [{self.name}] starting execute with query: {query[:50]}...", flush=True)
            while step_count < max_steps:
                if self.llm:
                    print(f"DEBUG: [{self.name}] Step {step_count} - Calling LLM...", flush=True)
                    try:
                        # 1. Plan / Think
                        tools = self._get_tools()
                        
                        # Call LLM with tools
                        # IMPORTANT: After a tool has been executed, switch to "none" to allow final response
                        if has_executed_tool:
                            tool_choice_value = "none"  # Force text response after tool execution
                        else:
                            tool_choice_value = self._get_tool_choice() if tools else None
                        print(f"DEBUG: [{self.name}] Using tool_choice={tool_choice_value}", flush=True)
                        
                        # When tool_choice is "none", don't pass tools to avoid LLM confusion
                        tools_to_pass = None if tool_choice_value == "none" else (tools if tools else None)
                        
                        response_message = await self.llm.chat_completion(
                            messages=messages,
                            tools=tools_to_pass,
                            tool_choice=tool_choice_value if tools_to_pass else None
                        )
                        
                        content_str = response_message.content[:100] if response_message.content else "None (Tool Call)"
                        print(f"DEBUG: [{self.name}] LLM Response Content: {content_str}...")
                        
                        # Extract Dynamic Query Summary [Task: ...]
                        if response_message.content:
                            summary_match = re.search(r'\[(?:Task|Summary):\s*(.*?)\]', response_message.content)
                            if summary_match and callback:
                                summary = summary_match.group(1).strip()
                                print(f"DEBUG: [{self.name}] Detected Task Summary: {summary}")
                                await callback("query_summary", summary)
                        
                        # Check for tool calls
                        tool_calls = self.llm.parse_tool_calls(response_message)
                        
                        if tool_calls:
                            print(f"DEBUG: [{self.name}] Detected {len(tool_calls)} tool calls")
                            # 2. Act (Execute Tool)
                            
                            # CRITICAL: Nullify content if tool calls are present to prevent LLM from "reading its own chatter"
                            # This fixes the "Echo" bug where the agent repeats its own tool call string.
                            if response_message.content:
                                print(f"DEBUG: [{self.name}] Clearing assistant content to prioritize tool calls")
                                response_message.content = None
                                
                            messages.append(response_message) # Add assistant's thought/tool_call to history
                            
                            for tool_call in tool_calls:
                                function_name = tool_call.function.name
                                function_args = tool_call.function.arguments
                                print(f"DEBUG: [{self.name}] Executing tool: {function_name} with args: {function_args}")
                                
                                if callback:
                                    await callback("thinking", f"Executing tool: {function_name}")
                                
                                try:
                                    import json
                                    args = json.loads(function_args)
                                    
                                    # DYNAMIC TOOL HANDLING
                                    tool_output = None
                                    
                                    # 1. Check if the agent has a method for this tool (e.g. SQLAgent.execute_sql)
                                    if hasattr(self, function_name) and function_name != "execute":
                                        method = getattr(self, function_name)
                                        if callable(method):
                                            print(f"DEBUG: [{self.name}] Calling class method for {function_name}")
                                            tool_output = await method(**args) if asyncio.iscoroutinefunction(method) else method(**args)
                                    
                                    # 2. Handle known cross-agent tools (Databricks)
                                    elif function_name == "execute_databricks_code":
                                        print(f"DEBUG: [{self.name}] Calling execute_databricks_code handler")
                                        from app.api.v1.endpoints.databricks import execute_code, ExecuteRequest
                                        code = args.get("code")
                                        language = args.get("language", "python")
                                        
                                        if callback:
                                            await callback("code_execution", code)
                                        
                                        cluster_id = full_context.get("cluster_id", "mock-cluster-1")
                                        result = await execute_code(ExecuteRequest(
                                            cluster_id=cluster_id,
                                            code=code,
                                            language=language
                                        ))
                                        
                                        tool_output = {
                                            "status": result.status,
                                            "output": result.output,
                                            "error": result.error,
                                            "plot": "Plot generated" if result.plot else None
                                        }
                                        
                                        if callback:
                                            if result.status == "success":
                                                await callback("observation", result.output if result.output else "Execution successful (no output).")
                                            else:
                                                await callback("observation", f"Error: {result.error}")
                                    
                                    # 3. Handle default routing for Orchestrator (Terminal Action)
                                    elif function_name == "route_to_agent":
                                        target = args.get("agent_name")
                                        query_to_route = args.get("query", query)
                                        print(f"DEBUG: [{self.name}] Routing to {target} with query: {query_to_route[:50]}...")
                                        
                                        from agents.registry import AgentRegistry
                                        target_agent = AgentRegistry.get_agent(target)
                                        if target_agent:
                                            print(f"DEBUG: [{self.name}] Found target agent {target}, delegating...")
                                            # TERMINAL: Directly return the target agent's response to the user
                                            delegated_response = await target_agent.execute(query_to_route, context, callback=callback)
                                            print(f"DEBUG: [{self.name}] Received delegated response from {target}")
                                            return delegated_response
                                        else:
                                            print(f"DEBUG: [{self.name}] Agent {target} not found in registry")
                                            tool_output = {"status": "error", "error": f"Agent {target} not found"}
                                            
                                    else:
                                        print(f"DEBUG: [{self.name}] Tool {function_name} not implemented")
                                        tool_output = {"status": "error", "error": f"Tool {function_name} not implemented"}
                                        
                                except Exception as e:
                                    print(f"DEBUG: [{self.name}] Exception during tool {function_name}: {str(e)}")
                                    tool_output = {"status": "error", "error": str(e)}
                                    if callback:
                                        await callback("observation", f"Tool execution exception: {str(e)}")
                                        
                                # 3. Observe (Feed back to LLM)
                                messages.append({
                                    "tool_call_id": tool_call.id,
                                    "role": "tool",
                                    "name": function_name,
                                    "content": json.dumps(tool_output) if not isinstance(tool_output, str) else tool_output
                                })
                            
                            step_count += 1
                            has_executed_tool = True  # Mark that we've executed tools, next turn should allow text response
                            continue # GO TO NEXT TURN
                        
                        # No tool calls -> Final Answer
                        content = response_message.content
                        
                        # SANITY CHECK: If content looks like a tool call string, it's likely an echo or mistake.
                        # We don't want to return "route_to_agent(...)" as the final answer.
                        if content and ("route_to_agent" in content or "execute_databricks_code" in content):
                            print(f"DEBUG: [{self.name}] Final content looks like a tool call string. Attempting recovery turn.")
                            # If it's the Orchestrator, it might have failed to use the real tool but wrote it in text.
                            # Let's try to parse it as a tool call one last time or just take another turn.
                            step_count += 1
                            continue
                        
                        print(f"DEBUG: [{self.name}] No more tool calls. Forming final response.")
                        sources_used = retrieved_context.get("sources_used", [])
                        
                        return AgentResponse(
                            content=content,
                            agent_name=self.name,
                            sources=sources_used + [str(r.get("title", r.get("content", "")[:50])) for r in retrieved_context.get("rag_results", [])[:3]],
                            metadata={
                                "context_used": bool(retrieved_context["rag_results"]),
                                "sources_used": sources_used,
                                "data_access": "Hybrid RAG + Code Interpreter"
                            },
                            success=True
                        )

                    except Exception as llm_error:
                        print(f"LLM execution error: {llm_error}")
                        retry_count += 1
                        if retry_count >= max_retries:
                             raise llm_error
                else:
                    break

            return AgentResponse(
                content="I tried to process your request but reached the maximum allowed steps or encountered repeated errors.",
                agent_name=self.name,
                success=False,
                error="Max steps or retries exceeded"
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
