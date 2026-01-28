"""Semantic search tools for cruise booking agent."""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.tools.semantic_search import SemanticSearch
from src.tools.vector_store import VectorStore
from ..config import tracer

# Initialize search components
_vector_store = VectorStore()
_semantic_search = SemanticSearch(vector_store=_vector_store)


@tracer.tool
def semantic_search_cruises(
    query: str,
    n_results: int = 5,
    filters: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """
    Perform semantic search for cruises based on natural language query.

    Args:
        query: Natural language search query (e.g., "romantic cruise with spa")
        n_results: Number of top results to return (default: 5)
        filters: Optional dictionary of filters to apply (e.g., {'destination': 'Caribbean'})

    Returns:
        List of matching cruise dictionaries with relevance scores.
    """
    # Pass None when there are no filters so the underlying vector
    # store does not receive an empty where clause (which Chroma
    # rejects with `Expected where to have exactly one operator`).
    normalized_filters = filters if filters else None
    return _semantic_search.search(query, n_results=n_results, filters=normalized_filters)


@tracer.tool
def find_similar_cruises(
    cruise_id: str,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Find cruises similar to a given cruise.
    
    Args:
        cruise_id: ID of the reference cruise
        top_k: Number of similar cruises to return
    
    Returns:
        List of similar cruise dictionaries.
    """
    return _semantic_search.find_similar(cruise_id, top_k=top_k)
