"""
Health Check Endpoints
"""
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }


@router.get("/azure")
async def azure_health():
    """Check Azure services connectivity"""
    status = {
        "openai": "unconfigured",
        "search": "unconfigured",
        "storage": "unconfigured",
        "document_intelligence": "unconfigured"
    }
    
    # Check Azure OpenAI
    if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY:
        status["openai"] = "configured"
    
    # Check Azure Search
    if settings.AZURE_SEARCH_ENDPOINT and settings.AZURE_SEARCH_KEY:
        status["search"] = "configured"
    
    # Check Azure Storage
    if settings.AZURE_STORAGE_CONNECTION_STRING:
        status["storage"] = "configured"
    
    # Check Document Intelligence
    if settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT:
        status["document_intelligence"] = "configured"
    
    return status
