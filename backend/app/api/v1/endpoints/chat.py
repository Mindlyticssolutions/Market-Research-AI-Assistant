"""
Chat Endpoints
Handles conversation with agents via REST and WebSocket
AI Assistant uses RAG/KAG for context retrieval
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from datetime import datetime
import uuid
import sys
import os

# Add project root to path to allow importing 'agents'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str  # user, assistant, system
    content: str
    agent: Optional[str] = None
    timestamp: Optional[datetime] = None
    sources: Optional[List[str]] = None
    plot: Optional[str] = None # Base64 encoded image


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    agent: str = "orchestrator"  # Default to orchestrator for routing
    session_id: Optional[str] = None
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    session_id: str
    agent: str
    response: str
    timestamp: datetime
    sources: Optional[List[str]] = None  # RAG sources used
    plot: Optional[str] = None # Base64 encoded image


# In-memory session storage (replace with database for production)
chat_sessions: dict[str, List[ChatMessage]] = {}


async def _execute_agent(
    agent_name: str, 
    query: str, 
    context: dict = None, 
    history: List[ChatMessage] = None,
    callback = None
) -> tuple[str, List[str]]:
    """
    Execute query with specified agent using RAG/KAG context
    
    Args:
        agent_name: Name of the agent to use
        query: User's query
        context: Additional context
        history: Conversation history for multi-turn context
        callback: Optional async callback for streaming events
    """
    try:
        # Import agent registry
        from agents.registry import AgentRegistry
        
        # Get the agent
        agent = AgentRegistry.get_agent(agent_name)
        
        if agent is None:
            # Fallback to orchestrator
            agent = AgentRegistry.get_agent("orchestrator")
        
        if agent is None:
            return f"Agent '{agent_name}' not available", []
        
        # Build context with conversation history
        full_context = context or {}
        
        if history and len(history) > 0:
            # Format last 10 messages as conversation context
            recent_history = history[-10:]
            history_text = "\n".join([
                f"{'User' if msg.role == 'user' else 'Assistant'}: {msg.content}"
                for msg in recent_history
            ])
            full_context["conversation_history"] = history_text
        
        # Execute with RAG/KAG context (handled internally by BaseAgent)
        result = await agent.execute(query, full_context, callback=callback)
        
        print(f"DEBUG: Agent {agent_name} execution complete. Success: {result.success}", flush=True)
        if result.success:
            content_preview = result.content[:100] if result.content else "None"
            print(f"DEBUG: Returning content (len {len(result.content or '')}): {content_preview}...", flush=True)
            return result.content, result.sources or [], result.plot
        else:
            print(f"DEBUG: Returning error: {result.error}", flush=True)
            return f"Agent error: {result.error}", [], None
            
    except Exception as e:
        print(f"Agent execution error: {e}")
        return f"I encountered an error processing your request: {str(e)}", [], None


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to an agent and get a response
    Uses RAG/KAG for context retrieval (Notebook does NOT use this)
    """
    # Get or create session
    session_id = request.session_id or str(uuid.uuid4())
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    
    # Add user message to history
    user_msg = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.utcnow()
    )
    chat_sessions[session_id].append(user_msg)
    
    # Execute agent with RAG/KAG context and conversation history
    response_content, sources, plot = await _execute_agent(
        agent_name=request.agent,
        query=request.message,
        context=request.context,
        history=chat_sessions[session_id][:-1]  # Exclude current message
    )
    
    # Add assistant response to history
    assistant_msg = ChatMessage(
        role="assistant",
        content=response_content,
        agent=request.agent,
        timestamp=datetime.utcnow(),
        sources=sources,
        plot=plot
    )
    chat_sessions[session_id].append(assistant_msg)
    
    return ChatResponse(
        session_id=session_id,
        agent=request.agent,
        response=response_content,
        timestamp=datetime.utcnow(),
        sources=sources,
        plot=plot
    )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "messages": chat_sessions[session_id],
        "message_count": len(chat_sessions[session_id])
    }


@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history for a session"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del chat_sessions[session_id]
    return {"message": "Chat history cleared", "session_id": session_id}


@router.get("/sessions")
async def list_sessions():
    """List all active chat sessions"""
    return {
        "sessions": [
            {
                "session_id": sid,
                "message_count": len(messages),
                "last_message": messages[-1].timestamp if messages else None
            }
            for sid, messages in chat_sessions.items()
        ]
    }


# WebSocket for real-time chat with streaming
@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat
    Supports streaming responses from agents with RAG/KAG context
    """
    await websocket.accept()
    
    # Initialize session if needed
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            agent = data.get("agent", "orchestrator")
            
            if not message:
                await websocket.send_json({
                    "type": "error",
                    "message": "No message provided"
                })
                continue
            
            # Add user message
            user_msg = ChatMessage(
                role="user",
                content=message,
                timestamp=datetime.utcnow()
            )
            chat_sessions[session_id].append(user_msg)
            
            # Notify client that processing started
            await websocket.send_json({
                "type": "status",
                "status": "processing",
                "agent": agent
            })
            
            # Define callback for streaming intermediate events
            async def agent_callback(event_type: str, content: str):
                await websocket.send_json({
                    "type": event_type, # thinking, code_execution, observation
                    "content": content,
                    "agent": agent,
                    "timestamp": datetime.utcnow().isoformat()
                })

            # Execute agent with RAG/KAG and history
            response_content, sources, plot = await _execute_agent(
                agent_name=agent,
                query=message,
                history=chat_sessions[session_id][:-1],  # Exclude current message
                callback=agent_callback
            )
            
            # Add to history
            assistant_msg = ChatMessage(
                role="assistant",
                content=response_content,
                agent=agent,
                timestamp=datetime.utcnow(),
                sources=sources,
                plot=plot
            )
            chat_sessions[session_id].append(assistant_msg)
            
            # Send response
            await websocket.send_json({
                "type": "response",
                "agent": agent,
                "content": response_content,
                "sources": sources,
                "plot": plot,
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except WebSocketDisconnect:
        pass  # Client disconnected
