
import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

def load_env():
    from dotenv import load_dotenv
    env_path = os.path.join(os.getcwd(), 'backend', '.env')
    print(f"Loading .env from: {env_path}")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(".env loaded successfully")
    else:
        print(f"WARNING: .env not found at {env_path}")

async def test_azure_openai():
    load_env()
    print("Testing Azure OpenAI Connectivity...")
    try:
        from app.core.config import settings
        from app.core.azure_client import get_ai_client
        
        print(f"Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
        print(f"Deployment: {settings.AZURE_OPENAI_DEPLOYMENT}")
        print(f"API Version: {settings.AZURE_OPENAI_API_VERSION}")
        print(f"API Key present: {bool(settings.AZURE_OPENAI_API_KEY)}")
        
        tools = [
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
        
        client = get_ai_client()
        print("Sending test message with tools...")
        response = await client.chat_completion(messages=messages, tools=tools, max_tokens=50)
        print(f"Response role: {response.role}")
        print(f"Response content: {response.content}")
        print(f"Tool calls: {client.parse_tool_calls(response)}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_azure_openai())
