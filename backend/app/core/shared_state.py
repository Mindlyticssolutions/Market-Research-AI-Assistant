"""
Shared State for Local/Mock Mode
Stores file metadata and content snippets to simulate a retriever when Azure services are not configured.
"""
from typing import Dict, Any, List
from datetime import datetime

class SharedStateManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedStateManager, cls).__new__(cls)
            cls._instance.files = {} # id -> FileInfo mapping
            cls._instance.file_content_preview = {} # id -> content/headers preview
        return cls._instance

    def add_file(self, file_id: str, file_info: Any, preview: str = ""):
        self.files[file_id] = file_info
        self.file_content_preview[file_id] = preview
        print(f"[Mock] Added file {file_info.filename} to shared state")

    def get_file(self, file_id: str):
        return self.files.get(file_id)

    def list_files(self):
        return list(self.files.values())

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Mock search that matches query against filenames"""
        results = []
        query_lower = query.lower()
        
        for fid, info in self.files.items():
            # Simple match: if query is in filename or filename in query
            if query_lower in info.filename.lower() or info.filename.lower() in query_lower:
                results.append({
                    "title": info.filename,
                    "source": info.filename,
                    "chunk_id": fid,
                    "content": "[METADATA ONLY]", # Keep strict metadata only
                    "metadata_storage_name": info.filename,
                    "score": 1.0,
                    # We inject headers into the title or source text for the agent to see? 
                    # No, the agent needs columns.
                    # The prompt says: "You have access to the file's metadata...".
                    # Let's append the preview (headers) to the 'title' or a custom field if the agent supports it?
                    # The RAGRetriever usually returns 'content'.
                    # If we hide content, we must put schema info SOMEWHERE.
                    # Let's put it in 'metadata_storage_name' or a special formatted title?
                    # Or, better: modify the 'content' placeholder to include schema only.
                    # content: "[METADATA] Schema: col1, col2, col3..."
                })
        
        return results

    def get_preview(self, filename: str) -> str:
        for fid, info in self.files.items():
            if info.filename == filename:
                return self.file_content_preview.get(fid, "")
        return ""

shared_state = SharedStateManager()
