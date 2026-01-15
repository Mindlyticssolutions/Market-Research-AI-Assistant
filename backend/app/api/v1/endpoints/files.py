"""
File Upload and Management Endpoints
Supports both structured and unstructured data
Files are uploaded to Azure Blob Storage and indexed into RAG
"""
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import uuid
import asyncio

from azure.storage.blob import BlobServiceClient
from app.core.config import settings

router = APIRouter()


# All files are supported now
# Text-extractable extensions for specific handling


# Text-extractable extensions
TEXT_EXTENSIONS = {"txt", "md", "rst", "csv", "json", "xml", "yaml", "yml", "html", "htm","xlsx"}


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


class UploadResponse(BaseModel):
    """Upload response model"""
    message: str
    file_id: str
    filename: str
    status: str
    blob_url: Optional[str] = None


# In-memory storage for demo (replace with database in production)
#files_store: dict[str, FileInfo] = {}



async def _upload_to_blob(filename: str, content: bytes, file_id: str, metadata: dict = None) -> str:
    """Upload file content to Azure Blob Storage with metadata"""
    try:
        if not settings.AZURE_STORAGE_CONNECTION_STRING:
            print("Warning: Azure Storage not configured")
            return ""

        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER)
        
        # Create container if not exists
        if not container_client.exists():
            container_client.create_container()

        # Use file_id prefix to avoid collisions
        blob_name = f"{file_id}/{filename}"
        blob_client = container_client.get_blob_client(blob_name)
        
        blob_client.upload_blob(content, overwrite=True, metadata=metadata)
        return blob_client.url
    except Exception as e:
        print(f"Blob upload error: {e}")
        return ""


async def _extract_text_content(content: bytes, ext: str) -> str:
    """Extract text content from file based on extension"""
    try:
        if ext in TEXT_EXTENSIONS:
            return content.decode('utf-8', errors='ignore')
        
        if ext == "pdf":
            try:
                from pypdf import PdfReader
                import io
                reader = PdfReader(io.BytesIO(content))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
            except Exception as e:
                print(f"PDF extraction error: {e}")
                return ""
        
        if ext in ("docx", "doc"):
            try:
                from docx import Document
                import io
                doc = Document(io.BytesIO(content))
                return "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                print(f"DOCX extraction error: {e}")
                return ""
        
        if ext in ("xlsx", "xls"):
            try:
                import pandas as pd
                import io
                df = pd.read_excel(io.BytesIO(content))
                return df.to_string()
            except Exception as e:
                print(f"Excel extraction error: {e}")
                return ""
        
        # For other types, try basic decode or return placeholder
        try:
             return content.decode('utf-8')
        except:
             return "[Binary/Unknown File Content]"
        
    except Exception as e:
        print(f"Text extraction error: {e}")
        return "[Error extraction content]"


async def _process_and_index_file(file_id: str, content: bytes, ext: str, filename: str, blob_url: str):
    """Background task to process and index file into RAG"""
    try:
        # Update status to processing in Blob Metadata
        try:
            blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
            container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER)
            blob_name = f"{file_id}/{filename}"
            blob_client = container_client.get_blob_client(blob_name)
            
            # Fetch current metadata, update, and set back
            meta = blob_client.get_blob_properties().metadata
            meta["status"] = "processing"
            blob_client.set_blob_metadata(meta)
        except Exception as e:
            print(f"Error updating blob metadata to processing: {e}")
        
        # Extract text content
        text_content = await _extract_text_content(content, ext)
        
        if not text_content:
             text_content = f"Filename: {filename} (Content not extractable)"
             
        # Prepare title with schema for CSVs
        display_title = filename
        if ext == 'csv':
            try:
                 lines = text_content.split('\n')
                 if lines:
                     header = lines[0].strip()
                     # Truncate if too long (Azure Limit)
                     if len(header) > 200:
                         header = header[:197] + "..."
                     display_title = f"{filename} (Schema: {header})"
            except:
                 pass

        # Index into RAG
        try:
            from app.rag.indexer import RAGIndexer
            indexer = RAGIndexer()
            result = await indexer.index_document(
                file_id=file_id,
                content=text_content,
                title=display_title, # Pass enriched title
                source=blob_url or filename
            )
            
            # Update status in Blob Metadata
            try:
                meta = blob_client.get_blob_properties().metadata
                if result.get("success"):
                    meta["status"] = "indexed"
                    meta["chunks_indexed"] = str(result.get("chunks_indexed", 0))
                else:
                    meta["status"] = "failed"
                blob_client.set_blob_metadata(meta)
            except Exception as e:
                print(f"Error updating final blob metadata: {e}")
                    
        except Exception as e:
            print(f"Indexing error: {e}")
            try:
                meta = blob_client.get_blob_properties().metadata
                meta["status"] = "failed"
                blob_client.set_blob_metadata(meta)
            except: pass
                
    except Exception as e:
        print(f"Processing error: {e}")


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload file to Azure Blob Storage and Index to RAG
    1. Uploads to Blob Storage (uploads container)
    2. Extracts text
    3. Indexes to Azure AI Search (Vector DB)
    """
    # Validate file extension - OK, allowing all
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""

    # Generate file ID
    file_id = str(uuid.uuid4())
    
    # Read content
    content = await file.read()
    size = len(content)
    
    # Prepare metadata for storage
    metadata = {
        "file_id": file_id,
        "filename": file.filename,
        "file_type": ext,
        "size": str(size),
        "uploaded_at": datetime.utcnow().isoformat(),
        "status": "pending"
    }
    
    # Upload to Blob Storage with metadata
    blob_url = await _upload_to_blob(file.filename, content, file_id, metadata=metadata)
    
    # Add background task for processing and indexing
    background_tasks.add_task(
        _process_and_index_file,
        file_id,
        content,
        ext,
        file.filename,
        blob_url
    )
    
    return UploadResponse(
        message="File uploaded to Blob Storage, indexing started",
        file_id=file_id,
        filename=file.filename,
        status="pending",
        blob_url=blob_url
    )


@router.get("/list", response_model=List[FileInfo])
async def list_files():
    """List all uploaded files by querying Blob Storage metadata"""
    try:
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER)
        
        if not container_client.exists():
            return []
            
        blobs = container_client.list_blobs(include=["metadata"])
        files = []
        
        for blob in blobs:
            meta = blob.metadata or {}
            # Reconstruct FileInfo
            print(meta.get("file_id", "unknown"), '')
            files.append(FileInfo(
                id=meta.get("file_id", "unknown"),
                filename=meta.get("filename", blob.name.split("/")[-1]),
                file_type=meta.get("file_type", ""),
                size=int(meta.get("size", blob.size)),
                uploaded_at=datetime.fromisoformat(meta.get("uploaded_at")) if meta.get("uploaded_at") else datetime.utcnow(),
                status=meta.get("status", "unknown"),
                blob_url=f"{container_client.url}/{blob.name}",
                chunks_indexed=int(meta.get("chunks_indexed", 0)) if meta.get("chunks_indexed") else None
            ))
            
        return files
    except Exception as e:
        print(f"Error listing files from blob: {e}")
        return []


@router.get("/{file_id}", response_model=FileInfo)
async def get_file(file_id: str):
    """Get file information by ID by searching Blob Storage"""
    # file_id might have quotes from Swagger UI, strip them just in case
    clean_id = file_id.strip('"').strip("'")
    
    try:
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER)
        
        # Blobs are stored as {file_id}/{filename}
        # We need to find the blob starting with this prefix
        blobs = list(container_client.list_blobs(name_starts_with=f"{clean_id}/", include=["metadata"]))
        
        if not blobs:
            raise HTTPException(status_code=404, detail=f"File with ID {clean_id} not found")
            
        blob = blobs[0]
        meta = blob.metadata or {}
        
        print(meta.get("file_id", clean_id))
        return FileInfo(
            id=meta.get("file_id", clean_id),
            filename=meta.get("filename", blob.name.split("/")[-1]),
            file_type=meta.get("file_type", ""),
            size=int(meta.get("size", blob.size)),
            uploaded_at=datetime.fromisoformat(meta.get("uploaded_at")) if meta.get("uploaded_at") else datetime.utcnow(),
            status=meta.get("status", "unknown"),
            blob_url=f"{container_client.url}/{blob.name}",
            chunks_indexed=int(meta.get("chunks_indexed", 0)) if meta.get("chunks_indexed") else None
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching file from blob: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete a file and remove from RAG index and Blob Storage"""
    clean_id = file_id.strip('"').strip("'")
    
    # 1. Remove from RAG index
    try:
        from app.rag.indexer import RAGIndexer
        indexer = RAGIndexer()
        await indexer.delete_document(clean_id)
    except Exception as e:
        print(f"Error removing from RAG: {e}")
    
    # 2. Delete from Blob Storage
    try:
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER)
        
        blobs = container_client.list_blobs(name_starts_with=f"{clean_id}/")
        for blob in blobs:
            container_client.delete_blob(blob.name)
            
    except Exception as e:
        print(f"Error deleting from blob: {e}")
        
    return {"message": "File deleted successfully", "file_id": clean_id}


@router.get("/{file_id}/status")
async def get_file_status(file_id: str):
    """Get file processing status from Blob Storage"""
    file_info = await get_file(file_id)
    return {
        "file_id": file_info.id,
        "filename": file_info.filename,
        "status": file_info.status,
        "chunks_indexed": file_info.chunks_indexed,
        "blob_url": file_info.blob_url,
        "message": f"File is {file_info.status}"
    }
