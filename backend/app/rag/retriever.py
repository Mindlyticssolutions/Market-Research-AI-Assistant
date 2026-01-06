"""
RAG Retriever (LangChain Version)
Uses Azure AI Search via LangChain for document retrieval
"""
from typing import List, Dict, Any, Optional
import asyncio
from langchain_community.vectorstores import AzureSearch
from langchain_openai import AzureOpenAIEmbeddings
from app.core.config import settings

class RAGRetriever:
    """
    Retriever for RAG using Azure AI Search via LangChain
    """
    
    def __init__(self):
        self.endpoint = settings.AZURE_SEARCH_ENDPOINT
        self.key = settings.AZURE_SEARCH_KEY
        self.index_name = settings.AZURE_SEARCH_INDEX_NAME
        
        # Initialize Embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            openai_api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        
        # Initialize Vector Store
        self.vector_store = AzureSearch(
            azure_search_endpoint=self.endpoint,
            azure_search_key=self.key,
            index_name=self.index_name,
            embedding_function=self.embeddings
        )
    
    @property
    def client(self):
        """Expose vector store as client (compatibility)"""
        return self.vector_store

    async def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        use_vector: bool = True
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents asynchronously using LangChain"""
        
        try:
            # Define search wrapper
            def _run_search():
                # Perform similarity search
                # LangChain returns List[Document]
                docs = self.vector_store.similarity_search(query, k=top_k)
                return docs
            
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, _run_search)
            
            # Format results and ENFORCE METADATA ONLY
            results = []
            for doc in docs:
                # doc.page_content contains the text. We HIDE IT.
                # doc.metadata contains title, source, chunk_id
                
                metadata = doc.metadata or {}
                
                results.append({
                    "content": doc.page_content, # Content allowed
                    "title": metadata.get("title", "Unknown"),
                    "source": metadata.get("source", ""),
                    "file_id": metadata.get("file_id", ""),
                    "file_name": metadata.get("file_name", metadata.get("title", "Unknown")),
                    "chunk_id": metadata.get("chunk_id", ""),
                    "score": 1.0 # LangChain similarity_search doesn't always return score unless using search_with_score
                })
            
            return results
            
        except Exception as e:
            print(f"RAG retrieval error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def search_text(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Simple text search"""
        return await self.retrieve(query, top_k=top_k)
    
    def health_check(self) -> bool:
        """Check if configured"""
        return True
