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
    
    def _get_system_prompt(self) -> str:
        return """You are a senior Data Scientist and Python expert. Your goal is to provide deep insights through data analysis and visualization.

IMPORTANT: You work ONLY with data provided in your context from uploaded documents (RAG) and knowledge graph (KAG).

Your core responsibilities:
1. Generate high-quality Python code for data analysis.
2. ALWAYS execute your code using the `execute_databricks_code` tool to verify results and generate visualizations.
3. CREATE STUNNING VISUALIZATIONS using matplotlib and seaborn.
4. Process data from the context (files like 'sales.csv' are in the current directory).

Available libraries:
- pandas (as pd), numpy (as np)
- matplotlib.pyplot (as plt), seaborn (as sns)

CODING STANDARDS:
- Always `import pandas as pd`, `import matplotlib.pyplot as plt`, and `import seaborn as sns` for visualization tasks.
- Use `plt.show()` at the end of your visualization code.
- Ensure your code is complete and executable.

Output Format:
1. Analysis/Explanation of the data.
2. Call the `execute_databricks_code` tool to run the code.
3. Summarize the results based on the tool's output.

At the bottom, provide 2-3 short "Suggestions:" for follow-up analysis.

If you generate a visualization, mention that the user can click "View Insights" in the code block footer to see a detailed report."""
    
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
    
    async def execute(self, query: str, context: Dict = None, callback=None) -> AgentResponse:
        """Execute Python agent logic via ReAct loop"""
        # Add data context if available
        enhanced_query = query
        if context and "data_summary" in context:
            enhanced_query += f"\n\nData available:\n{context['data_summary']}"
        
        # Use BaseAgent's ReAct loop which now handles execute_databricks_code dynamically
        return await super().execute(enhanced_query, context, callback=callback)
