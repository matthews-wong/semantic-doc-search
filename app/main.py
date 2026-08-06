"""FastAPI application exposing the semantic search index.

Routes:
    GET /            -> static search page
    GET /health      -> liveness/readiness probe
    GET /search      -> JSON search results for a query
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse

from app import __version__
from app.index import SearchIndex, extract_query_terms

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "data" / "docs"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="semantic-doc-search",
    version=__version__,
    description="Embeddings-based semantic search over a documentation corpus.",
)


@lru_cache(maxsize=1)
def get_index() -> SearchIndex:
    """Build (once) and return the shared search index.

    Cached so the corpus is embedded a single time per process.
    """
    return SearchIndex.from_dir(DOCS_DIR)


@app.on_event("startup")
def _warm_index() -> None:
    """Eagerly build the index at startup so the first query is fast."""
    get_index()


@app.get("/", include_in_schema=False)
def read_root() -> FileResponse:
    """Serve the static search page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> JSONResponse:
    """Report service health and the number of indexed documents."""
    index = get_index()
    return JSONResponse(
        {
            "status": "ok",
            "version": __version__,
            "documents": len(index.documents),
        }
    )


@app.get("/search")
def search(
    q: str = Query("", description="Free-text search query."),
    k: int = Query(5, ge=1, le=50, description="Number of results to return."),
    min_score: float = Query(
        0.0,
        ge=0.0,
        le=1.0,
        description=(
            "Drop results scoring below this cosine similarity (0.0-1.0). "
            "Defaults to 0.0, which keeps every top-k hit."
        ),
    ),
) -> JSONResponse:
    """Return up to ``k`` documents relevant to ``q``, above ``min_score``."""
    index = get_index()
    results = index.query(q, k=k, min_score=min_score)
    return JSONResponse(
        {
            "query": q,
            "terms": extract_query_terms(q),
            "count": len(results),
            "results": [
                {
                    "doc_id": r.doc_id,
                    "title": r.title,
                    "score": round(r.score, 4),
                    "snippet": r.snippet,
                }
                for r in results
            ],
        }
    )
