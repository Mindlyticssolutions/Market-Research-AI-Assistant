"""
Secure Data Access Layer
========================
This is the ONLY way agents can access data in the system.

SECURITY POLICY:
- Agents can ONLY access METADATA (file names, column names, data types)
- Agents CANNOT access actual data content or values
- All data access goes through RAG (Azure AI Search) and KAG (Cosmos DB)

No direct file system access, no direct database queries.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class DataSource(Enum):
    """Enumeration of allowed data sources"""
    RAG = "rag"  # Azure AI Search
    KAG = "kag"  # Cosmos DB Gremlin
    BLOB = "blob" # Azure Blob Storage


@dataclass
class RetrievedData:
    """Standard format for retrieved data - METADATA ONLY"""
    source: DataSource
    metadata: Dict[str, Any]
    score: float = 0.0
    # Content is intentionally REMOVED - agents only get metadata
    
    def __str__(self) -> str:
        source_label = "Document"
        if self.source == DataSource.KAG:
            source_label = "Knowledge Graph"
        elif self.source == DataSource.BLOB:
            source_label = "Blob Storage"
            
        title = self.metadata.get("title", self.metadata.get("filename", "Unknown"))
        return f"[{source_label}] {title}"
    
    def get_metadata_summary(self) -> str:
        """Get a summary of metadata without any actual data content"""
        parts = []
        if self.metadata.get("filename"):
            parts.append(f"File: {self.metadata['filename']}")
        if self.metadata.get("title"):
            parts.append(f"Title: {self.metadata['title']}")
        if self.metadata.get("columns"):
            parts.append(f"Columns: {', '.join(self.metadata['columns'])}")
        if self.metadata.get("row_count"):
            parts.append(f"Rows: {self.metadata['row_count']}")
        if self.metadata.get("file_type"):
            parts.append(f"Type: {self.metadata['file_type']}")
        if self.metadata.get("label"):
            parts.append(f"Label: {self.metadata['label']}")
        if self.metadata.get("properties"):
             # Only show property keys, NOT values
            keys = list(self.metadata['properties'].keys())
            parts.append(f"Properties: {', '.join(keys)}")
            
        return " | ".join(parts) if parts else str(self.metadata)


@dataclass
class DataAccessResult:
    """Result from data access layer - METADATA ONLY"""
    rag_results: List[RetrievedData]
    kag_results: List[RetrievedData]
    blob_results: List[RetrievedData]
    sources_used: List[str]
    
    @property
    def has_data(self) -> bool:
        return len(self.rag_results) > 0 or len(self.kag_results) > 0 or len(self.blob_results) > 0
    
    def get_context_text(self, max_results: int = 5) -> str:
        """Get formatted context text for LLM - METADATA ONLY, NO DATA CONTENT"""
        context_parts = [
            "=== AVAILABLE DATA METADATA (NO ACTUAL DATA VALUES) ==="
        ]
        
        if self.rag_results:
            context_parts.append("\n📁 Uploaded Documents:")
            for result in self.rag_results[:max_results]:
                context_parts.append(f"  - {result.get_metadata_summary()}")
        
        if self.kag_results:
            context_parts.append("\n🔗 Knowledge Graph Entities:")
            for result in self.kag_results[:max_results]:
                context_parts.append(f"  - {result.get_metadata_summary()}")

        if self.blob_results:
            context_parts.append("\n💾 Blob Storage Files (Raw Metadata):")
            for result in self.blob_results[:max_results]:
                context_parts.append(f"  - {result.get_metadata_summary()}")
        
        context_parts.append("\n⚠️ NOTE: You can only see metadata above. You do NOT have access to actual data values.")
        
        if not self.rag_results and not self.kag_results and not self.blob_results:
            return "No data metadata found. Ask user to upload documents first."
        
        return "\n".join(context_parts)


class DataAccessLayer:
    """
    Secure Data Access Layer - Singleton
    =====================================
    
    This class is the ONLY interface for agents to access data.
    It enforces that all data access goes through:
    - RAG (Retrieval-Augmented Generation via Azure AI Search)
    - KAG (Knowledge-Augmented Generation via Cosmos DB Gremlin)
    
    No file system access. No direct database queries.
    """
    
    _instance: Optional["DataAccessLayer"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._rag_retriever = None
        self._kag_retriever = None
        self._blob_retriever = None
        self._access_log: List[Dict[str, Any]] = []
        self._initialized = True
    
    @property
    def rag_retriever(self):
        """Lazy load RAG retriever (Azure AI Search)"""
        if self._rag_retriever is None:
            try:
                from app.rag.retriever import RAGRetriever
                self._rag_retriever = RAGRetriever()
            except Exception as e:
                print(f"[DataAccessLayer] RAG retriever not available: {e}")
        return self._rag_retriever
    
    @property
    def kag_retriever(self):
        """Lazy load KAG retriever (Cosmos DB Gremlin)"""
        if self._kag_retriever is None:
            try:
                from app.kag.graph_retriever import KAGRetriever
                self._kag_retriever = KAGRetriever()
            except Exception as e:
                print(f"[DataAccessLayer] KAG retriever not available: {e}")
        return self._kag_retriever
    
    @property
    def blob_retriever(self):
        """Lazy load Blob retriever"""
        if self._blob_retriever is None:
            try:
                from app.blob.retriever import BlobRetriever
                self._blob_retriever = BlobRetriever()
            except Exception as e:
                print(f"[DataAccessLayer] Blob retriever not available: {e}")
        return self._blob_retriever
    
    def _log_access(self, query: str, sources: List[DataSource], result_count: int):
        """Log data access for auditing"""
        import datetime
        self._access_log.append({
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "query": query[:100],  # Truncate for log
            "sources": [s.value for s in sources],
            "result_count": result_count
        })
        print(f"[DataAccessLayer] Access logged: query='{query[:50]}...' sources={[s.value for s in sources]} results={result_count}")
    
    async def retrieve(
        self, 
        query: str, 
        use_rag: bool = True, 
        use_kag: bool = True,
        use_blob: bool = True,
        top_k: int = 5
    ) -> DataAccessResult:
        """
        Retrieve data from RAG and/or KAG systems.
        
        This is the ONLY method agents should use to access data.
        
        Args:
            query: Search query
            use_rag: Whether to search Azure AI Search (RAG)
            use_kag: Whether to search Cosmos DB Gremlin (KAG)
            use_blob: Whether to search Blob Storage directly (Metadata)
            top_k: Maximum results per source
            
        Returns:
            DataAccessResult with attributed results from each source
        """
        rag_results: List[RetrievedData] = []
        kag_results: List[RetrievedData] = []
        blob_results: List[RetrievedData] = []
        sources_used: List[str] = []
        
        # 0. Fetch active blobs first to use as "Source of Truth"
        active_file_ids = set()
        if self.blob_retriever:
            try:
                # Get all blobs to cross-reference
                all_blobs = await self.blob_retriever.list_all(limit=1000)
                active_file_ids = {b.get("file_id") for b in all_blobs if b.get("file_id")}
                # Also include these in the results if it's a general search or matches
                for result in all_blobs:
                    # Basic match for blob results if query is provided
                    if not query or query == "*" or query.lower() in result.get("filename", "").lower():
                         blob_results.append(RetrievedData(
                            source=DataSource.BLOB,
                            metadata={
                                "filename": result.get("filename", ""),
                                "file_id": result.get("file_id", ""),
                                "status": result.get("status", ""),
                                "uploaded_at": result.get("uploaded_at", ""),
                                "size": result.get("size", 0),
                                "title": result.get("filename", "") 
                            },
                            score=result.get("score", 0.0)
                        ))
                if blob_results:
                    sources_used.append("Azure Blob Storage")
            except Exception as e:
                print(f"[DataAccessLayer] Initial blob list error: {e}")

        # 1. Retrieve from RAG (Azure AI Search)
        if use_rag and self.rag_retriever:
            try:
                raw_results = await self.rag_retriever.retrieve(query, top_k=top_k)
                for result in raw_results:
                    file_id = result.get("file_id", "")
                    
                    # STRICT FILTER: Only show if file still exists in Blob Storage
                    if file_id and file_id not in active_file_ids:
                        print(f"[DataAccessLayer] Hiding deleted file from RAG: {result.get('title')} ({file_id})")
                        continue

                    # STRIPPING CONTENT - METADATA ONLY
                    rag_results.append(RetrievedData(
                        source=DataSource.RAG,
                        # content field removed
                        metadata={
                            "title": result.get("title", "Unknown"),
                            "source": result.get("source", ""),
                            "chunk_id": result.get("chunk_id", ""),
                            "file_id": file_id
                        },
                        score=result.get("score", 0.0)
                    ))
                if rag_results:
                    sources_used.append("Azure AI Search (RAG)")
            except Exception as e:
                print(f"[DataAccessLayer] RAG retrieval error: {e}")
        
        # Retrieve from KAG (Cosmos DB Gremlin)
        if use_kag and self.kag_retriever:
            try:
                raw_results = await self.kag_retriever.retrieve(query, top_k=top_k)
                for result in raw_results:
                    # STRIPPING CONTENT - METADATA ONLY
                    kag_results.append(RetrievedData(
                        source=DataSource.KAG,
                        # content field removed
                        metadata={
                            "id": result.get("id", ""),
                            "label": result.get("label", ""),
                            "properties": result.get("properties", {}) 
                        },
                        score=0.0
                    ))
                if kag_results:
                    sources_used.append("Cosmos DB Gremlin (KAG)")
            except Exception as e:
                print(f"[DataAccessLayer] KAG retrieval error: {e}")
        
        # Log access
        sources_queried = []
        if use_rag:
            sources_queried.append(DataSource.RAG)
        if use_kag:
            sources_queried.append(DataSource.KAG)
        if use_blob:
            sources_queried.append(DataSource.BLOB)
        self._log_access(query, sources_queried, len(rag_results) + len(kag_results) + len(blob_results))
        
        return DataAccessResult(
            rag_results=rag_results,
            kag_results=kag_results,
            blob_results=blob_results,
            sources_used=sources_used
        )
    
    async def search_documents(self, query: str, top_k: int = 5) -> DataAccessResult:
        """Search uploaded documents only (RAG)"""
        return await self.retrieve(query, use_rag=True, use_kag=False, top_k=top_k)
    
    async def search_knowledge_graph(self, query: str, top_k: int = 10) -> DataAccessResult:
        """Search knowledge graph only (KAG)"""
        return await self.retrieve(query, use_rag=False, use_kag=True, top_k=top_k)

    async def list_all_files(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all files directly from Blob Storage"""
        if self.blob_retriever:
            return await self.blob_retriever.list_all(limit=limit)
        return []
    
    def get_access_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent data access log for auditing"""
        return self._access_log[-limit:]
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of data access systems"""
        return {
            "rag_available": self.rag_retriever is not None and self.rag_retriever.health_check() if self.rag_retriever else False,
            "kag_available": self.kag_retriever is not None and self.kag_retriever.health_check() if self.kag_retriever else False,
            "blob_available": self.blob_retriever is not None and self.blob_retriever.health_check() if self.blob_retriever else False
        }


# Singleton instance
_data_access_layer: Optional[DataAccessLayer] = None


def get_data_access_layer() -> DataAccessLayer:
    """Get the singleton DataAccessLayer instance"""
    global _data_access_layer
    if _data_access_layer is None:
        _data_access_layer = DataAccessLayer()
    return _data_access_layer
