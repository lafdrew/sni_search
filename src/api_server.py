"""FastAPI server for SNI RAG system."""

import uuid
import json
import logging
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

# Configure logging to see all details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Override any existing configuration
)

logger = logging.getLogger(__name__)

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


@app.get("/query/stream")
async def query_sni_stream(
    request: Request,
    query: str = Query(..., description="Search query"),
    session_id: Optional[str] = Query(None, description="Session ID"),
    verbose: bool = Query(True, description="Enable verbose logging")
):
    """SSE streaming endpoint for real-time search progress.

    Args:
        request: FastAPI request object
        query: Search query string
        session_id: Optional session ID for tracking
        verbose: Enable verbose logging

    Returns:
        EventSourceResponse with streaming search progress
    """
    if not sni_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    async def event_generator():
        try:
            # Use the session_id from outer scope or generate a new one
            current_session_id = session_id or str(uuid.uuid4())

            # Send start event
            yield {
                "event": "search_started",
                "data": json.dumps({
                    "query": query,
                    "session_id": current_session_id,
                    "timestamp": datetime.now().isoformat()
                })
            }

            # Stream query execution
            async for event in sni_agent.aquery_stream(query=query, verbose=verbose):
                yield {
                    "event": event["type"],
                    "data": json.dumps(event["data"])
                }

        except GeneratorExit:
            logger.info("Client disconnected from SSE stream")
        except Exception as e:
            logger.error(f"SSE stream error: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            }

    return EventSourceResponse(event_generator())


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
