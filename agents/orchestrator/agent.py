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
        return """You are the Orchestrator for an AI Data Science platform.
Your primary role is to understand the user's intent and route them to the most suitable specialized agent.

Available agents:
- sql: For accessing structured database tables and performing SQL queries.
- python: For math, data science, Python scripts, generating charts, and complex calculations.
- researcher: For general web-scale knowledge, market trends, and industry context.
- analyst: For deep statistical analysis and finding patterns in data.
- writer: For formatting reports and summarizing findings.

When responding:
1. Briefly (in 1 short sentence) tell the user which agent will handle their request.
2. Call the `route_to_agent` tool to delegate the task.

IMPORTANT:
- Always use the `route_to_agent` tool for any request that fits the specialized agents.
- Keep your initial text extremely brief.
- Provide 2-3 "Suggestions:" at the very bottom for next steps."""
    
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
