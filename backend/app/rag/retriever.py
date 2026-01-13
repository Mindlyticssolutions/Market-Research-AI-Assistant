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
        self.embeddings = None
        self.vector_store = None
        self._initialized = False
        
        try:
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
            self._initialized = True
        except Exception as e:
            print(f"DEBUG: [RAGRetriever] Initialization error: {e}")
            self._initialized = False
    
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
        
        if not self._initialized or not self.vector_store:
            print("DEBUG: [RAGRetriever] Not initialized, returning empty results")
            return []
        
        try:
            # Define search wrapper
            def _run_search():
                print(f"DEBUG: [RAGRetriever] Starting internal similarity_search for query: {query[:50]}...")
                try:
                    # Perform similarity search
                    # LangChain returns List[Document]
                    docs = self.vector_store.similarity_search(query, k=top_k)
                    print(f"DEBUG: [RAGRetriever] similarity_search complete. Returned {len(docs) if docs else 0} docs.")
                    return docs if docs else []
                except Exception as search_err:
                    print(f"DEBUG: [RAGRetriever] similarity_search error: {search_err}")
                    return []
            
            print(f"DEBUG: [RAGRetriever] Running search in executor...")
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, _run_search)
            print(f"DEBUG: [RAGRetriever] Executor returned.")
            
            if not docs:
                return []
            
            # Format results and ENFORCE METADATA ONLY
            results = []
            for doc in docs:
                # doc.page_content contains the text. We HIDE IT.
                # doc.metadata contains title, source, chunk_id
                
                metadata = doc.metadata or {}
                
                results.append({
                    "content": "[METADATA ONLY]", # STRICT SECURITY POLICY
                    "title": metadata.get("title", "Unknown"),
                    "source": metadata.get("source", ""),
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
