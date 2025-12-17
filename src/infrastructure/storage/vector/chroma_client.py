import chromadb
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from src.infrastructure.storage.vector.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

class ChromaDBClient:
    """
    ChromaDB vector store client.
    Handles persistence, indexing, and vector search operations.
    """
    
    def __init__(
        self, 
        collection_name: str, 
        persist_directory: str, 
        embedding_service: EmbeddingService
    ):
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.embedding_service = embedding_service
        
        # Ensure directory exists
        self.persist_directory.mkdir(exist_ok=True, parents=True)
        
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"✓ ChromaDB initialized at {self.persist_directory}")

    def index_article(self, article_id: str, embedding: List[float]) -> None:
        """
        Index article embedding.
        Note: We store empty string for document text as content lives in MongoDB.
        """
        self.collection.add(
            ids=[article_id],
            embeddings=[embedding],
            documents=[""], 
            metadatas=[{"article_id": article_id}]
        )

    def search(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """
        Perform unrestricted vector search using a pre-computed embedding.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "distances"]
        )
        return self._format_results(results)

    def search_by_ids(
        self,
        query_embedding: List[float],
        article_ids: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Search within a specific subset of article IDs.
        Critical for 'Metadata Filter -> Vector Search' strategy.
        """
        if not article_ids:
            return []
        
        # ChromaDB 'where' clause to filter by article_ids
        where_filter = {
            "article_id": {"$in": article_ids}
        }
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, len(article_ids)),
            where=where_filter,
            include=["metadatas", "distances"]
        )
        
        return self._format_results(results)

    def delete_article(self, article_id: str) -> None:
        """Delete article from vector store."""
        try:
            self.collection.delete(ids=[article_id])
        except Exception as e:
            logger.error(f"Error deleting article {article_id} from ChromaDB: {e}")

    def reset(self) -> None:
        """Wipe the current collection and recreate it."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"✓ VectorStore collection '{self.collection_name}' reset")
        except Exception as e:
            logger.error(f"Error resetting ChromaDB collection: {e}")

    def count(self) -> int:
        """Get total number of articles in vector store."""
        return self.collection.count()

    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Helper to format ChromaDB results to clean dictionary structure."""
        formatted_results = []
        if not results or not results["ids"]:
            return formatted_results
            
        # ChromaDB returns list of lists (batch format), we take the first query result
        ids = results["ids"][0]
        distances = results["distances"][0]
        
        for i in range(len(ids)):
            formatted_results.append({
                "article_id": ids[i],
                "similarity": 1 - distances[i],  # Convert cosine distance to similarity
                "distance": distances[i]
            })
            
        return formatted_results