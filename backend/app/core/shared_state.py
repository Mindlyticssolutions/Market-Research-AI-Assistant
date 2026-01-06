"""
Shared State for Local/Mock Mode
Stores file metadata and content snippets to simulate a retriever when Azure services are not configured.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

class FileInfo(BaseModel):
    """File information model"""
    id: str
    filename: str
    file_type: str
    size: int
    uploaded_at: datetime
    status: str  # pending, processing, indexed, failed
    blob_url: Optional[str] = None
    chunks_indexed: Optional[int] = None

class SharedStateManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedStateManager, cls).__new__(cls)
            cls._instance.files: Dict[str, FileInfo] = {} # id -> FileInfo mapping
            cls._instance.file_content_preview = {} # id -> content/headers preview
            cls._instance._load_state()
        return cls._instance

    def _get_storage_path(self):
        import tempfile
        import os
        return os.path.join(tempfile.gettempdir(), "ai_assistant_shared_state.json")

    def _load_state(self):
        import json
        import os
        path = self._get_storage_path()
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    for fid, f_data in data.items():
                        # Convert string dates back to datetime objects if needed
                        # Pydantic handles initialization from dict
                        self.files[fid] = FileInfo(**f_data)
                print(f"[SharedState] Restored {len(self.files)} files from persistence.")
            except Exception as e:
                print(f"[SharedState] Error loading state: {e}")

    def _save_state(self):
        import json
        try:
            path = self._get_storage_path()
            # Convert QueryDict/FileInfo objects to dicts using .dict() or .model_dump()
            data = {fid: info.dict() for fid, info in self.files.items()}
            # Serialize datetime objects
            with open(path, 'w') as f:
                json.dump(data, f, default=str, indent=2)
        except Exception as e:
            print(f"[SharedState] Error saving state: {e}")

    def add_file(self, file_id: str, file_info: FileInfo):
        self.files[file_id] = file_info
        self._save_state() # Persist immediately
        print(f"[SharedState @ {id(self)}] Added file {file_info.filename}. Total: {len(self.files)}")

    def get_file(self, file_id: str) -> Optional[FileInfo]:
        return self.files.get(file_id)

    def list_files(self) -> List[FileInfo]:
        # print(f"[SharedState @ {id(self)}] Listing {len(self.files)} files.") # Reduce noise
        return list(self.files.values())

    def remove_file(self, file_id: str):
        if file_id in self.files:
            del self.files[file_id]
            self._save_state() # Persist immediately
            print(f"[SharedState] Removed file {file_id}")

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Mock search that matches query against filenames"""
        results = []
        query_lower = query.lower()
        
        for fid, info in self.files.items():
            if query_lower in info.filename.lower() or info.filename.lower() in query_lower:
                results.append({
                    "title": info.filename,
                    "source": info.filename,
                    "chunk_id": fid,
                    "content": "[METADATA ONLY]", 
                    "metadata_storage_name": info.filename,
                    "score": 1.0,
                })
        
        return results

    def get_preview(self, filename: str) -> str:
        for fid, info in self.files.items():
            if info.filename == filename:
                return self.file_content_preview.get(fid, "")
        return ""

shared_state = SharedStateManager()
