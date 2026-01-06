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
        self._initialization_error = None
        
        # Validate configuration
        if not self.endpoint:
            self._initialization_error = "AZURE_OPENAI_ENDPOINT is not configured"
            print(f"❌ Azure OpenAI Config Error: {self._initialization_error}")
        if not self.api_key:
            self._initialization_error = "AZURE_OPENAI_API_KEY is not configured"
            print(f"❌ Azure OpenAI Config Error: {self._initialization_error}")
        if not self.deployment:
            self._initialization_error = "AZURE_OPENAI_DEPLOYMENT is not configured"
            print(f"❌ Azure OpenAI Config Error: {self._initialization_error}")
        
        if not self._initialization_error:
            print(f"✅ Azure OpenAI Client initialized:")
            print(f"   Endpoint: {self.endpoint}")
            print(f"   Deployment: {self.deployment}")
            print(f"   API Version: {self.api_version}")
    
    @classmethod
    def get_instance(cls) -> "AzureAIFoundryClient":
        """Singleton pattern for client"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @property
    def client(self) -> AsyncAzureOpenAI:
        """Get or create OpenAI client"""
        if self._initialization_error:
            raise Exception(f"Azure OpenAI client not initialized: {self._initialization_error}")
            
        if self._client is None:
            try:
                self._client = AsyncAzureOpenAI(
                    azure_endpoint=self.endpoint,
                    api_key=self.api_key,
                    api_version=self.api_version
                )
                print(f"✅ AsyncAzureOpenAI client created successfully")
            except Exception as e:
                error_msg = f"Failed to create Azure OpenAI client: {str(e)}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
        return self._client
    
    async def chat_completion(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Get chat completion from Azure OpenAI"""
        try:
            # Convert to OpenAI message format if needed
            formatted_messages = []
            for msg in messages:
                if hasattr(msg, 'content'):
                    # It's a Message object
                    role = 'system' if 'System' in type(msg).__name__ else 'user'
                    formatted_messages.append({"role": role, "content": msg.content})
                else:
                    # Already a dict
                    formatted_messages.append(msg)
            
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"Azure OpenAI error with deployment '{self.deployment}': {str(e)}"
            print(f"❌ {error_msg}")
            # Check for common errors
            if "DeploymentNotFound" in str(e) or "deployment" in str(e).lower():
                error_msg += f"\n💡 Tip: Verify deployment name '{self.deployment}' exists in Azure OpenAI Studio"
            raise Exception(error_msg)
    
    async def simple_chat(self, user_message: str, system_message: str = None) -> str:
        """Simple chat interface"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})
        
        return await self.chat_completion(messages)


def get_ai_client() -> AzureAIFoundryClient:
    """Dependency injection for AI client"""
    return AzureAIFoundryClient.get_instance()
