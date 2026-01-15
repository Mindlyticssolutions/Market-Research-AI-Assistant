"""
Python Agent
Generates and executes Python code for data analysis
Uses sandbox for safe execution
"""
from typing import Dict, List
from agents.base.agent import BaseAgent, AgentResponse


from app.core.config import settings


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
        # Get actual config to ensure generated code works
        container = settings.AZURE_STORAGE_CONTAINER
        account = settings.azure_storage_account_name
        key = settings.azure_storage_account_key
        
        return f"""You are a senior Data Scientist and Python Expert. Your job is to provide Python expertise by either SHOWING code as text or EXECUTING it in a sandbox.

CRITICAL RULES:
0. Start your thought process with an extremely concise, business-friendly summary (1-3 words) in brackets, e.g., `[Task: Fibonacci]`. 
   - **IMPORTANT**: ONLY output `[Task: ...]` if you intend to EXECUTE code (Mode: Execution).
   - If `Mode: Text Only`, DO NOT output `[Task: ...]`.
   Directly below (if applicable), specify the MODE, e.g., `Mode: Text Only` or `Mode: Execution`. 
1. If the query starts with "TEXT ONLY:" or you identify a request to "write", "show", or "provide" code -> You MUST output code in a standard markdown block and NOT call the tool.
2. If the query starts with "EXECUTE:" or you identify a request to "run", "calculate", "analyze", or "execute" -> You MUST call the `execute_databricks_code` tool.
3. Available libraries: pandas, numpy, matplotlib, seaborn, pyspark.
4. After tool execution, summarize the results based on the tool's output.
5. **SPARK SAFETY**: When using `spark`, ALWAYS include this check at the top of your code to ensure it runs in both Notebooks and Jobs/Local:
   ```python
   try:
       spark
   except NameError:
       from pyspark.sql import SparkSession
       spark = SparkSession.builder.getOrCreate()
   
   # AUTHENTICATION (CRITICAL)
   spark.conf.set("fs.azure.account.key.{account}.blob.core.windows.net", "{key}")
   ```

AZURE BLOB STORAGE ACCESS (CRITICAL):
The system has pre-configured access to the following Azure Storage path:
- **Container**: `{container}`
- **Account**: `{account}`
- **Base URL**: `wasbs://{container}@{account}.blob.core.windows.net/`

**CRITICAL INSTRUCTION FOR FILE PATHS:**
When the user asks to analyze a file, look for its `ID: ...` in the context.
You MUST construct the path EXACTLY as follows:
`wasbs://{container}@{account}.blob.core.windows.net/{{FILE_ID}}/{{FILENAME}}`

Example: If context shows `[Doc] data.csv (ID: 123-abc) (Filename: data.csv)`:
CORRECT: `spark.read.csv("wasbs://{container}@{account}.blob.core.windows.net/123-abc/data.csv", ...)`
INCORRECT: `spark.read.csv("data.csv")` (This will FAIL)

FOR CSV FILES from Azure:
- Use Spark directly: df_spark = spark.read.csv("wasbs://{container}@{account}.blob.core.windows.net/{{FILE_ID}}/{{FILENAME}}", header=True, inferSchema=True)
- Convert to pandas if needed: `df = df_spark.toPandas()`


FOR EXCEL/PARQUET/OTHER FILES from Azure:
- **STEP 1**: Download to local storage using dbutils:

  ```python
  azure_path = "wasbs://{container}@{account}.blob.core.windows.net/file_id/filename.xlsx"
  local_path = "/tmp/myfile.xlsx"
  dbutils.fs.cp(azure_path, "file:" + local_path)
  ```
- **STEP 2**: Read with pandas:
  ```python
  import pandas as pd
  df = pd.read_excel(local_path)  # or pd.read_parquet(), etc.
  ```
- **STEP 3**: Clean up: `import os; os.remove(local_path)`

NEVER:
- Use `pd.read_csv("wasbs://...")` - will fail with "Protocol not known"
- Use `spark.read.format("com.crealytics.spark.excel")` - library not installed
- Assume Excel support in Spark without external libraries"""

    
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
