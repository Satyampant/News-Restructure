# MongoDB connection
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

class MongoDBClient:
    """MongoDB connection manager."""
    
    def __init__(self, connection_string: str, database_name: str, max_pool_size: int = 100, timeout_ms: int = 5000):
        self.connection_string = connection_string
        self.database_name = database_name
        self.max_pool_size = max_pool_size
        self.timeout_ms = timeout_ms
        self.client: Optional[MongoClient] = None
        self.db = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """Establish MongoDB connection with retry logic."""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                self.client = MongoClient(
                    self.connection_string,
                    maxPoolSize=self.max_pool_size,
                    serverSelectionTimeoutMS=self.timeout_ms,
                    connectTimeoutMS=self.timeout_ms,
                    socketTimeoutMS=self.timeout_ms * 2
                )
                
                self.client.admin.command('ping')
                
                self.db = self.client[self.database_name]
                self.is_connected = True
                
                logger.info(f"✓ MongoDB connected: {self.database_name}")
                return True
                
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.warning(f"MongoDB connection attempt {attempt}/{max_retries} failed: {str(e)}")
                self.is_connected = False
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Unexpected error during MongoDB connection: {str(e)}")
                self.is_connected = False
                return False
        
        logger.error("Could not establish connection to MongoDB after maximum retries.")
        return False
    
    def health_check(self) -> bool:
        """Validate MongoDB connection health."""
        if not self.is_connected or not self.client:
            return False
        
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {str(e)}")
            self.is_connected = False
            return False
    
    def close(self) -> None:
        """Close MongoDB connection and cleanup resources."""
        if self.client:
            try:
                self.client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {str(e)}")
            finally:
                self.client = None
                self.db = None
                self.is_connected = False
    
    def get_collection(self, collection_name: str):
        """Get a collection object."""
        if not self.is_connected or self.db is None:
             raise ConnectionError("Not connected to MongoDB")
        return self.db[collection_name]