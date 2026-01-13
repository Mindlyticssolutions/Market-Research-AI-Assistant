"""
Orchestrator Agent
Routes queries to appropriate specialized agents
Coordinates multi-agent tasks
"""
from typing import Dict, List, Any
from agents.base.agent import BaseAgent, AgentResponse


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - Routes queries to specialized agents
    """
    
    def __init__(self):
        super().__init__(
            name="Orchestrator",
            description="Routes queries to appropriate agents and coordinates multi-agent tasks"
        )
        self.agent_routing = {
            "sql": ["sql", "query", "database", "table", "select", "join"],
            "python": ["code", "python", "script", "analyze", "calculate", "plot", "visualize"],
            "researcher": ["research", "market", "trend", "competitor", "industry", "report"],
            "analyst": ["analyze", "statistics", "insight", "pattern", "correlation"],
            "writer": ["write", "report", "summary", "document", "executive"]
        }
    
    def _get_system_prompt(self) -> str:
        return """You are the Orchestrator Agent. Your ONLY job is to route the user's request to the correct specialized agent.

AVAILABLE AGENTS:
1. "python": For data analysis, calculations, coding, plotting, and visualization.
   - Keywords: run, calculate, plot, analyze, python, code, graph, chart.
2. "sql": For database queries and SQL.
   - Keywords: sql, query, database, select, join.
3. "researcher": For searching files, documents, or general knowledge.
   - Keywords: search, find, what is, look up.
4. "analyst": For high-level business insights and recommendations (non-technical).
5. "writer": For summarizing, writing reports, or editing text.

CRITICAL RULES:
0. Start your thought process with an extremely concise summary (1-3 words) in brackets, e.g., `[Task: Fibonacci]`. 
   - **IMPORTANT**: ONLY output `[Task: ...]` if you are routing to `sql`, `python` (for EXECUTION), or `researcher`.
   - If routing to `python` for "TEXT ONLY" (write/show code), DO NOT output `[Task: ...]`. Just go straight to the explanation.
1. For data execution tasks (run, calculate, analyze, plot, graph), use the `route_to_agent` tool and ALWAYS prefix the query string with "EXECUTE: ".
2. For "show/write" requests (provide example, how to, show code for, script for), use the `route_to_agent` tool and ALWAYS prefix the query string with "TEXT ONLY: ".
3. For general knowledge, use the researcher.
4. - ALWAYS use the `route_to_agent` tool immediately."""
    
    def _get_tools(self) -> List[Dict]:
        return [
            {
                "name": "route_to_agent",
                "description": "Route a query to a specialized agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string", 
                            "enum": ["sql", "python", "researcher", "analyst", "writer"],
                            "description": "The name of the specialized agent to handle the task"
                        },
                        "query": {
                            "type": "string",
                            "description": "The specific query or task to delegate"
                        }
                    },
                    "required": ["agent_name", "query"]
                }
            }
        ]
    
    async def execute(self, query: str, context: Dict = None, callback=None) -> AgentResponse:
        """Execute orchestrator logic via ReAct loop"""
        return await super().execute(query, context, callback=callback)
