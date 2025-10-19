from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
import os
from pathlib import Path

from app.services.search_engine import SearchEngine

# =========================
# CONFIGURATION
# =========================

API_TITLE = "Visual Semantic Search API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
CLIP-powered semantic image search system

Search through 24,943+ images using natural language queries.

### Features:
* Fast similarity search with FAISS indexing
* CLIP ViT-B/32 model for semantic understanding
* Query enhancement for better results
* Adjustable top-K and threshold parameters
"""

DEVICE = os.getenv("DEVICE", "cuda")
DEFAULT_TOP_K = 5
DEFAULT_THRESHOLD = 0.2
MAX_TOP_K = 20

# =========================
# PYDANTIC MODELS
# =========================

class SearchRequest(BaseModel):
    """Search request schema with validation."""
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=MAX_TOP_K)
    threshold: float = Field(default=DEFAULT_THRESHOLD, ge=0.0, le=1.0)
    use_enhancement: bool = Field(default=True)

class SearchResultItem(BaseModel):
    """Individual search result."""
    rank: int
    filename: str
    image_path: str
    similarity_score: float
    confidence_percentage: str
    num_query_matches: int

class SearchResponse(BaseModel):
    """Complete search response."""
    query: str
    results: List[SearchResultItem]
    timing_ms: float
    enhanced_queries: List[str]
    results_count: int
    meta: Dict[str, Any]

class HealthResponse(BaseModel):
    """System health and status."""
    status: str
    device: str
    model: str
    vectors_indexed: int
    embedding_dim: int
    total_images: int
    index_type: str

# =========================
# FASTAPI APP INITIALIZATION
# =========================

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["http://localhost:3000", "https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for images
# Use relative path that works in any environment
BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "data" / "images"

if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")
    print(f"Mounted images directory: {IMAGES_DIR}")
else:
    print(f"Warning: Images directory not found at {IMAGES_DIR}")

# Global search engine instance
search_engine: Optional[SearchEngine] = None

# =========================
# LIFECYCLE EVENTS
# =========================

@app.on_event("startup")
async def startup_event():
    """Initialize search engine on startup."""
    global search_engine
    
    print("\n" + "=" * 70)
    print(f"Starting {API_TITLE} v{API_VERSION}")
    print("=" * 70)
    
    try:
        start_time = time.time()
        search_engine = SearchEngine.load_from_disk(device=DEVICE)
        load_time = time.time() - start_time
        
        status = search_engine.get_status()
        print(f"\n Search engine loaded successfully in {load_time:.2f}s")
        print(f"   Vectors indexed: {status['vectors_indexed']:,}")
        print(f"   Total images: {status['total_images']:,}")
        print(f"   Device: {status['device']}")
        print(f"   Model: {status['model']}")
        print("=" * 70 + "\n")
    
    except Exception as e:
        print(f"\nFailed to load search engine: {e}\n")
        raise RuntimeError(f"Startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("\nShutting down Visual Semantic Search API\n")

# =========================
# API ENDPOINTS
# =========================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Visual Semantic Search API",
        "version": API_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["System"], response_model=HealthResponse)
async def health_check():
    """Check system health and get configuration details."""
    if search_engine is None:
        raise HTTPException(
            status_code=503,
            detail="Search engine not initialized"
        )
    
    try:
        status = search_engine.get_status()
        return HealthResponse(
            status="healthy",
            device=status.get("device", "unknown"),
            model=status.get("model", "unknown"),
            vectors_indexed=status.get("vectors_indexed", 0),
            embedding_dim=status.get("embedding_dim", 0),
            total_images=status.get("total_images", 0),
            index_type=status.get("index_type", "unknown")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/search", tags=["Search"], response_model=SearchResponse)
async def search_images(request: SearchRequest):
    """Semantic image search using natural language queries."""
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    
    try:
        print(f"Search: '{request.query}' (k={request.top_k}, t={request.threshold})")
        
        # Execute search
        results, timing_ms = search_engine.search(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            use_enhancement=request.use_enhancement
        )
        
        # Transform image_path for React compatibility
        # Change absolute paths to relative /images/ URLs
        for result in results:
            # Extract just the filename
            filename = Path(result['image_path']).name
            # Set to URL path that React can fetch
            result['image_path'] = f"/images/{filename}"
        
        # Get enhanced queries
        enhanced_queries = search_engine.enhance_query(
            request.query, 
            request.use_enhancement
        )
        
        # Get system metadata
        status = search_engine.get_status()
        meta = {
            "device": status.get("device"),
            "model": status.get("model"),
            "index_type": status.get("index_type"),
            "total_images": status.get("total_images")
        }
        
        print(f"Found {len(results)} results in {timing_ms:.1f}ms")
        
        return SearchResponse(
            query=request.query,
            results=results,
            timing_ms=timing_ms,
            enhanced_queries=enhanced_queries,
            results_count=len(results),
            meta=meta
        )
    
    except Exception as e:
        print(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search operation failed: {str(e)}"
        )

@app.get("/search", tags=["Search"], response_model=SearchResponse)
async def search_images_get(
    query: str = Query(..., min_length=1, max_length=500),
    top_k: int = Query(default=DEFAULT_TOP_K, ge=1, le=MAX_TOP_K),
    threshold: float = Query(default=DEFAULT_THRESHOLD, ge=0.0, le=1.0),
    use_enhancement: bool = Query(default=True)
):
    """GET version of search endpoint."""
    request = SearchRequest(
        query=query,
        top_k=top_k,
        threshold=threshold,
        use_enhancement=use_enhancement
    )
    return await search_images(request)

@app.post("/admin/reload", tags=["Admin"])
async def reload_index():
    """Reload the search index and models."""
    global search_engine
    
    try:
        print("\nReloading search engine...")
        start_time = time.time()
        
        search_engine = SearchEngine.load_from_disk(device=DEVICE)
        
        load_time = time.time() - start_time
        print(f"Reload complete in {load_time:.2f}s\n")
        
        return {
            "status": "success",
            "message": "Search engine reloaded successfully",
            "load_time_seconds": round(load_time, 2)
        }
    
    except Exception as e:
        print(f"Reload failed: {e}\n")
        raise HTTPException(status_code=500, detail=f"Reload failed: {str(e)}")

# =========================
# ERROR HANDLERS
# =========================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": f"Endpoint {request.url.path} not found",
            "timestamp": time.time()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "timestamp": time.time()
        }
    )

# =========================
# DEVELOPMENT SERVER
# =========================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
