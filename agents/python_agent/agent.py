"""
Python Agent
Generates and executes Python code for data analysis
Uses sandbox for safe execution
"""
from typing import Dict, List
from agents.base.agent import BaseAgent, AgentResponse


class PythonAgent(BaseAgent):
    """
    Python Agent - Generates Python code for data analysis
    Can execute code in a sandboxed environment
    """
    
    def __init__(self):
        super().__init__(
            name="Python Agent",
            description="Generates Python code for data analysis and visualization"
        )
        self._current_query = ""
    
    def _get_system_prompt(self) -> str:
        return """You are a senior Data Scientist and Python Expert. Your job is to provide Python expertise by either SHOWING code as text or EXECUTING it in a sandbox.

CRITICAL RULES:
CRITICAL RULES:
0. Start your thought process with an extremely concise, business-friendly summary (1-3 words) in brackets, e.g., `[Task: Fibonacci]`. 
   - **IMPORTANT**: ONLY output `[Task: ...]` if you intend to EXECUTE code (Mode: Execution).
   - If `Mode: Text Only`, DO NOT output `[Task: ...]`.
   Directly below (if applicable), specify the MODE, e.g., `Mode: Text Only` or `Mode: Execution`. 
1. If the query starts with "TEXT ONLY:" or you identify a request to "write", "show", or "provide" code -> You MUST output code in a standard markdown block and NOT call the tool.
2. If the query starts with "EXECUTE:" or you identify a request to "run", "calculate", "analyze", or "execute" -> You MUST call the `execute_databricks_code` tool.
3. Available libraries: pandas, numpy, matplotlib, seaborn.
4. After tool execution, summarize the results based on the tool's output."""
    
    def _get_tools(self) -> List[Dict]:
        return [
            {
                "name": "execute_databricks_code",
                "description": "Execute Python code in Databricks sandbox and return results/plots",
                "parameters": {
                    "code": "string",
                    "language": "string"
                }
            }
        ]
    
    def _get_tool_choice(self) -> str:
        """Dynamically mask tool usage if the intent is strictly 'write/show'."""
        q = self._current_query.upper()
        
        # 1. Absolute Overrides based on Orchestrator Prefix
        if "TEXT ONLY:" in q:
            print(f"DEBUG: [Python Agent] Strict Prefix detected: TEXT ONLY. Disabling tools.")
            return "none"
        if "EXECUTE:" in q:
            print(f"DEBUG: [Python Agent] Strict Prefix detected: EXECUTION. Enabling tools.")
            return "auto"
            
        # 2. Keyword Fallback
        q_lower = q.lower()
        write_keywords = ["write", "show", "provide", "example", "how to", "just the code", "code for", "script for"]
        run_keywords = ["run", "calculate", "analyze", "execute", "plot", "visualize", "determine", "process"]
        
        # If it looks like a request to SEE code and NOT run it
        if any(k in q_lower for k in write_keywords) and not any(k in q_lower for k in run_keywords):
            return "none"
            
        return "auto"
    
    async def execute(self, query: str, context: Dict = None, callback=None) -> AgentResponse:
        """Execute Python agent logic via ReAct loop"""
        self._current_query = query # Track for tool choice logic
        # Add data context if available
        enhanced_query = query
        if context and "data_summary" in context:
            enhanced_query += f"\n\nData available:\n{context['data_summary']}"
        
        # Use BaseAgent's ReAct loop which now handles execute_databricks_code dynamically
        return await super().execute(enhanced_query, context, callback=callback)
