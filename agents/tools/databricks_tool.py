from pydantic import BaseModel, Field

class ExecuteDatabricksCode(BaseModel):
    """
    Execute Python code in a Databricks sandbox environment.
    Use this tool to perform data analysis, data manipulation, or calculation that requires Python.
    The code will be executed in a persistent notebook session.
    """
    code: str = Field(..., description="The valid Python code to execute.")
    language: str = Field("python", description="The language of the code (default: python).")

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_databricks_code",
        "description": "Execute Python code in a Databricks sandbox. Returns stdout, stderr, and plots.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The valid Python code to execute."
                },
                "language": {
                    "type": "string",
                    "description": "The language (python or sql)",
                    "enum": ["python", "sql"]
                }
            },
            "required": ["code"]
        }
    }
}
