"""Semantic search using embeddings and vector store."""

from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

from .vector_store import VectorStore
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SemanticSearch:
    """Semantic search for cruise data using BGE-small-en-v1.5 embeddings."""
    
    def __init__(self, vector_store: Optional[VectorStore] = None, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.vector_store = vector_store or VectorStore()
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a text."""
        if not self.model:
            raise ValueError("Model not loaded")
        
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search."""
        try:
            # Generate query embedding (currently unused by Chroma text search
            # but kept for future similarity search extensions)
            query_embedding = self.embed_text(query)
            
            # Chroma expects either a valid `where` object or None, not an empty dict.
            where_clause = filters if filters else None

            # Search vector store
            results = self.vector_store.search(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
            
            # Format results
            formatted_results = []
            if results.get("ids") and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0.0
                    })
            
            logger.info(f"Semantic search returned {len(formatted_results)} results")
            return formatted_results
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def search_by_preference(
        self,
        preferences: List[str],
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search by preferences (e.g., 'romantic', 'spa', 'family-friendly')."""
        query = " ".join(preferences)
        return self.search(query, n_results=n_results)
