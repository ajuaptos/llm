"""
FastAPI Main Server for Local-AI-RAG Application
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json

from backend.config import get_settings
from backend.llm_client import get_ollama_client
from backend.firewall import get_firewall
from backend.scout import get_scout
from backend.rag_pipeline import get_rag_pipeline
from backend.database import get_database
from backend.search_client import get_search_client


# Initialize FastAPI app
app = FastAPI(
    title="Local-AI-RAG",
    description="Local LLM with AI Firewall, Scout, and RAG capabilities",
    version="1.0.0"
)

# Load settings
settings = get_settings()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],  # Allow all in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
llm_client = get_ollama_client()
firewall = get_firewall()
scout = get_scout()
rag_pipeline = get_rag_pipeline()
db = get_database()
search_client = get_search_client()


# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_rag: bool = False
    use_scout: bool = True  # Enable Scout by default
    stream: bool = False
    temperature: float = 0.7


class ChatResponse(BaseModel):
    response: str
    session_id: str
    firewall_passed: bool
    scout_triggered: bool
    rag_used: bool
    search_results: Optional[List[Dict]] = None
    retrieved_docs: Optional[List[Dict]] = None


class DocumentIngestRequest(BaseModel):
    content: str
    title: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    metadata: Optional[Dict] = None


class RAGQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class FirewallCheckRequest(BaseModel):
    content: str


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    ollama_status = await llm_client.check_health()
    
    return {
        "status": "healthy" if ollama_status else "degraded",
        "ollama": "connected" if ollama_status else "disconnected",
        "database": "connected",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "rag": "/api/rag/*",
            "firewall": "/api/firewall/*",
            "scout": "/api/scout/*",
            "stats": "/api/stats"
        }
    }


# Chat endpoints
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with AI firewall, scout, and RAG support
    """
    # Generate or use session ID
    session_id = request.session_id or str(uuid.uuid4())
    
    # Create session if new
    if not request.session_id:
        db.create_session(session_id)
    
    # Check firewall on input
    is_safe, block_reason = await firewall.check_content(request.message)
    
    if not is_safe:
        # Log blocked message
        db.add_message(
            session_id=session_id,
            role="user",
            content=request.message,
            firewall_passed=False
        )
        
        return ChatResponse(
            response=f"Message blocked by AI firewall: {block_reason}",
            session_id=session_id,
            firewall_passed=False,
            scout_triggered=False,
            rag_used=False
        )
    
    # Get chat history
    history = db.get_chat_history(session_id, limit=10)
    messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
    ]
    messages.append({"role": "user", "content": request.message})
    
    # Generate response
    if request.use_rag:
        # Use RAG pipeline
        rag_result = await rag_pipeline.query(
            query=request.message,
            chat_history=messages[:-1]  # Exclude current message
        )
        
        response_text = rag_result["response"]
        rag_used = rag_result["rag_used"]
        retrieved_docs = rag_result.get("retrieved_docs", [])
    else:
        # Standard LLM chat
        response_text = await llm_client.chat(
            messages=messages,
            temperature=request.temperature
        )
        rag_used = False
        retrieved_docs = None
    
    # Check firewall on output
    output_safe, _ = await firewall.filter_response(response_text)
    if not output_safe:
        response_text = "I apologize, but I cannot provide that response."
    
    # Scout analysis (check for uncertainty) - only if enabled by user
    scout_triggered = False
    search_results = []
    final_response = response_text
    
    if request.use_scout:
        scout_result = await scout.enhance_query(
            query=request.message,
            response=response_text,
            session_id=session_id
        )
        
        final_response = scout_result["response"]
        scout_triggered = scout_result["scout_triggered"]
        search_results = scout_result.get("search_results", [])
    
    # Log messages
    db.add_message(
        session_id=session_id,
        role="user",
        content=request.message,
        firewall_passed=True,
        scout_triggered=False,
        rag_used=rag_used
    )
    
    db.add_message(
        session_id=session_id,
        role="assistant",
        content=final_response,
        firewall_passed=output_safe,
        scout_triggered=scout_triggered,
        rag_used=rag_used
    )
    
    return ChatResponse(
        response=final_response,
        session_id=session_id,
        firewall_passed=True,
        scout_triggered=scout_triggered,
        rag_used=rag_used,
        search_results=search_results if scout_triggered else None,
        retrieved_docs=retrieved_docs if rag_used else None
    )


@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 50):
    """Get chat history for a session"""
    history = db.get_chat_history(session_id, limit=limit)
    return {"session_id": session_id, "messages": history}


# RAG endpoints
@app.post("/api/rag/ingest")
async def ingest_document(request: DocumentIngestRequest):
    """Ingest a document into the RAG system"""
    result = await rag_pipeline.ingest_document(
        content=request.content,
        title=request.title,
        source=request.source,
        url=request.url,
        metadata=request.metadata
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@app.post("/api/rag/ingest/batch")
async def ingest_documents_batch(documents: List[DocumentIngestRequest]):
    """Ingest multiple documents"""
    docs = [doc.dict() for doc in documents]
    results = await rag_pipeline.ingest_documents_batch(docs)
    
    return {
        "total": len(results),
        "successful": sum(1 for r in results if r["success"]),
        "results": results
    }


@app.post("/api/rag/query")
async def rag_query(request: RAGQueryRequest):
    """Query the RAG system"""
    result = await rag_pipeline.query(
        query=request.query,
        top_k=request.top_k
    )
    return result


@app.get("/api/rag/documents")
async def list_documents(limit: Optional[int] = 100):
    """List all ingested documents"""
    documents = rag_pipeline.list_documents(limit=limit)
    return {"documents": documents, "count": len(documents)}


@app.delete("/api/rag/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document"""
    success = rag_pipeline.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True, "doc_id": doc_id}


# Firewall endpoints
@app.post("/api/firewall/check")
async def check_firewall(request: FirewallCheckRequest):
    """Check content against firewall"""
    is_safe, reason = await firewall.check_content(request.content)
    return {
        "is_safe": is_safe,
        "reason": reason,
        "content_length": len(request.content)
    }


@app.get("/api/firewall/stats")
async def firewall_stats():
    """Get firewall statistics"""
    return firewall.get_stats()


# Scout endpoints
@app.get("/api/scout/stats")
async def scout_stats():
    """Get scout statistics"""
    return scout.get_stats()


@app.post("/api/scout/search")
async def scout_search(query: str):
    """Perform web search"""
    results = await search_client.search_and_summarize(query)
    return results


# System endpoints
@app.get("/api/stats")
async def system_stats():
    """Get overall system statistics"""
    db_stats = db.get_stats()
    rag_stats = rag_pipeline.get_stats()
    firewall_stats = firewall.get_stats()
    scout_stats = scout.get_stats()
    
    return {
        "database": db_stats,
        "rag": rag_stats,
        "firewall": firewall_stats,
        "scout": scout_stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/models")
async def list_models():
    """List available Ollama models"""
    try:
        models = await llm_client.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve frontend static files
import os
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    print(f"Warning: Frontend directory not found at {frontend_dir}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
