import asyncio
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables from .env
env_path = os.path.join(project_root, "backend", ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

# Correct path for backend imports
sys.path.insert(0, os.path.join(project_root, "backend"))

async def test_agent_handoff():
    print("Initializing AgentRegistry...")
    from agents.registry import AgentRegistry
    AgentRegistry.initialize()
    
    # Test through Orchestrator to see handoff
    agent = AgentRegistry.get_agent("orchestrator")
    if not agent:
        print("Error: OrchestratorAgent not found in registry!")
        return
        
    print(f"Agent found: {agent.name}")
    
    async def callback(event_type, content):
        print(f"EVENT [{event_type}]: {content}")
        
    query = "Calculate the 10th Fibonacci number using Python"
    print(f"Executing query: {query}")
    
    # This should trigger routing to Python Agent and then Python Agent execution
    result = await agent.execute(query, context={}, callback=callback)
    
    print("\n--- FINAL RESPONSE FROM AGENT ---")
    print(f"Agent Name: {result.agent_name}")
    print(f"Content: {result.content}")
    print(f"Success: {result.success}")
    if result.error:
        print(f"ERROR: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_agent_handoff())
