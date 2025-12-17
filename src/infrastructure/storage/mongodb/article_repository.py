from typing import Optional, List, Dict, Any
from pymongo import ASCENDING, DESCENDING
import logging
from datetime import datetime

from src.infrastructure.storage.mongodb.client import MongoDBClient
from src.domain.models.article import NewsArticle

logger = logging.getLogger(__name__)

class ArticleRepository:
    """Repository for NewsArticle persistence."""
    
    def __init__(self, client: MongoDBClient, collection_name: str):
        self.client = client
        self.collection = client.get_collection(collection_name)
        self._create_indexes()
    
    def _create_indexes(self) -> None:
        """Create indexes on frequently queried fields for optimal performance."""
        try:
            self.collection.create_index([("id", ASCENDING)], unique=True, name="idx_id")
            self.collection.create_index([("timestamp", DESCENDING)], name="idx_timestamp")
            self.collection.create_index([("entities.Sectors", ASCENDING)], name="idx_sectors")
            self.collection.create_index([("sentiment.classification", ASCENDING)], name="idx_sentiment")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")

    def insert_article(self, article: NewsArticle) -> str:
        """Insert or update article in MongoDB using upsert."""
        mongo_doc = self._to_document(article)
        self.collection.replace_one(
            {"id": article.id},
            mongo_doc,
            upsert=True
        )
        return article.id
    
    def get_article_by_id(self, article_id: str) -> Optional[NewsArticle]:
        """Retrieve a single article by its business ID."""
        doc = self.collection.find_one({"id": article_id})
        if doc is None:
            return None
        return self._from_document(doc)

    def get_articles_by_ids(self, article_ids: List[str]) -> List[NewsArticle]:
        """Retrieve multiple articles by IDs, preserving order."""
        if not article_ids:
            return []
        cursor = self.collection.find({"id": {"$in": article_ids}})
        article_dict = {doc["id"]: self._from_document(doc) for doc in cursor}
        return [article_dict[aid] for aid in article_ids if aid in article_dict]

    def _to_document(self, article: NewsArticle) -> dict:
        """Convert domain model to MongoDB document."""
        doc = {
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "source": article.source,
            "timestamp": article.timestamp.isoformat() if article.timestamp else None,
            "raw_text": getattr(article, "raw_text", article.content)
        }
        
        # Flatten and serialize optional fields if they exist
        if hasattr(article, 'entities_rich') and article.entities_rich:
             doc["entities_rich"] = article.entities_rich
        
        # Legacy entities support
        if hasattr(article, 'entities') and article.entities:
             doc["entities"] = article.entities
             
        if hasattr(article, 'sentiment') and article.sentiment:
             doc["sentiment"] = article.sentiment

        if hasattr(article, 'impacted_stocks') and article.impacted_stocks:
             doc["impacted_stocks"] = [
                 stock if isinstance(stock, dict) else stock.to_dict() 
                 for stock in article.impacted_stocks
             ]
             
        if hasattr(article, 'cross_impacts') and article.cross_impacts:
             doc["cross_impacts"] = article.cross_impacts

        return doc
    
    def _from_document(self, doc: dict) -> NewsArticle:
        """Convert MongoDB document to domain model."""
        timestamp = doc.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
            
        article = NewsArticle(
            id=doc["id"],
            title=doc["title"],
            content=doc["content"],
            source=doc["source"],
            timestamp=timestamp
        )
        
        if "raw_text" in doc:
            article.raw_text = doc["raw_text"]
            
        if "entities_rich" in doc:
            article.entities_rich = doc["entities_rich"]
        
        if "entities" in doc:
            article.entities = doc["entities"]
            
        if "sentiment" in doc:
            article.sentiment = doc["sentiment"]
            
        if "impacted_stocks" in doc:
            article.impacted_stocks = doc["impacted_stocks"]
            
        if "cross_impacts" in doc:
            article.cross_impacts = doc["cross_impacts"]
            
        return article