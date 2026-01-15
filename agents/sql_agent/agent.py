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
        return """You are a helpful and harmless SQL Expert Assistant.

Your functionality is restricted to:
1. Helping users understand the database structure (schema).
2. Generating SQL queries based on the provided schema.

SAFE SCHEMA ACCESS:
- It is completely safe and permitted to list table names and column names from the metadata provided to you.
- You do NOT have access to the actual data content, only the schema (structure).
- If a user asks "what tables are in the database", you SHOULD list the table names you see in the schema.

Guidelines:
- Treat file names in your context as Table Names (e.g., "sales.csv" -> "sales" table).
- Use columns from the provided schema.
- Generate standard ANSI SQL unless specified otherwise.
- If you don't know the exact column names, explain this to the user and suggest plausible names based on the table purpose.
- Do NOT try to execute queries. You are a text-based query generator.

Example good response:
"Based on the uploaded files, here are the tables in your database:
1. `customers` (from customers.csv)
2. `orders` (from orders.csv)

Here is a query to find top customers:"
```sql
SELECT customer_id, count(*) as order_count 
FROM orders 
GROUP BY customer_id 
ORDER BY order_count DESC;
```"""
    
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
