"""
Blob Storage Retriever
======================
Retrieves file metadata directly from Azure Blob Storage.
Used to give agents a "source of truth" regarding available files,
independent of the search index.
"""
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from app.core.config import settings

class BlobRetriever:
    """
    Retriever for direct Azure Blob Storage metadata access.
    """
    
    def __init__(self):
        self.conn_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER
        self._client = None
        self._container_client = None
        self._initialized = False
        
        try:
            if self.conn_string:
                self._client = BlobServiceClient.from_connection_string(self.conn_string)
                self._container_client = self._client.get_container_client(self.container_name)
                self._initialized = True
        except Exception as e:
            print(f"DEBUG: [BlobRetriever] Initialization error: {e}")
            self._initialized = False

    def health_check(self) -> bool:
        """Check if connected to Blob Storage"""
        try:
            if not self._initialized or not self._container_client:
                return False
            return self._container_client.exists()
        except:
            return False

    async def list_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all files in the container with metadata"""
        if not self._initialized:
            return []
            
        try:
            # Azure SDK is synchronous, so we run in executor for async compatibility
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._list_blobs_sync, limit, None)
        except Exception as e:
            print(f"DEBUG: [BlobRetriever] Error listing blobs: {e}")
            return []

    async def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve files matching the query from Blob Storage.
        Since Blob Storage doesn't support full-text search on content,
        this performs a client-side filter on filenames and metadata.
        """
        if not self._initialized:
            return []
            
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._list_blobs_sync, top_k, query)
        except Exception as e:
            print(f"DEBUG: [BlobRetriever] Error retrieving blobs: {e}")
            return []
            
    def _list_blobs_sync(self, limit: int, query: Optional[str]) -> List[Dict[str, Any]]:
        """Synchronous internal method to list and filter blobs"""
        if not self._container_client:
            return []
            
        results = []
        try:
            # List blobs with metadata
            # Note: listing all blobs can be slow if there are thousands
            # We assume a reasonable number for this specific use case
            blobs = self._container_client.list_blobs(include=["metadata"])
            
            count = 0
            for blob in blobs:
                # Basic filtering logic
                match = True
                if query and query != "*":
                    # clear quotes
                    clean_query = query.lower().strip('"\'')
                    # Check filename
                    name_match = clean_query in blob.name.lower()
                    
                    # Check metadata tags if any
                    meta_match = False
                    if blob.metadata:
                        for v in blob.metadata.values():
                            if v and clean_query in str(v).lower():
                                meta_match = True
                                break
                    
                    if not (name_match or meta_match):
                        match = False
                
                if match:
                    # Format result straight away
                    meta = blob.metadata or {}
                    
                    # Calculate relevance score (fake)
                    score = 1.0 if query and query.lower() in blob.name.lower() else 0.5
                    
                    results.append({
                        "file_id": meta.get("file_id", "unknown"),
                        "filename": meta.get("filename", blob.name.split("/")[-1]),
                        "status": meta.get("status", "unknown"),
                        "uploaded_at": meta.get("uploaded_at", ""),
                        "blob_name": blob.name,
                        "size": blob.size,
                        # Standardize keys for DataAccessLayer
                        "title": meta.get("filename", blob.name.split("/")[-1]),
                        "source": "Azure Blob Storage",
                        "score": score
                    })
                    count += 1
                    
                if count >= limit:
                    break
                    
            return results
            
        except Exception as e:
            print(f"DEBUG: [BlobRetriever] Sync list error: {e}")
            return []
