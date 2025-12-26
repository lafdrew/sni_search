"""FastAPI server for SNI RAG system."""

import uuid
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src.agent import SNIAgent
from src.tools import SNITools


# Global instances
sni_agent = None
sni_tools = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global sni_agent, sni_tools

    # Startup
    print("Initializing SNI RAG system...")
    sni_agent = SNIAgent(locale="en-US")
    sni_tools = SNITools()
    print("SNI RAG system initialized with LangGraph workflow")

    yield

    # Shutdown
    print("Shutting down SNI RAG system...")


app = FastAPI(
    title="SNI Recognition API",
    description="SNI Recognition System with LangGraph",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class QueryRequest(BaseModel):
    """SNI query request."""
    query: str
    session_id: Optional[str] = None
    verbose: bool = False


class QueryResponse(BaseModel):
    """SNI query response."""
    query: str
    answer: str
    metadata: dict
    session_id: Optional[str] = None


class ToolQueryRequest(BaseModel):
    """Direct tool query request."""
    sni: str
    tool: str = "exact"  # exact, vector, or domain


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "SNI Recognition API",
        "version": "2.0.0",
        "mode": "LangGraph Workflow",
        "endpoints": {
            "query": "/query",
            "tools": "/tools/{tool_name}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent": "initialized" if sni_agent else "not_initialized",
        "tools": "initialized" if sni_tools else "not_initialized",
    }


@app.post("/query", response_model=QueryResponse)
async def query_sni(request: QueryRequest):
    """Execute SNI query using LangGraph workflow.

    Args:
        request: Query request with query string

    Returns:
        Query response with answer and metadata
    """
    if not sni_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Execute query
        result = await sni_agent.aquery(
            query=request.query,
            verbose=request.verbose
        )

        return QueryResponse(
            query=request.query,
            answer=result["answer"],
            metadata=result.get("metadata", {}),
            session_id=session_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/exact")
async def exact_search(request: ToolQueryRequest):
    """Direct exact SNI search.

    Args:
        request: Tool query request

    Returns:
        Search results
    """
    if not sni_tools:
        raise HTTPException(status_code=503, detail="Tools not initialized")

    try:
        result = sni_tools.search_sni_exact(request.sni)
        return {"sni": request.sni, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/vector")
async def vector_search(request: ToolQueryRequest):
    """Direct vector similarity search.

    Args:
        request: Tool query request

    Returns:
        Search results
    """
    if not sni_tools:
        raise HTTPException(status_code=503, detail="Tools not initialized")

    try:
        result = sni_tools.search_sni_vector(request.sni, limit=5)
        return {"query": request.sni, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/domain")
async def domain_search(request: ToolQueryRequest):
    """Direct domain search.

    Args:
        request: Tool query request

    Returns:
        Search results
    """
    if not sni_tools:
        raise HTTPException(status_code=503, detail="Tools not initialized")

    try:
        result = sni_tools.search_by_domain(request.sni, limit=20)
        return {"domain": request.sni, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
    )
