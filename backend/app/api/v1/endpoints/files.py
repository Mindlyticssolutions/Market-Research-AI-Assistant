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
from app.core.shared_state import shared_state, FileInfo

router = APIRouter()


# All files are supported now
# Text-extractable extensions for specific handling


# Text-extractable extensions
TEXT_EXTENSIONS = {"txt", "md", "rst", "csv", "json", "xml", "yaml", "yml", "html", "htm"}


class UploadResponse(BaseModel):
    """Upload response model"""
    message: str
    file_id: str
    filename: str
    status: str
    blob_url: Optional[str] = None



async def _upload_to_blob(filename: str, content: bytes, file_id: str) -> str:
    """Upload file content to Azure Blob Storage"""
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
        
        blob_client.upload_blob(content, overwrite=True)
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
        # Update status to processing
        file_info = shared_state.get_file(file_id)
        if file_info:
            file_info.status = "processing"
        
        # Extract text content
        text_content = await _extract_text_content(content, ext)
        
        if not text_content:
             text_content = f"Filename: {filename} (Content not extractable)"
             
        # Allow short content (e.g. just filename for binary files)

        
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
            
            if result.get("success"):
                file_info = shared_state.get_file(file_id)
                if file_info:
                    file_info.status = "indexed"
                    file_info.chunks_indexed = result.get("chunks_indexed", 0)
            else:
                file_info = shared_state.get_file(file_id)
                if file_info:
                    file_info.status = "failed"
                    
        except Exception as e:
            print(f"Indexing error: {e}")
            file_info = shared_state.get_file(file_id)
            if file_info:
                file_info.status = "failed"
                
    except Exception as e:
        print(f"Processing error: {e}")
        file_info = shared_state.get_file(file_id)
        if file_info:
            file_info.status = "failed"


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...)
):
    """
    Upload file to Azure Blob Storage and Index to RAG (SYNCHRONOUS)
    1. Uploads to Blob Storage (uploads container)
    2. Extracts text
    3. Indexes to Azure AI Search (Vector DB)
    
    Returns only after indexing is complete so file is immediately queryable.
    """
    # Validate file extension - OK, allowing all
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""

    
    # Generate file ID
    file_id = str(uuid.uuid4())
    
    # Read content
    content = await file.read()
    size = len(content)
    
    # Upload to Blob Storage
    blob_url = await _upload_to_blob(file.filename, content, file_id)

    # Create file info
    file_info = FileInfo(
        id=file_id,
        filename=file.filename,
        file_type=ext,
        size=size,
        uploaded_at=datetime.utcnow(),
        status="processing",  # Start as processing
        blob_url=blob_url
    )
    
    # Store file info
    shared_state.add_file(file_id, file_info)
    
    # SYNCHRONOUS PROCESSING - Wait for indexing to complete
    try:
        await _process_and_index_file(
            file_id,
            content,
            ext,
            file.filename,
            blob_url
        )
        
        # Get updated status
        current_info = shared_state.get_file(file_id)
        final_status = current_info.status
        chunks_indexed = current_info.chunks_indexed
        
        return UploadResponse(
            message=f"File uploaded and indexed successfully ({chunks_indexed} chunks)",
            file_id=file_id,
            filename=file.filename,
            status=final_status,
            blob_url=blob_url
        )
    except Exception as e:
        current_info = shared_state.get_file(file_id)
        if current_info:
            current_info.status = "failed"
        raise HTTPException(
            status_code=500,
            detail=f"Upload succeeded but indexing failed: {str(e)}"
        )


@router.get("/list", response_model=List[FileInfo])
async def list_files():
    """List all uploaded files"""
    return shared_state.list_files()


@router.get("/{file_id}", response_model=FileInfo)
async def get_file(file_id: str):
    """Get file information by ID"""
    file_info = shared_state.get_file(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    return file_info


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete a file and remove from RAG index"""
    if not shared_state.get_file(file_id):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Remove from RAG index
    try:
        from app.rag.indexer import RAGIndexer
        indexer = RAGIndexer()
        await indexer.delete_document(file_id)
    except Exception as e:
        print(f"Error removing from RAG: {e}")
    
    shared_state.remove_file(file_id)
    return {"message": "File deleted successfully", "file_id": file_id}


@router.get("/{file_id}/status")
async def get_file_status(file_id: str):
    """Get file processing status"""
    file_info = shared_state.get_file(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "file_id": file_id,
        "filename": file_info.filename,
        "status": file_info.status,
        "chunks_indexed": file_info.chunks_indexed,
        "blob_url": file_info.blob_url,
        "message": f"File is {file_info.status}"
    }

# Force reload
