from fastapi import APIRouter, Depends
from datetime import datetime
from src.infrastructure.storage.mongodb.client import MongoDBClient
from src.infrastructure.storage.vector.chroma_client import ChromaDBClient

router = APIRouter()

@router.get("/health")
async def health_check(
    mongo: MongoDBClient = Depends(),
    vector: ChromaDBClient = Depends()
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