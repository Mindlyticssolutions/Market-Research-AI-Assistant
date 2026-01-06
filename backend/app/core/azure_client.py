"""
Azure AI Foundry Client
Wrapper for Azure OpenAI operations using the openai library
"""
from typing import Optional, List
from openai import AsyncAzureOpenAI

from app.core.config import settings


class AzureAIFoundryClient:
    """Client for Azure OpenAI operations"""
    
    _instance: Optional["AzureAIFoundryClient"] = None
    
    def __init__(self):
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT.rstrip('/')
        self.api_key = settings.AZURE_OPENAI_API_KEY
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
        self.api_version = settings.AZURE_OPENAI_API_VERSION
        self._client = None
    
    @classmethod
    def get_instance(cls) -> "AzureAIFoundryClient":
        """Singleton pattern for client"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @property
    def client(self) -> AsyncAzureOpenAI:
        """Get or create OpenAI client"""
        if self._client is None:
            self._client = AsyncAzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.api_version
            )
        return self._client
    
    def _format_tools(self, tools: List[dict]) -> List[dict]:
        """Format expanded or simplified tools to OpenAI schema"""
        if not tools:
            return None
            
        formatted_tools = []
        for tool in tools:
            # 1. If already in full OpenAI function format, use as is
            if "type" in tool and tool["type"] == "function":
                formatted_tools.append(tool)
                continue
            
            # 2. Extract components
            name = tool.get("name")
            description = tool.get("description", "")
            parameters = tool.get("parameters", {})
            
            # 3. Determine if parameters is already a JSON schema or a simple dict
            if isinstance(parameters, dict) and parameters.get("type") == "object":
                # It's already a full JSON schema
                final_params = parameters
            else:
                # Convert simple dict {name: type} to JSON schema
                properties = {}
                required = []
                for key, value in parameters.items():
                    # Handle simple types (string, int, etc)
                    if isinstance(value, str):
                        prop_type = "string"
                        if value in ["int", "integer"]: prop_type = "integer"
                        elif value == "float": prop_type = "number"
                        elif value in ["bool", "boolean"]: prop_type = "boolean"
                        elif value == "list": prop_type = "array"
                        elif value == "dict": prop_type = "object"
                        properties[key] = {"type": prop_type}
                    else:
                        # Value is already a schema fragment (e.g. {"type": "string", "enum": [...]})
                        properties[key] = value
                    required.append(key)
                
                final_params = {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }

            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": final_params
                }
            })
        return formatted_tools

    async def chat_completion(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        """Get chat completion from Azure OpenAI"""
        try:
            # Convert to OpenAI message format if needed
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    formatted_messages.append(msg)
                elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                    # Pydantic models or OpenAI message objects
                    formatted_messages.append({
                        "role": msg.role,
                        "content": msg.content,
                        "tool_calls": getattr(msg, 'tool_calls', None)
                    })
                elif hasattr(msg, 'content'):
                    # Fallback for simpler message objects
                    msg_type = type(msg).__name__.lower()
                    if 'system' in msg_type:
                        role = 'system'
                    elif 'assistant' in msg_type:
                        role = 'assistant'
                    elif 'tool' in msg_type:
                        role = 'tool'
                    else:
                        role = 'user'
                    formatted_messages.append({"role": role, "content": msg.content})
                else:
                    formatted_messages.append(msg)
            
            # Format tools if present
            tools = kwargs.get('tools')
            formatted_tools = self._format_tools(tools) if tools else None

            print(f"DEBUG: [AzureClient] Sending {len(formatted_messages)} messages with {len(formatted_tools) if formatted_tools else 0} tools")
            
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=formatted_tools,
                tool_choice=kwargs.get('tool_choice', 'auto') if formatted_tools else None
            )
            
            msg = response.choices[0].message
            print(f"DEBUG: [AzureClient] Response role: {msg.role}, has_content: {bool(msg.content)}, has_tools: {bool(msg.tool_calls)}")
            return msg
        except Exception as e:
            print(f"DEBUG: [AzureClient] Error: {str(e)}")
            raise Exception(f"Azure OpenAI error: {str(e)}")

    def parse_tool_calls(self, response_message):
        """Extract tool calls from response message"""
        if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
            print(f"DEBUG: [AzureClient] Parsed {len(response_message.tool_calls)} tool calls")
            return response_message.tool_calls
        return None
    
    async def simple_chat(self, user_message: str, system_message: str = None) -> str:
        """Simple chat interface"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})
        
        response = await self.chat_completion(messages)
        return response.content if hasattr(response, 'content') else str(response)


def get_ai_client() -> AzureAIFoundryClient:
    """Dependency injection for AI client"""
    return AzureAIFoundryClient.get_instance()
