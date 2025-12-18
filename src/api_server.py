"""FastAPI server for SNI RAG system."""

import uuid
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from src.config import settings
from src.graph import create_sni_graph, aquery_sni, stream_sni_query
from src.tools import SNITools


# Global instances
sni_graph = None
sni_tools = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global sni_graph, sni_tools

    # Startup
    print("Initializing SNI RAG system...")
    sni_graph = create_sni_graph()
    sni_tools = SNITools()
    print("SNI RAG system initialized")

    yield

    # Shutdown
    print("Shutting down SNI RAG system...")


app = FastAPI(
    title="SNI Recognition API",
    description="SNI Recognition System with LangGraph RAG",
    version="1.0.0",
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
    """Query request model."""

    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """Query response model."""

    query: str
    answer: str
    session_id: str
    steps: int
    tool_calls: List[Dict[str, Any]]


class SearchRequest(BaseModel):
    """Search request model."""

    query: str
    top_k: int = 5


class DomainSearchRequest(BaseModel):
    """Domain search request model."""

    domain: str
    limit: int = 20


class BatchSearchRequest(BaseModel):
    """Batch search request model."""

    sni_list: List[str]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


class StatsResponse(BaseModel):
    """Statistics response."""

    total_records: Optional[int] = None
    vector_dimension: Optional[int] = None
    top_domains: Optional[List[Dict[str, Any]]] = None
    collection_status: Optional[str] = None
    error: Optional[str] = None


# Endpoints
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/api/query", response_model=QueryResponse)
async def query_sni_endpoint(request: QueryRequest):
    """Query SNI using LangGraph RAG.

    This endpoint uses the full LangGraph workflow to understand
    the query, select appropriate tools, and generate an answer.
    """
    global sni_graph

    if sni_graph is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    session_id = request.session_id or str(uuid.uuid4())

    try:
        result = await aquery_sni(
            query=request.query,
            app=sni_graph,
            session_id=session_id,
        )

        return QueryResponse(
            query=request.query,
            answer=result.get("answer", "No answer generated"),
            session_id=session_id,
            steps=result.get("steps", 0),
            tool_calls=result.get("tool_calls", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query/stream")
async def query_sni_stream(request: QueryRequest):
    """Stream query execution events.

    Returns Server-Sent Events (SSE) with execution progress.
    """
    global sni_graph

    if sni_graph is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    session_id = request.session_id or str(uuid.uuid4())

    async def generate():
        try:
            async for event in stream_sni_query(
                query=request.query,
                app=sni_graph,
                session_id=session_id,
            ):
                data = json.dumps(event, ensure_ascii=False)
                yield f"data: {data}\n\n"

            # Send completion event
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


@app.post("/api/search/exact")
async def search_exact(sni: str):
    """Direct exact search for SNI."""
    global sni_tools

    if sni_tools is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    result = sni_tools.search_sni_exact(sni)

    if not result.get("found"):
        raise HTTPException(status_code=404, detail=f"SNI '{sni}' not found")

    return result


@app.post("/api/search/vector")
async def search_vector(request: SearchRequest):
    """Direct vector similarity search."""
    global sni_tools

    if sni_tools is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    results = sni_tools.search_sni_vector(
        query=request.query,
        top_k=request.top_k,
    )

    return {"query": request.query, "results": results}


@app.post("/api/search/domain")
async def search_by_domain(request: DomainSearchRequest):
    """Search all SNIs under a domain."""
    global sni_tools

    if sni_tools is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    results = sni_tools.search_by_domain(
        domain=request.domain,
        limit=request.limit,
    )

    return {"domain": request.domain, "results": results}


@app.post("/api/search/batch")
async def batch_search(request: BatchSearchRequest):
    """Batch search multiple SNIs."""
    global sni_tools

    if sni_tools is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    results = sni_tools.batch_search_sni(request.sni_list)

    return {"results": results}


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get collection statistics."""
    global sni_tools

    if sni_tools is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    stats = sni_tools.get_stats()

    return StatsResponse(**stats)


@app.get("/api/graph/mermaid")
async def get_graph_mermaid():
    """Get graph visualization in Mermaid format."""
    global sni_graph

    if sni_graph is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        mermaid_code = sni_graph.get_graph().draw_mermaid()
        return {"mermaid": mermaid_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_server():
    """Run the FastAPI server."""
    import uvicorn

    uvicorn.run(
        "src.api_server:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )


if __name__ == "__main__":
    run_server()
