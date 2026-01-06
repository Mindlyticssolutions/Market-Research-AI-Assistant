"""
SQL Agent
Generates SQL queries from natural language
Uses RAG to understand database schema
"""
from typing import Dict, List
from agents.base.agent import BaseAgent, AgentResponse


class SQLAgent(BaseAgent):
    """
    SQL Agent - Generates and explains SQL queries
    Does NOT execute queries directly - only generates them
    """
    
    def __init__(self):
        super().__init__(
            name="SQL Agent",
            description="Generates SQL queries from natural language using RAG-retrieved schema information"
        )
    
    def _get_system_prompt(self) -> str:
        return """You are a SQL expert assistant.

IMPORTANT: You work ONLY with schema metadata (table names, column names) provided in your context.
You do NOT have access to run queries or see table content.

Your role is to:
1. Generate syntactically correct SQL queries based on the provided schema
2. Explain how to join tables based on column names/keys
3. Optimize potential queries

DATA ACCESS RESTRICTIONS:
- READ-ONLY METADATA ACCESS: You see schema only
- NO EXECUTION: Queries you meet are for reference only
- NO DATA PREVIEW: You cannot see sample data

Guidelines:
- Treat file names provided in metadata as Table Names (e.g., "sales.csv" -> "sales" table)
- Inherit columns from any provided file headers/schema metadata
- Generate standard ANSI SQL unless a specific dialect is requested
- If exact column names are unknown, use descriptive placeholders (e.g., `user_id`, `created_at`) and explain your assumption
- Construct queries that *would* work if the data were loaded into a database with that schema

Example good response:
```sql
-- Query to find top customers (Generated based on schema 'customers' table)
SELECT customer_id, count(*) as order_count 
FROM orders 
GROUP BY customer_id 
ORDER BY order_count DESC;
```

At the bottom, provide 2-3 short "Suggestions:" for query improvements."""
    
    def _get_tools(self) -> List[Dict]:
        return [
            {
                "name": "generate_sql",
                "description": "Generate a SQL query from natural language",
                "parameters": {"question": "string"}
            },
            {
                "name": "explain_sql",
                "description": "Explain what a SQL query does",
                "parameters": {"query": "string"}
            }
        ]
    
    async def execute(self, query: str, context: Dict = None, callback=None) -> AgentResponse:
        """Generate SQL query from natural language"""
        # Enhance system prompt with schema info if available
        enhanced_prompt = self._get_system_prompt()
        
        if context and "schema" in context:
            enhanced_prompt += f"\n\nDatabase Schema:\n{context['schema']}"
        
        # Use base execution with enhanced prompt
        return await super().execute(query, context, callback=callback)
