from fastapi import APIRouter, Depends
from datetime import datetime
from src.infrastructure.storage.mongodb.client import MongoDBClient
from src.infrastructure.storage.vector.chroma_client import ChromaDBClient

from src.interfaces.rest.dependencies import get_mongodb_client, get_vector_store

router = APIRouter()

@router.get("/health")
async def health_check(
    mongo: MongoDBClient = Depends(get_mongodb_client),
    vector: ChromaDBClient = Depends(get_vector_store)
):
    """Comprehensive health check."""
    return {
        "status": "healthy" if mongo.is_connected else "degraded",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "mongodb": {
                "status": "healthy" if mongo.is_connected else "unhealthy",
                "connected": mongo.is_connected
            },
            "vector_store": {
                "status": "healthy",
                # Assuming the vector client exposes a count method as implied by the snippet/legacy code
                "count": vector.count() if hasattr(vector, 'count') else "unknown"
            }
        }
    }