"""Vector store wrapper for ChromaDB."""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Wrapper for ChromaDB vector store."""
    
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "cruises"):
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._initialize()
    
    def _initialize(self):
        """Initialize ChromaDB client and collection."""
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Cruise data for semantic search"}
            )
            
            logger.info(f"Initialized ChromaDB collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
    
    def add_documents(
        self,
        documents: List[str],
        ids: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """Add documents to the vector store."""
        try:
            self.collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            logger.info(f"Added {len(documents)} documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def search(
        self,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search the vector store."""
        try:
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where
            )
            return results
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}
    
    def get_collection_size(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count() if self.collection else 0
