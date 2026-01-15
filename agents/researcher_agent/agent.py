"""
Market Researcher Agent
Conducts market research using RAG/KAG data
"""
from typing import Dict, List, Any
from agents.base.agent import BaseAgent, AgentResponse


class ResearcherAgent(BaseAgent):
    """
    Market Researcher Agent
    Uses RAG and KAG to conduct market research analysis
    """
    
    def __init__(self):
        super().__init__(
            name="Market Researcher",
            description="Conducts market research analysis using uploaded documents and knowledge graphs"
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a concise market research expert.

Your role is to help users understand what data is available in the system.

IMPORTANT: Your research is strictly limited to METADATA (titles, filenames, schemas) provided in your context.
You CANNOT read the actual content of documents, but you CAN see their structure.

Guidelines:
1. Identify relevant documents based on their titles and metadata.
2. If a user asks about a specific file (e.g., "describe sample-1.csv") and you see a similar one (e.g., "sample1.csv"), point this out.
3. If you don't see the exact file in your initial context, use the `search_documents` tool to look for it explicitly.
4. When suggesting files, mention their "Schema" (columns) if available in the title.
5. RECOMMEND which documents to open/read (for the user to do).

DATA ACCESS RESTRICTIONS:
- NO CONTENT ACCESS: You cannot summarize text you cannot see.
- METADATA ONLY: You see filenames, properties, and labels.
- PROHIBITED: Do not pretend to read the file content.

If the user asks for a summary of a file, say: "I cannot read the internal file content directly. However, based on the metadata (Title: ...), it appears to cover [topics]. Please open it to analyze the full data."

At the end of your response, provide 2-3 short "Suggestions:" for follow-up questions."""
    
    def _get_tools(self) -> List[Dict]:
        return [
            {
                "name": "search_documents",
                "description": "Explicity search for uploaded documents by name or topic to see their metadata",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The file name or topic to search for"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "analyze_trends",
                "description": "Analyze market trends based on metadata of available documents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "The market topic to analyze"}
                    },
                    "required": ["topic"]
                }
            }
        ]

    async def search_documents(self, query: str) -> Dict[str,Any]:
        """Tool to explicitly search for documents"""
        # BaseAgent.execute already injects context, but this tool allows
        # the agent to double-check or look for something specific if not found.
        # We reuse retrieve_context but with the clean query.
        context = await self.retrieve_context(query)
        return {
            "status": "success",
            "matches": context.get("context_text", "No specific matches found for that query."),
            "sources": context.get("sources_used", [])
        }

    async def analyze_trends(self, topic: str) -> Dict[str,Any]:
        """Tool to analyze trends from metadata"""
        # Similar to search, but framed as trend analysis
        context = await self.retrieve_context(f"trends in {topic}")
        return {
            "status": "success",
            "analysis_base": context.get("context_text", f"No metadata found relating to {topic}."),
            "message": f"I have gathered the following metadata related to {topic}. I will now formulate an analysis based on these file titles and schemas."
        }
